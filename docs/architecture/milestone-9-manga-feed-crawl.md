# Milestone 9: Manga Feed Crawl

Milestone 9 expands the readable catalog by crawling chapters from each manga's feed.

Previously, the pipeline crawled MangaDex `/manga` and global `/chapter` collections independently. Milestone 8 made Gold safe for the web by filtering out unreadable manga and latest rows without title/cover metadata. Milestone 9 improves completeness by fetching chapters directly for the crawled manga.

## Design

```text
crawl manga catalog
crawl global latest chapters
crawl /manga/{id}/feed for catalog manga
backfill manga referenced by chapters
Raw -> Bronze -> Silver -> Supabase
dbt Gold readable catalog/latest
```

The `/manga/{id}/feed` step writes MangaDex chapter payloads into the normal raw chapter folder, so Bronze and Silver continue to use the same schema and parsing logic.

## Raw Contract

Feed crawl files are stored as raw chapter files:

```text
data/raw/mangadex/crawl_run_id=<run_id>/chapter/feed_manga_<manga_id>_page_000001.json
```

`crawl_run.json` includes a `summary.manga_feed` block:

```json
{
  "feed_manga_selected_count": 50,
  "feed_request_count": 50,
  "feed_chapter_count": 500,
  "feed_failed_request_count": 0
}
```

## Airflow Params

The DAG enables feed crawl by default for demo runs:

```text
crawl_manga_feed=true
feed_limit=100
feed_pages_per_manga=1
max_manga_feed=50
```

Keep these small when using a free Supabase tier or an unstable MangaDex/proxy connection.

## Validation

After a healthy run:

```sql
select count(*) from gold.gold_manga_catalog;
select count(*) from gold.gold_latest_chapters;
select count(*) from monitoring.data_quality_checks;
```

Expected behavior:

- `gold.gold_manga_catalog` grows beyond the small filtered catalog from Milestone 8.
- `manga_without_chapters` remains `0`.
- `/manga` shows more readable manga.
- `/chapters/latest` keeps manga titles and cover URLs.
