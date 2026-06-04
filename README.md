# Web Manga Platform

Monorepo skeleton for a manga web platform that combines SWE, DE, and AI work:

- SWE: web app, admin app, API services, auth, domain services.
- DE: crawler, raw/bronze/silver/gold pipeline, PostgreSQL, dbt.
- AI: future OCR and translation service for manga content.

Current source is **MangaDex only**. Other sources can be added later through source adapters, but Milestone 1 focuses on building a clean data foundation first.

## Milestone 2: Manga Catalog API

Milestone 2 exposes dbt Gold tables through a read-only FastAPI service:

```text
PostgreSQL gold tables
  -> services/manga-service
  -> future web app
```

API endpoints:

```text
GET /health
GET /manga
GET /manga/{manga_id}
GET /manga/{manga_id}/chapters
GET /chapters/latest
```

Run locally:

```powershell
docker compose up -d postgres
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r services/manga-service/requirements.txt
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn app.main:app --app-dir services/manga-service --host 0.0.0.0 --port 8000
```

Smoke:

```powershell
curl http://localhost:8000/health
curl "http://localhost:8000/manga?limit=10&offset=0"
curl "http://localhost:8000/chapters/latest?limit=10"
```

Detailed Milestone 2 architecture, build, run, and test docs:

```text
docs/architecture/milestone-2-manga-api.md
```

## Milestone 3: Web Reader Preview

Milestone 3 adds a React/Vite web UI with real MangaDex images:

```text
Gold tables -> manga-service API -> web UI
                           |
                           -> cover_url
                           -> chapter page image URLs
```

Views:

```text
/catalog
/manga/:manga_id
/latest
/chapters/:source_chapter_id/read
```

Run:

```powershell
docker compose up -d postgres
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn app.main:app --app-dir services/manga-service --host 0.0.0.0 --port 8000
cd apps/web
npm install
npm run dev
```

Detailed docs:

```text
docs/architecture/milestone-3-web-reader-preview.md
```

## Milestone 1: Local DE Pipeline MVP

Milestone 1 proves that the project can ingest MangaDex data and transform it through a complete local data pipeline:

```text
MangaDex API
  -> Raw JSON
  -> Bronze JSONL
  -> Silver JSONL
  -> PostgreSQL silver schema
  -> dbt staging views
  -> dbt gold tables
```

Verified result:

```text
dbt build: PASS=34 WARN=0 ERROR=0

gold.gold_manga_catalog      10 rows
gold.gold_manga_detail       10 rows
gold.gold_chapter_list       10 rows
gold.gold_latest_chapters    10 rows
```

This is not production scale yet. It is a local MVP that establishes the data model, lineage, transformations, and dbt-based Gold layer.

## Repository Structure

```text
apps/
  web/                         User-facing manga reader
  admin/                       Admin tools for data, crawler jobs, translations

services/
  crawler-service/             MangaDex crawler and future source adapters
  data-pipeline/               Raw -> Bronze -> Silver loaders and transforms
  dbt/                         dbt project for Silver -> Gold
  api-gateway/                 Future API gateway
  manga-service/               Future manga domain service
  auth-service/                Future auth service
  ai-translation-service/      Future OCR/translation service

data/
  raw/                         Immutable source responses, ignored by Git
  bronze/                      Parsed source-shaped JSONL, ignored by Git
  silver/                      Normalized domain JSONL, ignored by Git
  gold/                        Reserved for file-based Gold if needed

docs/
  data/                        Data layer docs and ERDs
```

## How To Crawl Data From MangaDex

The crawler is here:

```text
services/crawler-service/mangadex_raw_crawler.py
```

It calls public MangaDex API endpoints and stores each response as a raw artifact.

