# Crawler Service

Source adapters, crawl jobs, rate limiting, retry behavior, and raw artifacts.

## MangaDex Raw Crawler

The MangaDex crawler stores original API responses under `data/raw/mangadex`.

```powershell
python services/crawler-service/mangadex_raw_crawler.py --limit 10 --pages 1
```

After crawling chapters, the crawler backfills manga referenced by `relationships[type=manga]` but missing from the catalog crawl. This improves matching between `gold.gold_chapter_list` and `gold.gold_manga_catalog`.

Raw collection files use this shape:

```text
data/raw/mangadex/crawl_run_id=<run_id>/<entity_type>/page_000001.json
```

Backfilled manga records are stored as normal raw manga files:

```text
data/raw/mangadex/crawl_run_id=<run_id>/manga/backfill_missing_manga_000001.json
```

If a request fails, the crawler writes an error artifact:

```text
data/raw/mangadex/crawl_run_id=<run_id>/errors/<entity_type>/page_000001.json
```

Disable manga backfill only when debugging the original collection crawl:

```powershell
python services/crawler-service/mangadex_raw_crawler.py --disable-manga-backfill
```

Run with the bundled Codex Python on this machine:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/crawler-service/mangadex_raw_crawler.py --limit 10 --pages 1 --pause-seconds 0.5
```
