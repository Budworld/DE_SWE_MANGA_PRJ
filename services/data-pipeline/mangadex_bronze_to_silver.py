from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE = "mangadex"
SILVER_SCHEMA_VERSION = "silver.v1"
ENTITY_TYPES = ("manga", "chapter", "cover", "author", "tag", "scanlation_group")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {error}") from error
    return records


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            file.write("\n")


def clear_output_run_dir(output_run_dir: Path) -> None:
    if not output_run_dir.exists():
        return

    for path in sorted(output_run_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()


def get_crawl_run_id(bronze_run_dir: Path) -> str:
    if bronze_run_dir.name.startswith("crawl_run_id="):
        return bronze_run_dir.name.split("=", 1)[1]

    summary_file = bronze_run_dir / "ingest_summary.json"
    if summary_file.exists():
        return read_json(summary_file)["crawl_run_id"]

    raise ValueError(f"Cannot infer crawl_run_id from {bronze_run_dir}")


def silver_id(entity_type: str, source_entity_id: str) -> str:
    return f"{SOURCE}:{entity_type}:{source_entity_id}"


def first_localized_value(value: Any, preferred_languages: tuple[str, ...] = ("en", "ja-ro", "ja")) -> tuple[str | None, str | None]:
    if not isinstance(value, dict) or not value:
        return None, None

    for language in preferred_languages:
        localized = value.get(language)
        if isinstance(localized, str) and localized.strip():
            return localized, language

    for language, localized in value.items():
        if isinstance(localized, str) and localized.strip():
            return localized, language

    return None, None


def relationship_target(record: dict[str, Any], relationship_type: str) -> str | None:
    relationships = record.get("relationships") or []
    for relationship in relationships:
        if relationship.get("type") == relationship_type:
            return relationship.get("id")
    return None


def base_fields(record: dict[str, Any], transformed_at: str) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "crawl_run_id": record["crawl_run_id"],
        "bronze_record_id": record["bronze_record_id"],
        "silver_schema_version": SILVER_SCHEMA_VERSION,
        "silver_transformed_at": transformed_at,
    }


