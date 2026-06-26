# Airflow Orchestration

Milestone 4 adds Airflow as the orchestration layer for the existing MangaDex data pipeline.

Airflow does not replace the current pipeline logic:

```text
Airflow DAG
  -> crawler Python script writes Raw
  -> data-pipeline Python scripts write Bronze and Silver
  -> load script writes Silver into PostgreSQL
  -> dbt builds Gold
  -> validation checks Gold row counts
```

## Services

Docker Compose defines:

```text
airflow-init
airflow-webserver
airflow-scheduler
```

The Airflow container mounts the project at:

```text
/opt/airflow/project
```

The DAG file is copied into the Airflow image from:

```text
services/airflow/dags/mangadex_pipeline.py
```

For local development, Docker Compose also mounts that folder into:

```text
/opt/airflow/dags
```

After changing DAG code, restart the Airflow services if the UI does not refresh the DAG quickly.

## Run

Initialize Airflow metadata and admin user:

```powershell
docker compose up airflow-init
```

Start Airflow:

```powershell
docker compose up -d postgres airflow-webserver airflow-scheduler
```

Open:

```text
http://localhost:8080
```

Default local login:

```text
username: admin
password: admin
```

Trigger the DAG manually:

```text
mangadex_data_pipeline
```

## Supabase Data Target

Milestone 7 can run the same DAG into Supabase Postgres while keeping Airflow metadata local.

Create a local env file:

```powershell
Copy-Item .env.supabase.example .env.supabase
```

Replace the password placeholder, then start Airflow with the env file:

```powershell
docker compose --env-file .env.supabase up airflow-init
docker compose --env-file .env.supabase up -d postgres airflow-webserver airflow-scheduler manga-service
```

In this mode:

```text
local postgres  -> Airflow metadata
Supabase        -> silver, staging, gold, monitoring
```

The normal workflow is still one manual Airflow trigger. You do not need to run the Raw/Bronze/Silver/load/dbt commands manually.

## DAG Params

Defaults are intentionally small for demo runs:

```text
limit: 10
pages: 1
start_offset: 0
pause_seconds: 0.5
translated_language: en
crawl_manga_feed: true
feed_limit: 100
feed_pages_per_manga: 1
max_manga_feed: 50
```

Increase `start_offset` when you want the next DAG run to fetch a different MangaDex page instead of crawling the first page again.

`crawl_manga_feed` fetches `/manga/{id}/feed` for manga in the current catalog batch. This is the preferred way to grow the readable web catalog because it guarantees crawled manga also have chapters.

## Task Order

```text
crawl_mangadex_raw
  -> raw_to_bronze
  -> bronze_to_silver
  -> load_silver_to_postgres
  -> dbt_build
  -> validate_gold_tables
```

## Validation

The final task fails if any required Gold table is empty:

```text
gold.gold_manga_catalog
gold.gold_manga_detail
gold.gold_chapter_list
gold.gold_latest_chapters
```

## Local Checks

```powershell
python -m py_compile services/airflow/dags/mangadex_pipeline.py
docker compose config --services
```

MangaDex network/proxy issues should fail the crawl task visibly in Airflow.
