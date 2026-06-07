# Milestone 4: Airflow Pipeline Orchestration

Milestone 4 turns the existing manual DE pipeline into an observable Airflow DAG.

The important design decision is that Airflow only orchestrates. It does not rewrite crawler, transformation, loading, or dbt logic.

```text
MangaDex API
  -> Raw JSON
  -> Bronze JSONL
  -> Silver JSONL
  -> PostgreSQL silver schema
  -> dbt staging and Gold
  -> manga-service and web UI read Gold
```

## Scope

Included:

- Airflow services in Docker Compose.
- Manual DAG `mangadex_data_pipeline`.
- Task-level orchestration for the existing scripts.
- `crawl_run_id` propagation through Airflow XCom.
- Gold table row-count validation.
- Small default crawl params for demo.

Deferred:

- Scheduled production runs.
- Spark.
- Kafka.
- Airflow secrets backend.
- Persisting MangaDex at-home page metadata.
- UI/reader completion.

## Runtime Contract

The crawler prints:

```text
crawl_run_id=<crawl_run_id>
```

The DAG captures that value and passes it to downstream tasks. Each task works with deterministic run paths:

```text
data/raw/mangadex/crawl_run_id=<crawl_run_id>
data/bronze/mangadex/crawl_run_id=<crawl_run_id>
data/silver/mangadex/crawl_run_id=<crawl_run_id>
```

## DAG

```text
mangadex_data_pipeline
```

Task order:

```text
crawl_mangadex_raw
  -> raw_to_bronze
  -> bronze_to_silver
  -> load_silver_to_postgres
  -> dbt_build
  -> validate_gold_tables
```

Default params:

```text
limit: 10
pages: 1
start_offset: 0
pause_seconds: 0.5
translated_language: en
```

These defaults are intentionally small. They make a live demo faster and reduce the chance of triggering MangaDex rate or network problems.

Use `start_offset` to fetch a different MangaDex page on a manual run. For example, with `limit=10`, use `start_offset=30` to start from the fourth page.

## Responsibilities By Layer

Airflow:

- Runs tasks in the right order.
- Captures `crawl_run_id`.
- Makes failure visible.
- Provides logs and manual retry.

Python scripts:

- Crawl MangaDex Raw data.
- Parse Raw into Bronze.
- Transform Bronze into Silver.
- Load Silver into PostgreSQL.

dbt:

- Builds staging views.
- Builds Gold marts.
- Runs dbt tests.

manga-service and web:

- Read from Gold only.
- Do not crawl.
- Do not transform Raw/Bronze/Silver.

## Docker Compose

Services:

```text
airflow-init
airflow-webserver
airflow-scheduler
postgres
```

The Airflow image installs:

```text
psycopg[binary]
dbt-core
dbt-postgres
```

The repo is mounted inside Airflow at:

```text
/opt/airflow/project
```

That lets the DAG call the same scripts used locally.

## Run

Initialize Airflow:

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

Login:

```text
admin / admin
```

Trigger:

```text
mangadex_data_pipeline
```

## Validation

The final task queries PostgreSQL and requires these Gold tables to have rows:

```text
gold.gold_manga_catalog > 0
gold.gold_manga_detail > 0
gold.gold_chapter_list > 0
gold.gold_latest_chapters > 0
```

If MangaDex is blocked, the crawler task fails. If transformations or dbt break, the matching task fails. If Gold is empty, `validate_gold_tables` fails. This is useful for demo because the pipeline exposes where the problem is.

## Test Plan

Static check:

```powershell
python -m py_compile services/airflow/dags/mangadex_pipeline.py
```

Compose config check:

```powershell
docker compose config --services
```

Airflow smoke:

```powershell
docker compose up airflow-init
docker compose up -d postgres airflow-webserver airflow-scheduler
```

Post-run API smoke:

```powershell
curl "http://localhost:8000/manga?limit=10"
curl "http://localhost:8000/chapters/latest?limit=10"
```