def transform_manga(record: dict[str, Any], transformed_at: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    attributes = record.get("attributes") or {}
    source_manga_id = record["source_entity_id"]
    primary_title, primary_title_language = first_localized_value(attributes.get("title"))
    errors = []
    if not primary_title:
        errors.append(error_record(record, "missing_primary_title", "Manga primary title is empty"))

    output = {
        "manga_id": silver_id("manga", source_manga_id),
        "source_manga_id": source_manga_id,
        "primary_title": primary_title,
        "primary_title_language": primary_title_language,
        "alt_titles": attributes.get("altTitles") or [],
        "description": attributes.get("description") or {},
        "original_language": attributes.get("originalLanguage"),
        "available_translated_languages": attributes.get("availableTranslatedLanguages") or [],
        "publication_demographic": attributes.get("publicationDemographic"),
        "status": attributes.get("status"),
        "year": attributes.get("year"),
        "content_rating": attributes.get("contentRating"),
        "created_at": attributes.get("createdAt"),
        "updated_at": attributes.get("updatedAt"),
        "latest_uploaded_chapter": attributes.get("latestUploadedChapter"),
        **base_fields(record, transformed_at),
    }
    manga_tag_records = []
    for tag in attributes.get("tags") or []:
        if not isinstance(tag, dict) or not tag.get("id"):
            continue

        manga_tag_records.append({
            "source": SOURCE,
            "crawl_run_id": record["crawl_run_id"],
            "from_entity_type": "manga",
            "from_entity_id": source_manga_id,
            "relationship_type": "tag",
            "to_entity_type": "tag",
            "to_entity_id": tag["id"],
            "source_manga_id": source_manga_id,
            "source_tag_id": tag["id"],
            "bronze_record_id": record["bronze_record_id"],
            "silver_schema_version": SILVER_SCHEMA_VERSION,
            "silver_transformed_at": transformed_at,
        })

    manga_cover_records = []
    for relationship in record.get("relationships") or []:
        if relationship.get("type") != "cover_art" or not relationship.get("id"):
            continue

        relationship_attributes = relationship.get("attributes") or {}
        manga_cover_records.append({
            "source": SOURCE,
            "crawl_run_id": record["crawl_run_id"],
            "from_entity_type": "manga",
            "from_entity_id": source_manga_id,
            "relationship_type": "cover_art",
            "to_entity_type": "cover_art",
            "to_entity_id": relationship["id"],
            "source_manga_id": source_manga_id,
            "source_cover_id": relationship["id"],
            "cover_file_name": relationship_attributes.get("fileName"),
            "cover_volume": relationship_attributes.get("volume"),
            "cover_locale": relationship_attributes.get("locale"),
            "bronze_record_id": record["bronze_record_id"],
            "silver_schema_version": SILVER_SCHEMA_VERSION,
            "silver_transformed_at": transformed_at,
        })

    return output, errors, manga_tag_records, manga_cover_records


def transform_chapter(record: dict[str, Any], transformed_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    attributes = record.get("attributes") or {}
    source_chapter_id = record["source_entity_id"]
    source_manga_id = relationship_target(record, "manga")
    errors = []
    if not attributes.get("translatedLanguage"):
        errors.append(error_record(record, "missing_translated_language", "Chapter translated language is empty"))

    output = {
        "chapter_id": silver_id("chapter", source_chapter_id),
        "source_chapter_id": source_chapter_id,
        "source_manga_id": source_manga_id,
        "title": attributes.get("title"),
        "volume": attributes.get("volume"),
        "chapter_number": attributes.get("chapter"),
        "translated_language": attributes.get("translatedLanguage"),
        "external_url": attributes.get("externalUrl"),
        "pages": attributes.get("pages"),
        "version": attributes.get("version"),
        "publish_at": attributes.get("publishAt"),
        "readable_at": attributes.get("readableAt"),
        "created_at": attributes.get("createdAt"),
        "updated_at": attributes.get("updatedAt"),
        **base_fields(record, transformed_at),
    }
    return output, errors


def transform_cover(record: dict[str, Any], transformed_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    attributes = record.get("attributes") or {}
    source_cover_id = record["source_entity_id"]
    source_manga_id = relationship_target(record, "manga")
    errors = []
    if not attributes.get("fileName"):
        errors.append(error_record(record, "missing_file_name", "Cover file name is empty"))

    output = {
        "cover_id": silver_id("cover", source_cover_id),
        "source_cover_id": source_cover_id,
        "source_manga_id": source_manga_id,
        "volume": attributes.get("volume"),
        "file_name": attributes.get("fileName"),
        "description": attributes.get("description"),
        "locale": attributes.get("locale"),
        "created_at": attributes.get("createdAt"),
        "updated_at": attributes.get("updatedAt"),
        **base_fields(record, transformed_at),
    }
    return output, errors


def transform_author(record: dict[str, Any], transformed_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    attributes = record.get("attributes") or {}
    source_author_id = record["source_entity_id"]
    errors = []
    if not attributes.get("name"):
        errors.append(error_record(record, "missing_name", "Author name is empty"))

    output = {
        "author_id": silver_id("author", source_author_id),
        "source_author_id": source_author_id,
        "name": attributes.get("name"),
        "biography": attributes.get("biography") or {},
        "image_url": attributes.get("imageUrl"),
        "website": attributes.get("website"),
        "twitter": attributes.get("twitter"),
        "pixiv": attributes.get("pixiv"),
        "created_at": attributes.get("createdAt"),
        "updated_at": attributes.get("updatedAt"),
        **base_fields(record, transformed_at),
    }
    return output, errors


def transform_tag(record: dict[str, Any], transformed_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    attributes = record.get("attributes") or {}
    source_tag_id = record["source_entity_id"]
    errors = []
    if not attributes.get("name"):
        errors.append(error_record(record, "missing_name", "Tag name is empty"))

    output = {
        "tag_id": silver_id("tag", source_tag_id),
        "source_tag_id": source_tag_id,
        "name": attributes.get("name") or {},
        "description": attributes.get("description") or {},
        "group_name": attributes.get("group"),
        "version": attributes.get("version"),
        **base_fields(record, transformed_at),
    }
    return output, errors


def transform_scanlation_group(record: dict[str, Any], transformed_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    attributes = record.get("attributes") or {}
    source_group_id = record["source_entity_id"]
    errors = []
    if not attributes.get("name"):
        errors.append(error_record(record, "missing_name", "Scanlation group name is empty"))

    output = {
        "scanlation_group_id": silver_id("scanlation_group", source_group_id),
        "source_group_id": source_group_id,
        "name": attributes.get("name"),
        "alt_names": attributes.get("altNames") or [],
        "website": attributes.get("website"),
        "discord": attributes.get("discord"),
        "contact_email": attributes.get("contactEmail"),
        "description": attributes.get("description"),
        "created_at": attributes.get("createdAt"),
        "updated_at": attributes.get("updatedAt"),
        **base_fields(record, transformed_at),
    }
    return output, errors


def error_record(record: dict[str, Any], error_type: str, error_message: str) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "crawl_run_id": record.get("crawl_run_id"),
        "bronze_record_id": record.get("bronze_record_id"),
        "source_entity_type": record.get("source_entity_type"),
        "source_entity_id": record.get("source_entity_id"),
        "error_type": error_type,
        "error_message": error_message,
        "silver_schema_version": SILVER_SCHEMA_VERSION,
        "silver_transformed_at": utc_now(),
    }


TRANSFORMERS = {
    "manga": transform_manga,
    "chapter": transform_chapter,
    "cover": transform_cover,
    "author": transform_author,
    "tag": transform_tag,
    "scanlation_group": transform_scanlation_group,
}


BRIDGE_TABLES = {
    ("manga", "author"): "manga_author",
    ("manga", "artist"): "manga_artist",
    ("manga", "tag"): "manga_tag",
    ("chapter", "manga"): "chapter_manga",
    ("chapter", "scanlation_group"): "chapter_scanlation_group",
}


def bridge_record(relationship: dict[str, Any], transformed_at: str) -> dict[str, Any]:
    from_type = relationship["from_entity_type"]
    to_type = relationship["to_entity_type"]
    record = {
        "source": SOURCE,
        "crawl_run_id": relationship["crawl_run_id"],
        "from_entity_type": from_type,
        "from_entity_id": relationship["from_entity_id"],
        "relationship_type": relationship["relationship_type"],
        "to_entity_type": to_type,
        "to_entity_id": relationship["to_entity_id"],
        "bronze_relationship_id": relationship["bronze_relationship_id"],
        "silver_schema_version": SILVER_SCHEMA_VERSION,
        "silver_transformed_at": transformed_at,
    }

    if from_type == "manga":
        record["source_manga_id"] = relationship["from_entity_id"]
    if from_type == "chapter":
        record["source_chapter_id"] = relationship["from_entity_id"]
    if to_type in {"author", "artist"}:
        record["source_author_id"] = relationship["to_entity_id"]
    if to_type == "tag":
        record["source_tag_id"] = relationship["to_entity_id"]
    if to_type == "cover_art":
        record["source_cover_id"] = relationship["to_entity_id"]
    if to_type == "manga":
        record["source_manga_id"] = relationship["to_entity_id"]
    if to_type == "scanlation_group":
        record["source_group_id"] = relationship["to_entity_id"]

    return record


def run(bronze_run_dir: Path, output_root: Path, overwrite: bool) -> dict[str, Any]:
    crawl_run_id = get_crawl_run_id(bronze_run_dir)
    output_run_dir = output_root / SOURCE / f"crawl_run_id={crawl_run_id}"
    if overwrite:
        clear_output_run_dir(output_run_dir)

    transformed_at = utc_now()
    entity_counts: Counter[str] = Counter()
    bridge_counts: Counter[str] = Counter()
    errors: list[dict[str, Any]] = []

    for entity_type in ENTITY_TYPES:
        transformer = TRANSFORMERS[entity_type]
        bronze_file = bronze_run_dir / entity_type / "entities.jsonl"
        records = read_jsonl(bronze_file)
        silver_records: list[dict[str, Any]] = []

        for record in records:
            if entity_type == "manga":
                silver_record, record_errors, manga_tag_records, manga_cover_records = transformer(record, transformed_at)
                append_jsonl(output_run_dir / "manga_tag.jsonl", manga_tag_records)
                append_jsonl(output_run_dir / "manga_cover.jsonl", manga_cover_records)
                bridge_counts["manga_tag"] += len(manga_tag_records)
                bridge_counts["manga_cover"] += len(manga_cover_records)
            else:
                silver_record, record_errors = transformer(record, transformed_at)
            silver_records.append(silver_record)
            errors.extend(record_errors)

        append_jsonl(output_run_dir / f"{entity_type}.jsonl", silver_records)
        entity_counts[entity_type] += len(silver_records)

    relationship_file = bronze_run_dir / "relationships" / "relationships.jsonl"
    for relationship in read_jsonl(relationship_file):
        table_name = BRIDGE_TABLES.get((relationship.get("from_entity_type"), relationship.get("relationship_type")))
        if not table_name:
            continue

        append_jsonl(output_run_dir / f"{table_name}.jsonl", [bridge_record(relationship, transformed_at)])
        bridge_counts[table_name] += 1

    if errors:
        append_jsonl(output_run_dir / "errors" / "errors.jsonl", errors)

    summary = {
        "source": SOURCE,
        "crawl_run_id": crawl_run_id,
        "silver_schema_version": SILVER_SCHEMA_VERSION,
        "bronze_run_dir": str(bronze_run_dir),
        "output_run_dir": str(output_run_dir),
        "silver_transformed_at": transformed_at,
        "entity_counts": dict(sorted(entity_counts.items())),
        "bridge_counts": dict(sorted(bridge_counts.items())),
        "error_count": len(errors),
    }
    write_json(output_run_dir / "transform_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform MangaDex Bronze JSONL records into Silver domain records.")
    parser.add_argument("--bronze-run-dir", required=True, help="Path to data/bronze/mangadex/crawl_run_id=<id>.")
    parser.add_argument("--output-root", default="data/silver", help="Silver data output root.")
    parser.add_argument("--overwrite", action="store_true", help="Delete existing output for this crawl run before writing.")
    args = parser.parse_args()

    summary = run(
        bronze_run_dir=Path(args.bronze_run_dir),
        output_root=Path(args.output_root),
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
