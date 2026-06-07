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


def write_crawl_run(output_root: Path, crawl_run_id: str, status: str, started_at: str, ended_at: str) -> Path:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch small MangaDex raw datasets.")
    parser.add_argument("--output-root", default="data/raw", help="Raw data output root.")
    parser.add_argument("--limit", type=int, default=10, help="Items per API request.")
    parser.add_argument("--pages", type=int, default=1, help="Pages per collection endpoint.")
    parser.add_argument("--start-offset", type=int, default=0, help="Starting MangaDex collection offset for paginated endpoints.")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--pause-seconds", type=float, default=1.0)
    parser.add_argument("--translated-language", default="en")
    args = parser.parse_args()

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
    except Exception:
        status = "failed"
        raise
    finally:
        crawl_run_file = write_crawl_run(output_root, crawl_run_id, status, started_at, utc_now())

    print(f"crawl_run_id={crawl_run_id}")
    print(f"crawl_run_file={crawl_run_file}")
    for path in written_files:
        print(path)


if __name__ == "__main__":
    main()
