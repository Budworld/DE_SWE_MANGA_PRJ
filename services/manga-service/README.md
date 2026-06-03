# Manga Service

FastAPI service that exposes API-ready manga data from PostgreSQL `gold` tables.

This service is read-only. It does not crawl MangaDex and does not transform Raw/Bronze/Silver data.

Detailed milestone docs:

```text
docs/architecture/milestone-2-manga-api.md
```

## Data Flow

```text
Gold tables -> manga-service API -> future web app
```

Source tables:

```text
gold.gold_manga_catalog
gold.gold_manga_detail
gold.gold_chapter_list
gold.gold_latest_chapters
```

## Install

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r services/manga-service/requirements.txt
```

## Run Locally

Start PostgreSQL and make sure Milestone 1 data has been loaded and dbt Gold has been built.

```powershell
docker compose up -d postgres
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
```

Start API:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn app.main:app --app-dir services/manga-service --host 0.0.0.0 --port 8000
```

## Docker

```powershell
docker compose up manga-service
```

## Endpoints

```text
GET /health
GET /manga
GET /manga/{manga_id}
GET /manga/{manga_id}/chapters
GET /chapters/latest
```

Query examples:

```powershell
curl http://localhost:8000/health
curl "http://localhost:8000/manga?limit=10&offset=0"
curl "http://localhost:8000/manga?status=ongoing&original_language=ja"
curl "http://localhost:8000/chapters/latest?translated_language=en&limit=10"
```

## Tests

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest services/manga-service/tests
```

Expected verification for Milestone 2:

```text
pytest: 7 passed
dbt build: PASS=34 WARN=0 ERROR=0
Docker /health: 200
```
