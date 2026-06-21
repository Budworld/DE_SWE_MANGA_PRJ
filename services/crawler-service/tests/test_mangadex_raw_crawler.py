from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "mangadex_raw_crawler.py"
SPEC = importlib.util.spec_from_file_location("mangadex_raw_crawler", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
mangadex_raw_crawler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mangadex_raw_crawler)


def write_raw(path: Path, entity_type: str, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "crawl_metadata": {
                    "crawl_run_id": "run-1",
                    "entity_type": entity_type,
                    "schema_version": "raw.v1",
                },
                "payload": {"result": "ok", "data": data},
            }
        ),
        encoding="utf-8",
    )


def test_chapter_referenced_manga_ids_reads_manga_relationships(tmp_path: Path) -> None:
    raw_run_dir = tmp_path / "mangadex" / "crawl_run_id=run-1"
    write_raw(
        raw_run_dir / "chapter" / "page_000001.json",
        "chapter",
        [
            {"id": "chapter-1", "relationships": [{"type": "manga", "id": "manga-1"}]},
            {"id": "chapter-2", "relationships": [{"type": "manga", "id": "manga-2"}]},
            {"id": "chapter-3", "relationships": [{"type": "scanlation_group", "id": "group-1"}]},
        ],
    )

    assert mangadex_raw_crawler.chapter_referenced_manga_ids(raw_run_dir) == {"manga-1", "manga-2"}


def test_backfill_missing_manga_detects_only_missing_ids(tmp_path: Path, monkeypatch) -> None:
    output_root = tmp_path
    raw_run_dir = output_root / "mangadex" / "crawl_run_id=run-1"
    write_raw(raw_run_dir / "manga" / "page_000001.json", "manga", [{"id": "manga-1"}])
    write_raw(
        raw_run_dir / "chapter" / "page_000001.json",
        "chapter",
        [
            {"id": "chapter-1", "relationships": [{"type": "manga", "id": "manga-1"}]},
            {"id": "chapter-2", "relationships": [{"type": "manga", "id": "manga-2"}]},
        ],
    )

    calls = []

    def fake_fetch_json(endpoint: str, params: dict, timeout_seconds: int):
        calls.append((endpoint, params, timeout_seconds))
        return "https://example.test", 200, {"result": "ok", "data": [{"id": "manga-2", "type": "manga"}]}

    monkeypatch.setattr(mangadex_raw_crawler, "fetch_json", fake_fetch_json)
    written_files, stats = mangadex_raw_crawler.backfill_missing_manga(
        output_root=output_root,
        crawl_run_id="run-1",
        timeout_seconds=30,
        pause_seconds=0,
        batch_size=100,
    )

    assert len(written_files) == 1
    assert calls[0][0] == "/manga"
    assert calls[0][1]["ids[]"] == ["manga-2"]
    assert stats["chapter_referenced_manga_count"] == 2
    assert stats["catalog_manga_count"] == 1
    assert stats["missing_manga_detected_count"] == 1
    assert stats["missing_manga_backfilled_count"] == 1