Run:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/crawler-service/mangadex_raw_crawler.py --limit 10 --pages 1 --pause-seconds 0.5
```

Current crawled entity types:

```text
manga
chapter
cover
author
tag
scanlation_group
```

The crawler writes data like this:

```text
data/raw/mangadex/crawl_run_id=<crawl_run_id>/
  crawl_run.json
  manga/page_000001.json
  chapter/page_000001.json
  cover/page_000001.json
  author/page_000001.json
  tag/page_000001.json
  scanlation_group/page_000001.json
```

If MangaDex is blocked by the network, use a VPN/proxy first. The crawler also writes failed requests into:

```text
data/raw/mangadex/crawl_run_id=<crawl_run_id>/errors/<entity_type>/page_000001.json
```

Raw data is ignored by Git on purpose. Do not commit crawled data.

## Raw Layer

Raw stores source responses as immutable artifacts. It preserves what MangaDex returned and wraps it with crawl metadata.

Each raw response has:

```json
{
  "crawl_metadata": {
    "crawl_run_id": "...",
    "source": "mangadex",
    "entity_type": "manga",
    "endpoint": "/manga",
    "request_url": "https://api.mangadex.org/manga?...",
    "request_params": {},
    "http_status": 200,
    "fetched_at": "2026-06-02T05:52:20Z",
    "response_hash": "sha256...",
    "schema_version": "raw.v1"
  },
  "payload": {
    "result": "ok",
    "response": "collection",
    "data": []
  }
}
```

Raw contains:

- Original MangaDex payload.
- Request URL and params.
- HTTP status.
- Fetch time.
- Response hash.
- Crawl run id.
- Error artifact if the request failed.

Raw does not clean, join, deduplicate, or normalize business fields. It is the replay/debug layer.

Detailed docs and ERD:

```text
docs/data/raw-layer.md
```

## Bronze Layer

Bronze parses Raw collection responses into source-shaped records.

Run:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/mangadex_raw_to_bronze.py --raw-run-dir "data/raw/mangadex/crawl_run_id=<crawl_run_id>" --overwrite
```

Output:

```text
data/bronze/mangadex/crawl_run_id=<crawl_run_id>/
  manga/entities.jsonl
  chapter/entities.jsonl
  cover/entities.jsonl
  author/entities.jsonl
  tag/entities.jsonl
  scanlation_group/entities.jsonl
  relationships/relationships.jsonl
  ingest_summary.json
```

Bronze entity records keep:

- `source_entity_id`
- `source_entity_type`
- `attributes`
- `relationships`
- raw file path
- raw response hash
- crawl lineage

Bronze also extracts MangaDex `relationships[]` into `relationships.jsonl`.

Bronze does light validation only. It does not become a business model yet.

Detailed docs and ERD:

```text
docs/data/bronze-layer.md
```

## Silver Layer

Silver converts Bronze source-shaped records into normalized domain records.

Run:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/mangadex_bronze_to_silver.py --bronze-run-dir "data/bronze/mangadex/crawl_run_id=<crawl_run_id>" --overwrite
```

Output:

```text
data/silver/mangadex/crawl_run_id=<crawl_run_id>/
  manga.jsonl
  chapter.jsonl
  cover.jsonl
  author.jsonl
  tag.jsonl
  scanlation_group.jsonl
  manga_author.jsonl
  manga_artist.jsonl
  manga_tag.jsonl
  manga_cover.jsonl
  chapter_manga.jsonl
  chapter_scanlation_group.jsonl
  transform_summary.json
