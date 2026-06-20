# Data Pipeline

Parse, validate, clean, deduplicate, normalize và publish dữ liệu từ `raw` sang `bronze`, `silver`, `gold`.

## MangaDex raw to Bronze

Parse raw MangaDex API responses thành Bronze JSONL records:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/mangadex_raw_to_bronze.py --raw-run-dir "data/raw/mangadex/crawl_run_id=20260602T055219Z-0438e6fd" --overwrite
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

## MangaDex Bronze to Silver

Transform Bronze source-shaped records thành Silver domain records:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/data-pipeline/mangadex_bronze_to_silver.py --bronze-run-dir "data/bronze/mangadex/crawl_run_id=20260602T055219Z-0438e6fd" --overwrite
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

## Load Silver to PostgreSQL

Install loader dependency:

```powershell
pip install -r services/data-pipeline/requirements.txt
```

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Load a Silver run into schema `silver`:

```powershell
python services/data-pipeline/load_silver_to_postgres.py --silver-run-dir "data/silver/mangadex/crawl_run_id=20260602T055219Z-0438e6fd" --overwrite
```

The default database URL is:

```text
postgresql://web_manga:web_manga@localhost:5432/web_manga
```

## Airflow to Supabase

Milestone 7 makes Airflow the normal way to run the complete ETL into Supabase.

Create `.env.supabase` from `.env.supabase.example`, replace the password, then start Airflow:

```powershell
docker compose --env-file .env.supabase up airflow-init
docker compose --env-file .env.supabase up -d postgres airflow-webserver airflow-scheduler manga-service
```

Trigger `mangadex_data_pipeline` in Airflow. The DAG runs:

```text
crawl raw -> bronze -> silver -> load silver to Supabase -> dbt build -> validate gold
```

Manual script commands remain useful for debugging, but they are not required for the normal Supabase workflow.
