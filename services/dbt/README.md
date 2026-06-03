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
