# dbt Project

dbt transforms PostgreSQL `silver` JSONB landing tables into `gold` API-ready marts.

## Install

```powershell
pip install -r services/dbt/requirements.txt
```

## Profile

Copy the example profile into your dbt profiles directory or set `DBT_PROFILES_DIR` to `services/dbt`.

```powershell
$env:DBT_PROFILES_DIR="services/dbt"
```

## Run

```powershell
dbt debug --project-dir services/dbt
dbt build --project-dir services/dbt
```

The default connection matches the local `docker-compose.yml` PostgreSQL service:

```text
host: localhost
port: 5432
database: web_manga
user: web_manga
password: web_manga
```

## Supabase Target

Milestone 7 adds a Supabase target for Airflow-driven ETL.

Create `.env.supabase` from the template and set the real password:

```powershell
Copy-Item .env.supabase.example .env.supabase
```

For local dbt debugging, load the same values into your shell and run:

```powershell
$env:DBT_TARGET="supabase"
dbt debug --project-dir services/dbt --profiles-dir services/dbt
dbt build --project-dir services/dbt --profiles-dir services/dbt
```

Airflow passes these env vars automatically when started with:

```powershell
docker compose --env-file .env.supabase up -d airflow-webserver airflow-scheduler
```
