# Milestone 7: Airflow ETL to Supabase

Milestone 7 keeps Airflow as the orchestration layer, but moves the application/data warehouse database to Supabase Postgres.

```text
Airflow local
  -> crawl MangaDex Raw
  -> Raw to Bronze
  -> Bronze to Silver
  -> load Silver to Supabase
  -> dbt build staging/gold/monitoring on Supabase
  -> validate Gold
```

## Goals

- Trigger the whole ETL from Airflow instead of running scripts manually.
- Store `silver`, `staging`, `gold`, and `monitoring` in Supabase Postgres.
- Keep Airflow metadata on local Postgres for reliability and separation.
- Let `manga-service` read Supabase through `DATABASE_URL`.
- Keep the existing local Postgres workflow as a fallback.

## Database Roles

Local Postgres:

```text
airflow metadata only
```

Supabase Postgres:

```text
silver      loaded by services/data-pipeline/load_silver_to_postgres.py
staging     built by dbt
gold        built by dbt and read by manga-service
monitoring  built by dbt and read by admin APIs
```

## Supabase Env

Create a local env file from the committed template:

```powershell
Copy-Item .env.supabase.example .env.supabase
```

Then replace the placeholder password in `.env.supabase`.

The default connection mode is Supabase Shared Pooler session mode:

```text
postgresql://postgres.<project-ref>:YOUR_PASSWORD@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require
```

Do not commit `.env.supabase`.

## Run

Initialize Airflow metadata locally:

```powershell
docker compose --env-file .env.supabase up airflow-init
```

Start the local orchestrator and API:

```powershell
docker compose --env-file .env.supabase up -d postgres airflow-webserver airflow-scheduler manga-service
```

Open Airflow:

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

The DAG remains manual by default. The default crawl params are intentionally small for Supabase and MangaDex-friendly demo runs.

## Validate

After the DAG succeeds, Supabase should contain:

```text
silver.*
staging.*
gold.gold_manga_catalog
gold.gold_manga_detail
gold.gold_chapter_list
gold.gold_latest_chapters
monitoring.*
```

Smoke API:

```powershell
curl http://localhost:8000/manga?limit=5
curl http://localhost:8000/chapters/latest?limit=5
```

Admin API:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/login -ContentType "application/json" -Body '{"username":"admin","password":"admin"}'
Invoke-RestMethod -Uri http://localhost:8000/admin/pipeline/summary -Headers @{ Authorization = "Bearer $($login.access_token)" }
```

## Notes

- Airflow metadata remains local because it is operational state, not manga warehouse data.
- `DATABASE_URL` is the single source of truth for the data target.
- `DBT_TARGET=supabase` tells dbt to use the Supabase profile.
- Scripts remain useful for debugging, but the normal workflow is Airflow-triggered ETL.
- Supabase Auth, Storage, deployment, and scheduled production runs are deferred.

## Troubleshooting

- If the DAG cannot connect, verify `.env.supabase` has the real database password.
- If dbt connects locally by mistake, verify `DBT_TARGET=supabase`.
- If SSL fails, verify `DATABASE_URL` includes `sslmode=require` and `POSTGRES_SSLMODE=require`.
- If API reads old local data, rebuild/restart `manga-service` with `docker compose --env-file .env.supabase up -d --build manga-service`.
- If Supabase free tier is paused, resume the project before running Airflow.
