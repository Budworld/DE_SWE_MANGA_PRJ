from __future__ import annotations

import argparse
import json
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE = "mangadex"
BRONZE_SCHEMA_VERSION = "bronze.v1"
ENTITY_TYPES = ("manga", "chapter", "cover", "author", "tag", "scanlation_group")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def get_crawl_run_id(raw_run_dir: Path) -> str:
    if raw_run_dir.name.startswith("crawl_run_id="):
        return raw_run_dir.name.split("=", 1)[1]

    crawl_run_file = raw_run_dir / "crawl_run.json"
    if crawl_run_file.exists():
        return read_json(crawl_run_file)["crawl_run_id"]

    raise ValueError(f"Cannot infer crawl_run_id from {raw_run_dir}")


def make_bronze_record_id(entity_type: str, entity_id: str, crawl_run_id: str) -> str:
    return f"{SOURCE}:{entity_type}:{entity_id}:{crawl_run_id}"


def make_bronze_relationship_id(
    from_entity_type: str,
    from_entity_id: str,
    relationship_type: str,
    to_entity_id: str,
    crawl_run_id: str,
    ordinal: int,
) -> str:
    return (
        f"{SOURCE}:{from_entity_type}:{from_entity_id}:"
        f"{relationship_type}:{to_entity_id}:{ordinal}:{crawl_run_id}"
    )


