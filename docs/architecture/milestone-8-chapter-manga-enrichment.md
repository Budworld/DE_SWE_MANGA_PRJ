# Milestone 8: Chapter-Manga Enrichment

Milestone 8 fixes the mismatch between crawled chapters and crawled manga.

The previous crawler collected `/manga` and `/chapter` as independent MangaDex collections. A chapter can reference a manga that was not present in the catalog batch, so `gold.gold_chapter_list.manga_id` could be null after dbt joined chapters to manga.

## Design

The crawler now uses a hybrid ingestion flow:

```text
crawl manga catalog
crawl latest chapters
extract manga ids from chapter relationships
backfill missing manga through /manga?ids[]=...
Raw -> Bronze -> Silver -> dbt Gold
validate chapter/manga match quality
```

This keeps the existing catalog crawl while adding a dimension backfill step for manga referenced by chapters.

## Raw Contract

Backfilled manga records are written to the same raw entity folder:

```text
data/raw/mangadex/crawl_run_id=<run_id>/manga/backfill_missing_manga_000001.json
```

`crawl_run.json` includes a `summary.manga_backfill` block:

```json
{
  "chapter_referenced_manga_count": 250,
  "catalog_manga_count": 100,
  "missing_manga_detected_count": 150,
  "missing_manga_backfilled_count": 150,
  "missing_manga_backfill_failed_count": 0
}
```

Bronze and Silver do not need a new schema because the enrichment still produces normal MangaDex `manga` API payloads.

## Monitoring

The existing `chapters_without_manga` data quality check remains.

Milestone 8 adds:

```text
chapter_manga_match_rate_percent
```

Gold catalog tables are also filtered to readable manga only:

```text
gold.gold_manga_catalog
gold.gold_manga_detail
```

only include manga whose `source_manga_id` exists in `stg_chapter`. Raw, Bronze, Silver, and staging still keep the full crawled dataset for lineage and future backfills.

Milestone 8 also adds:

```text
manga_without_chapters
```

Expected result for the web-facing catalog is `0`.

The latest feed is also web-facing:

```text
gold.gold_latest_chapters
```

It joins `gold.gold_chapter_list` to `gold.gold_manga_catalog` and only returns chapters whose manga is present in the readable catalog. This prevents `/latest` from rendering rows without `manga_title` or `cover_url`. `gold.gold_chapter_list` still keeps unmatched historical chapters for debugging and future backfill.

Latest-specific checks:

```text
latest_chapters_missing_manga_title
latest_chapters_missing_cover
```

Expected result for `latest_chapters_missing_manga_title` is `0`. Missing cover metadata is treated as a warning because MangaDex records can exist without cover metadata.

Expected result after a healthy run:

```sql
select count(*)
from gold.gold_chapter_list
where manga_id is null;
```

should return `0` or a very small number if MangaDex omitted/deleted a referenced manga.

## Run

Local small crawl:

```powershell
python services/crawler-service/mangadex_raw_crawler.py --limit 10 --pages 1 --pause-seconds 0.5
```

Disable enrichment only for debugging:

```powershell
python services/crawler-service/mangadex_raw_crawler.py --disable-manga-backfill
```

Airflow uses the same crawler, so DAG runs inherit the enrichment behavior automatically.