```

Silver extracts and normalizes key fields:

- manga title, language, status, year, content rating
- chapter number, volume, translated language, page count
- author names and links
- cover file names
- tag names and groups
- scanlation group names

Silver also creates bridge tables:

```text
manga_author
manga_artist
manga_tag
manga_cover
chapter_manga
chapter_scanlation_group
```

### Why Silver ERD Is Designed This Way

Silver is designed as a normalized domain model because:

- MangaDex relationships are nested and source-shaped; the app needs explicit business relationships.
- Many relationships are many-to-many, such as manga-author, manga-artist, and manga-tag.
- Chapter belongs to manga, but MangaDex exposes that through relationship references, so Silver makes it explicit.
- Cover is separated because cover metadata can change independently from manga metadata.
- Tags are separated because they are reusable dimensions for search, filters, and analytics.
- Scanlation groups are separated because chapters can be analyzed by translation group later.

One MangaDex detail: `manga_tag` is not extracted from `relationships[]`; MangaDex stores tags inside `manga.attributes.tags`. The Silver transformer handles that separately.

Detailed docs and ERD:

```text
docs/data/silver-layer.md
```

## Load Silver Into PostgreSQL

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Install loader dependency:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r services/data-pipeline/requirements.txt
```

Load Silver:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/load_silver_to_postgres.py --silver-run-dir "data/silver/mangadex/crawl_run_id=<crawl_run_id>" --overwrite
```

Default database:

```text
postgresql://web_manga:web_manga@localhost:5432/web_manga
```

The loader creates PostgreSQL schema `silver` and stores each Silver record as JSONB. This keeps loading simple while dbt handles SQL modeling afterward.

## dbt Gold Layer

Install dbt:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r services/dbt/requirements.txt
```

Check connection:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" debug --project-dir services/dbt --profiles-dir services/dbt
```

Build Gold:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
```

dbt creates:

```text
staging.stg_manga
staging.stg_chapter
staging.stg_cover
staging.stg_author
staging.stg_tag
staging.stg_scanlation_group
...

gold.gold_manga_catalog
gold.gold_manga_detail
gold.gold_chapter_list
gold.gold_latest_chapters
```

### Why Gold ERD Is Designed This Way

Gold is not a normalized source model. Gold is designed around product use cases:

- `gold_manga_catalog`: fast manga listing, filtering, and search.
- `gold_manga_detail`: manga detail page with authors, artists, tags, cover, descriptions.
- `gold_chapter_list`: chapter list for a manga page.
- `gold_latest_chapters`: homepage/latest updates feed.

Gold intentionally denormalizes some data:

- author names are aggregated into JSON arrays
- tag names are aggregated into JSON arrays
- cover file name is attached to manga-facing views
- manga title is attached to chapter-facing views

This avoids forcing the API/web layer to join many normalized Silver tables for common read paths.

Detailed docs and ERD:

```text
docs/data/gold-layer.md
```

## Full Local Run Order

Replace `<crawl_run_id>` with the crawl run folder you generated.

```powershell
# 1. Crawl MangaDex Raw
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/crawler-service/mangadex_raw_crawler.py --limit 10 --pages 1 --pause-seconds 0.5

# 2. Raw -> Bronze
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/mangadex_raw_to_bronze.py --raw-run-dir "data/raw/mangadex/crawl_run_id=<crawl_run_id>" --overwrite

# 3. Bronze -> Silver
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/mangadex_bronze_to_silver.py --bronze-run-dir "data/bronze/mangadex/crawl_run_id=<crawl_run_id>" --overwrite

# 4. Start PostgreSQL
docker compose up -d postgres

# 5. Load Silver to PostgreSQL
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/load_silver_to_postgres.py --silver-run-dir "data/silver/mangadex/crawl_run_id=<crawl_run_id>" --overwrite

# 6. Build Gold with dbt
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
```

## Current Tech Stack

- Python: crawler and local transforms.
- PostgreSQL: Silver landing schema and Gold marts.
- dbt-postgres: staging models, Gold marts, tests, lineage.
- Docker Compose: local infrastructure.

Later additions:

- Airflow: orchestrate crawler and pipeline tasks.
- Spark: scale Raw/Bronze/Silver transforms and write Parquet.
- Kafka: event-driven crawler and pipeline notifications.
- FastAPI/Next.js: API and web reader.
- AI translation service: OCR and multilingual manga translation.

## Legal Note

Only crawl sources that allow API usage/crawling or data that you have permission to use. MangaDex is used here as a structured public API source for educational data engineering work.
