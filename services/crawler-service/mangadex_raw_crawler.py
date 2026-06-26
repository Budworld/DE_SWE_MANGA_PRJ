from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API_BASE_URL = "https://api.mangadex.org"
SOURCE = "mangadex"
RAW_SCHEMA_VERSION = "raw.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_url(endpoint: str, params: dict[str, Any]) -> str:
    query = urllib.parse.urlencode(params, doseq=True)
    return f"{API_BASE_URL}{endpoint}?{query}" if query else f"{API_BASE_URL}{endpoint}"


def fetch_json(endpoint: str, params: dict[str, Any], timeout_seconds: int) -> tuple[str, int, Any]:
    url = build_url(endpoint, params)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "web-manga-de-project/0.1",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")
        return url, response.status, json.loads(body)


def write_raw_response(
    output_root: Path,
    crawl_run_id: str,
    entity_type: str,
    endpoint: str,
    request_url: str,
    request_params: dict[str, Any],
    http_status: int,
    payload: Any,
    file_stem: str,
) -> Path:
    fetched_at = utc_now()
    response_hash = stable_json_hash(payload)
    target_dir = output_root / SOURCE / f"crawl_run_id={crawl_run_id}" / entity_type
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{file_stem}.json"

    raw_document = {
        "crawl_metadata": {
            "crawl_run_id": crawl_run_id,
            "source": SOURCE,
            "entity_type": entity_type,
            "endpoint": endpoint,
            "request_url": request_url,
            "request_params": request_params,
            "http_status": http_status,
            "fetched_at": fetched_at,
            "response_hash": response_hash,
            "schema_version": RAW_SCHEMA_VERSION,
        },
        "payload": payload,
    }

    target_file.write_text(json.dumps(raw_document, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_file


def write_raw_error(
    output_root: Path,
    crawl_run_id: str,
    entity_type: str,
    endpoint: str,
    request_url: str,
    request_params: dict[str, Any],
    error: Exception,
    file_stem: str,
) -> Path:
    fetched_at = utc_now()
    target_dir = output_root / SOURCE / f"crawl_run_id={crawl_run_id}" / "errors" / entity_type
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{file_stem}.json"

    raw_document = {
        "crawl_metadata": {
            "crawl_run_id": crawl_run_id,
            "source": SOURCE,
            "entity_type": entity_type,
            "endpoint": endpoint,
            "request_url": request_url,
            "request_params": request_params,
            "http_status": getattr(error, "code", None),
            "fetched_at": fetched_at,
            "response_hash": None,
            "schema_version": RAW_SCHEMA_VERSION,
        },
        "error": {
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    }

    target_file.write_text(json.dumps(raw_document, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_file


def write_crawl_run(
    output_root: Path,
    crawl_run_id: str,
    status: str,
    started_at: str,
    ended_at: str,
    summary: dict[str, Any] | None = None,
) -> Path:
    target_dir = output_root / SOURCE / f"crawl_run_id={crawl_run_id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "crawl_run.json"
    document = {
        "crawl_run_id": crawl_run_id,
        "source": SOURCE,
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at,
        "schema_version": RAW_SCHEMA_VERSION,
    }
    if summary is not None:
        document["summary"] = summary
    target_file.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_file


def crawl_collection(
    output_root: Path,
    crawl_run_id: str,
    entity_type: str,
    endpoint: str,
    limit: int,
    pages: int,
    start_offset: int,
    timeout_seconds: int,
    pause_seconds: float,
    extra_params: dict[str, Any] | None = None,
) -> list[Path]:
    written_files: list[Path] = []
    for page_index in range(pages):
        params = {
            "limit": limit,
            "offset": start_offset + page_index * limit,
        }
        if extra_params:
            params.update(extra_params)

        file_stem = f"page_{page_index + 1:06d}"
        request_url = build_url(endpoint, params)
        try:
            request_url, http_status, payload = fetch_json(endpoint, params, timeout_seconds)
            written_files.append(
                write_raw_response(
                    output_root=output_root,
                    crawl_run_id=crawl_run_id,
                    entity_type=entity_type,
                    endpoint=endpoint,
                    request_url=request_url,
                    request_params=params,
                    http_status=http_status,
                    payload=payload,
                    file_stem=file_stem,
                )
            )
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            written_files.append(
                write_raw_error(
                    output_root=output_root,
                    crawl_run_id=crawl_run_id,
                    entity_type=entity_type,
                    endpoint=endpoint,
                    request_url=request_url,
                    request_params=params,
                    error=error,
                    file_stem=file_stem,
                )
            )
            raise
        time.sleep(pause_seconds)
    return written_files


def payload_items(raw_file: Path) -> list[dict[str, Any]]:
    raw_document = json.loads(raw_file.read_text(encoding="utf-8"))
    payload = raw_document.get("payload") or {}
    data = payload.get("data") or []
    return [item for item in data if isinstance(item, dict)]


def relationship_ids(item: dict[str, Any], relationship_type: str) -> set[str]:
    ids: set[str] = set()
    for relationship in item.get("relationships") or []:
        if not isinstance(relationship, dict):
            continue
        if relationship.get("type") == relationship_type and relationship.get("id"):
            ids.add(relationship["id"])
    return ids


def entity_ids_from_raw_files(raw_run_dir: Path, entity_type: str) -> set[str]:
    entity_dir = raw_run_dir / entity_type
    if not entity_dir.exists():
        return set()

    ids: set[str] = set()
    for raw_file in sorted(entity_dir.glob("*.json")):
        for item in payload_items(raw_file):
            if item.get("id"):
                ids.add(item["id"])
    return ids


def chapter_referenced_manga_ids(raw_run_dir: Path) -> set[str]:
    chapter_dir = raw_run_dir / "chapter"
    if not chapter_dir.exists():
        return set()

    ids: set[str] = set()
    for raw_file in sorted(chapter_dir.glob("*.json")):
        for item in payload_items(raw_file):
            ids.update(relationship_ids(item, "manga"))
    return ids


def chunks(values: list[str], batch_size: int) -> list[list[str]]:
    return [values[index : index + batch_size] for index in range(0, len(values), batch_size)]


def backfill_missing_manga(
    output_root: Path,
    crawl_run_id: str,
    timeout_seconds: int,
    pause_seconds: float,
    batch_size: int,
) -> tuple[list[Path], dict[str, int]]:
    raw_run_dir = output_root / SOURCE / f"crawl_run_id={crawl_run_id}"
    existing_manga_ids = entity_ids_from_raw_files(raw_run_dir, "manga")
    referenced_manga_ids = chapter_referenced_manga_ids(raw_run_dir)
    missing_manga_ids = sorted(referenced_manga_ids - existing_manga_ids)

    stats = {
        "chapter_referenced_manga_count": len(referenced_manga_ids),
        "catalog_manga_count": len(existing_manga_ids),
        "missing_manga_detected_count": len(missing_manga_ids),
        "missing_manga_backfilled_count": 0,
        "missing_manga_backfill_failed_count": 0,
    }
    written_files: list[Path] = []

    for batch_index, batch_ids in enumerate(chunks(missing_manga_ids, batch_size), start=1):
        params = {
            "limit": len(batch_ids),
            "ids[]": batch_ids,
            "includes[]": ["author", "artist", "cover_art"],
        }
        file_stem = f"backfill_missing_manga_{batch_index:06d}"
        request_url = build_url("/manga", params)
        try:
            request_url, http_status, payload = fetch_json("/manga", params, timeout_seconds)
            data = payload.get("data") if isinstance(payload, dict) else []
            backfilled_count = len(data) if isinstance(data, list) else 0
            stats["missing_manga_backfilled_count"] += backfilled_count
            written_files.append(
                write_raw_response(
                    output_root=output_root,
                    crawl_run_id=crawl_run_id,
                    entity_type="manga",
                    endpoint="/manga",
                    request_url=request_url,
                    request_params=params,
                    http_status=http_status,
                    payload=payload,
                    file_stem=file_stem,
                )
            )
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            stats["missing_manga_backfill_failed_count"] += len(batch_ids)
            written_files.append(
                write_raw_error(
                    output_root=output_root,
                    crawl_run_id=crawl_run_id,
                    entity_type="manga",
                    endpoint="/manga",
                    request_url=request_url,
                    request_params=params,
                    error=error,
                    file_stem=file_stem,
                )
            )
            raise
        time.sleep(pause_seconds)

    return written_files, stats


def crawl_manga_feed(
    output_root: Path,
    crawl_run_id: str,
    translated_language: str,
    limit: int,
    pages_per_manga: int,
    max_manga: int,
    timeout_seconds: int,
    pause_seconds: float,
) -> tuple[list[Path], dict[str, int]]:
    raw_run_dir = output_root / SOURCE / f"crawl_run_id={crawl_run_id}"
    manga_ids = sorted(entity_ids_from_raw_files(raw_run_dir, "manga"))[:max_manga]
    stats = {
        "feed_manga_selected_count": len(manga_ids),
        "feed_request_count": 0,
        "feed_chapter_count": 0,
        "feed_failed_request_count": 0,
    }
    written_files: list[Path] = []

    for manga_id in manga_ids:
        endpoint = f"/manga/{manga_id}/feed"
        for page_index in range(pages_per_manga):
            params = {
                "limit": limit,
                "offset": page_index * limit,
                "translatedLanguage[]": [translated_language],
                "includes[]": ["manga", "scanlation_group"],
                "order[chapter]": "asc",
            }
            file_stem = f"feed_manga_{manga_id}_page_{page_index + 1:06d}"
            request_url = build_url(endpoint, params)
            stats["feed_request_count"] += 1
            try:
                request_url, http_status, payload = fetch_json(endpoint, params, timeout_seconds)
                data = payload.get("data") if isinstance(payload, dict) else []
                if isinstance(data, list):
                    stats["feed_chapter_count"] += len(data)
                written_files.append(
                    write_raw_response(
                        output_root=output_root,
                        crawl_run_id=crawl_run_id,
                        entity_type="chapter",
                        endpoint=endpoint,
                        request_url=request_url,
                        request_params=params,
                        http_status=http_status,
                        payload=payload,
                        file_stem=file_stem,
                    )
                )
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                stats["feed_failed_request_count"] += 1
                written_files.append(
                    write_raw_error(
                        output_root=output_root,
                        crawl_run_id=crawl_run_id,
                        entity_type="chapter",
                        endpoint=endpoint,
                        request_url=request_url,
                        request_params=params,
                        error=error,
                        file_stem=file_stem,
                    )
                )
                raise
            time.sleep(pause_seconds)

    return written_files, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch small MangaDex raw datasets.")
    parser.add_argument("--output-root", default="data/raw", help="Raw data output root.")
    parser.add_argument("--limit", type=int, default=10, help="Items per API request.")
    parser.add_argument("--pages", type=int, default=1, help="Pages per collection endpoint.")
    parser.add_argument("--start-offset", type=int, default=0, help="Starting MangaDex collection offset for paginated endpoints.")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--pause-seconds", type=float, default=1.0)
    parser.add_argument("--translated-language", default="en")
    parser.add_argument("--crawl-manga-feed", action="store_true", help="Fetch /manga/{id}/feed for crawled manga.")
    parser.add_argument("--feed-limit", type=int, default=100, help="Chapter feed items per manga request.")
    parser.add_argument("--feed-pages-per-manga", type=int, default=1, help="Feed pages to fetch per manga.")
    parser.add_argument("--max-manga-feed", type=int, default=50, help="Maximum crawled manga ids to fetch feeds for.")
    parser.add_argument("--disable-manga-backfill", action="store_true", help="Skip backfilling manga referenced by crawled chapters.")
    parser.add_argument("--manga-backfill-batch-size", type=int, default=100, help="Manga ids per enrichment request.")
    args = parser.parse_args()
    if args.feed_limit < 1:
        parser.error("--feed-limit must be at least 1")
    if args.feed_pages_per_manga < 1:
        parser.error("--feed-pages-per-manga must be at least 1")
    if args.max_manga_feed < 1:
        parser.error("--max-manga-feed must be at least 1")
    if args.manga_backfill_batch_size < 1:
        parser.error("--manga-backfill-batch-size must be at least 1")

    output_root = Path(args.output_root)
    crawl_run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    started_at = utc_now()

    endpoints = [
        ("manga", "/manga", {"includes[]": ["author", "artist", "cover_art"]}),
        ("chapter", "/chapter", {"translatedLanguage[]": [args.translated_language], "includes[]": ["manga", "scanlation_group"]}),
        ("cover", "/cover", {"includes[]": ["manga"]}),
        ("author", "/author", None),
        ("tag", "/manga/tag", None),
        ("scanlation_group", "/group", None),
    ]

    status = "success"
    written_files: list[Path] = []
    crawl_summary: dict[str, Any] = {}
    try:
        for entity_type, endpoint, extra_params in endpoints:
            endpoint_pages = 1 if entity_type == "tag" else args.pages
            endpoint_start_offset = 0 if entity_type == "tag" else args.start_offset
            written_files.extend(
                crawl_collection(
                    output_root=output_root,
                    crawl_run_id=crawl_run_id,
                    entity_type=entity_type,
                    endpoint=endpoint,
                    limit=args.limit,
                    pages=endpoint_pages,
                    start_offset=endpoint_start_offset,
                    timeout_seconds=args.timeout_seconds,
                    pause_seconds=args.pause_seconds,
                    extra_params=extra_params,
                )
            )
        if args.crawl_manga_feed:
            feed_files, feed_stats = crawl_manga_feed(
                output_root=output_root,
                crawl_run_id=crawl_run_id,
                translated_language=args.translated_language,
                limit=args.feed_limit,
                pages_per_manga=args.feed_pages_per_manga,
                max_manga=args.max_manga_feed,
                timeout_seconds=args.timeout_seconds,
                pause_seconds=args.pause_seconds,
            )
            written_files.extend(feed_files)
            crawl_summary["manga_feed"] = feed_stats
        if not args.disable_manga_backfill:
            backfill_files, backfill_stats = backfill_missing_manga(
                output_root=output_root,
                crawl_run_id=crawl_run_id,
                timeout_seconds=args.timeout_seconds,
                pause_seconds=args.pause_seconds,
                batch_size=args.manga_backfill_batch_size,
            )
            written_files.extend(backfill_files)
            crawl_summary["manga_backfill"] = backfill_stats
    except Exception:
        status = "failed"
        raise
    finally:
        crawl_run_file = write_crawl_run(output_root, crawl_run_id, status, started_at, utc_now(), crawl_summary)

    print(f"crawl_run_id={crawl_run_id}")
    print(f"crawl_run_file={crawl_run_file}")
    for path in written_files:
        print(path)


if __name__ == "__main__":
    main()
