# Milestone 5: Data Observability & Admin Dashboard

Milestone 5 adds a read-only monitoring layer for the MangaDex data pipeline.

```text
Airflow DAG -> Raw/Bronze/Silver -> dbt Gold -> monitoring views -> admin API -> admin UI
```

## Goals

- Show pipeline health without writing ad hoc SQL.
- Explain why Silver row counts differ from Gold business counts.
- Surface data quality issues such as missing covers and chapters without matched manga.
- Provide a local dashboard for demoing the DE pipeline.

## Components

dbt monitoring views:

```text
monitoring.pipeline_run_summary
monitoring.gold_table_counts
monitoring.data_quality_checks
```

Admin API:

```text
GET /admin/health
GET /admin/pipeline/runs
GET /admin/pipeline/summary
GET /admin/data-quality
GET /admin/catalog/stats
GET /admin/gold-table-counts
```

Web UI:

```text
/admin
```

## Notes

- The admin dashboard is local-only and read-only.
- Airflow remains the place to trigger pipeline runs.
- pgAdmin remains available for manual database inspection.
- Gold deduplicates manga and chapter business IDs, so it can have fewer rows than Silver.

## Run

```powershell
docker compose up -d postgres airflow-webserver airflow-scheduler manga-service
dbt build --project-dir services/dbt --profiles-dir services/dbt
cd apps/web
npm run dev
```

Open:

```text
http://localhost:5173/admin
```

## Smoke

```powershell
curl http://localhost:8000/admin/pipeline/summary
curl http://localhost:8000/admin/data-quality
curl http://localhost:8000/admin/catalog/stats
```