def validate_raw_document(raw_document: dict[str, Any], raw_file: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    metadata = raw_document.get("crawl_metadata")
    payload = raw_document.get("payload")

    if not isinstance(metadata, dict):
        errors.append({"raw_file_path": str(raw_file), "error_type": "missing_metadata", "error_message": "Missing crawl_metadata object"})
        return errors

    if not isinstance(payload, dict):
        errors.append({"raw_file_path": str(raw_file), "error_type": "missing_payload", "error_message": "Missing payload object"})
        return errors

    if payload.get("result") != "ok":
        errors.append({"raw_file_path": str(raw_file), "error_type": "invalid_result", "error_message": f"Expected payload.result=ok, got {payload.get('result')}"})

    if not isinstance(payload.get("data"), list):
        errors.append({"raw_file_path": str(raw_file), "error_type": "invalid_data", "error_message": "Expected payload.data to be a list"})

    return errors


def parse_raw_file(raw_file: Path, output_run_dir: Path, bronze_ingested_at: str) -> tuple[int, int, list[dict[str, Any]]]:
    raw_document = read_json(raw_file)
    validation_errors = validate_raw_document(raw_document, raw_file)
    if validation_errors:
        return 0, 0, validation_errors

    metadata = raw_document["crawl_metadata"]
    payload = raw_document["payload"]
    crawl_run_id = metadata["crawl_run_id"]
    entity_type = metadata["entity_type"]
    entity_records: list[dict[str, Any]] = []
    relationship_records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for item_index, item in enumerate(payload["data"]):
        if not isinstance(item, dict):
            errors.append({
                "raw_file_path": str(raw_file),
                "error_type": "invalid_entity",
                "error_message": f"payload.data[{item_index}] is not an object",
            })
            continue

        source_entity_id = item.get("id")
        source_entity_type = item.get("type", entity_type)
        relationships = item.get("relationships") or []

        if not source_entity_id:
            errors.append({
                "raw_file_path": str(raw_file),
                "error_type": "missing_entity_id",
                "error_message": f"payload.data[{item_index}] is missing id",
            })
            continue

        if not isinstance(relationships, list):
            errors.append({
                "raw_file_path": str(raw_file),
                "error_type": "invalid_relationships",
                "error_message": f"relationships for {source_entity_id} is not a list",
            })
            relationships = []

        entity_records.append({
            "bronze_record_id": make_bronze_record_id(source_entity_type, source_entity_id, crawl_run_id),
            "source": SOURCE,
            "source_entity_type": source_entity_type,
            "source_entity_id": source_entity_id,
            "crawl_run_id": crawl_run_id,
            "raw_file_path": str(raw_file),
            "raw_response_hash": metadata.get("response_hash"),
            "raw_fetched_at": metadata.get("fetched_at"),
            "bronze_ingested_at": bronze_ingested_at,
            "bronze_schema_version": BRONZE_SCHEMA_VERSION,
            "attributes": item.get("attributes") or {},
            "relationships": relationships,
        })

        for relationship_index, relationship in enumerate(relationships):
            if not isinstance(relationship, dict):
                errors.append({
                    "raw_file_path": str(raw_file),
                    "error_type": "invalid_relationship",
                    "error_message": f"relationships[{relationship_index}] for {source_entity_id} is not an object",
                })
                continue

            to_entity_id = relationship.get("id")
            relationship_type = relationship.get("type")
            if not to_entity_id or not relationship_type:
                errors.append({
                    "raw_file_path": str(raw_file),
                    "error_type": "invalid_relationship_ref",
                    "error_message": f"Relationship for {source_entity_id} is missing id or type",
                })
                continue

            relationship_records.append({
                "bronze_relationship_id": make_bronze_relationship_id(
                    source_entity_type,
                    source_entity_id,
                    relationship_type,
                    to_entity_id,
                    crawl_run_id,
                    relationship_index,
                ),
                "source": SOURCE,
                "crawl_run_id": crawl_run_id,
                "from_entity_type": source_entity_type,
                "from_entity_id": source_entity_id,
                "relationship_type": relationship_type,
                "to_entity_type": relationship_type,
                "to_entity_id": to_entity_id,
                "raw_file_path": str(raw_file),
                "bronze_ingested_at": bronze_ingested_at,
                "bronze_schema_version": BRONZE_SCHEMA_VERSION,
            })

    append_jsonl(output_run_dir / entity_type / "entities.jsonl", entity_records)
    append_jsonl(output_run_dir / "relationships" / "relationships.jsonl", relationship_records)
    return len(entity_records), len(relationship_records), errors


def clear_output_run_dir(output_run_dir: Path) -> None:
    if not output_run_dir.exists():
        return

    for path in sorted(output_run_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()


def run(raw_run_dir: Path, output_root: Path, overwrite: bool) -> dict[str, Any]:
    crawl_run_id = get_crawl_run_id(raw_run_dir)
    output_run_dir = output_root / SOURCE / f"crawl_run_id={crawl_run_id}"
    if overwrite:
        clear_output_run_dir(output_run_dir)

    bronze_ingested_at = utc_now()
    entity_counts: Counter[str] = Counter()
    relationship_counts: Counter[str] = Counter()
    raw_file_counts: Counter[str] = Counter()
    all_errors: list[dict[str, Any]] = []

    for entity_type in ENTITY_TYPES:
        entity_dir = raw_run_dir / entity_type
        if not entity_dir.exists():
            continue

        for raw_file in sorted(entity_dir.glob("*.json")):
            entity_count, relationship_count, errors = parse_raw_file(raw_file, output_run_dir, bronze_ingested_at)
            entity_counts[entity_type] += entity_count
            relationship_counts[entity_type] += relationship_count
            raw_file_counts[entity_type] += 1
            all_errors.extend(errors)

    if all_errors:
        append_jsonl(output_run_dir / "errors" / "errors.jsonl", all_errors)

    summary = {
        "source": SOURCE,
        "crawl_run_id": crawl_run_id,
        "bronze_schema_version": BRONZE_SCHEMA_VERSION,
        "raw_run_dir": str(raw_run_dir),
        "output_run_dir": str(output_run_dir),
        "bronze_ingested_at": bronze_ingested_at,
        "entity_counts": dict(sorted(entity_counts.items())),
        "relationship_counts_by_from_entity": dict(sorted(relationship_counts.items())),
        "raw_file_counts": dict(sorted(raw_file_counts.items())),
        "error_count": len(all_errors),
    }
    write_json(output_run_dir / "ingest_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse MangaDex raw JSON files into Bronze JSONL records.")
    parser.add_argument("--raw-run-dir", required=True, help="Path to data/raw/mangadex/crawl_run_id=<id>.")
    parser.add_argument("--output-root", default="data/bronze", help="Bronze data output root.")
    parser.add_argument("--overwrite", action="store_true", help="Delete existing output for this crawl run before writing.")
    args = parser.parse_args()

    summary = run(
        raw_run_dir=Path(args.raw_run_dir),
        output_root=Path(args.output_root),
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
