# Milestone 2: Manga Catalog API

Milestone 2 turns the data foundation from Milestone 1 into a usable read API. The service exposes dbt Gold tables through FastAPI so the future web app can read manga catalog, manga detail, chapter lists, and latest chapters without knowing the DE pipeline internals.

## Goal

Build a read-only Manga API over PostgreSQL `gold` tables.

```text
MangaDex API
  -> Raw
  -> Bronze
  -> Silver
  -> PostgreSQL silver
  -> dbt Gold
  -> manga-service API
  -> future web app
```

Success criteria:

- API starts locally.
- API reads from `gold`, not Raw/Bronze/Silver.
- Unit tests pass.
- dbt Gold build still passes.
- Docker service can start and answer `/health`.

## Scope

In scope:

- `services/manga-service` FastAPI app.
- Read-only SQL queries over `gold` schema.
- Pydantic response contracts.
- Local and Docker run commands.
- Minimal route tests.

Out of scope:

- Authentication.
- Web frontend.
- Write APIs.
- Manga image/page serving.
- AI translation.
- Airflow, Spark, Kafka.

## Service Design

```text
app/main.py
  creates FastAPI app

app/routes.py
  HTTP endpoints and request validation

app/repositories.py
  SQL queries against PostgreSQL gold tables

app/schemas.py
  Pydantic response models

app/db.py
  PostgreSQL connection dependency

app/config.py
  environment-based settings
```

The service is intentionally thin. dbt owns product-shaped read models, while the API owns HTTP contracts and request filtering.

## Data Source

The service reads only these tables:

```text
gold.gold_manga_catalog
gold.gold_manga_detail
gold.gold_chapter_list
gold.gold_latest_chapters
```

Why Gold only:

- Gold is API-ready and denormalized for product use cases.
- Silver remains a normalized domain layer for data modeling.
- Raw and Bronze are lineage/replay layers, not API surfaces.
- Keeping API reads on Gold avoids scattering joins across app code.

## API Contract

Endpoints:

```text
GET /health
GET /manga
GET /manga/{manga_id}
GET /manga/{manga_id}/chapters
GET /chapters/latest
```

Pagination shape:

```json
{
  "items": [],
  "limit": 20,
  "offset": 0,
  "count": 0
}
```

Query parameters:

```text
GET /manga
  q
  status
  original_language
  limit: 1..100
  offset: >= 0

GET /manga/{manga_id}/chapters
  translated_language
  limit: 1..200
  offset: >= 0

GET /chapters/latest
  translated_language
  limit: 1..100
  offset: >= 0
```

Missing manga detail returns:

```text
404 Manga not found
```

## Build And Run

Install service dependencies:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r services/manga-service/requirements.txt
```

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Ensure Gold tables are built:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
```

Start API locally:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn app.main:app --app-dir services/manga-service --host 0.0.0.0 --port 8000
```

Start API with Docker:

```powershell
docker compose up --build manga-service
```

## Test Strategy

Unit tests:

- Use FastAPI `TestClient`.
- Override repository dependency.
- Do not require PostgreSQL.
- Verify route contracts, pagination shape, 404 behavior, and request validation.

Run:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest services/manga-service/tests
```

Data integration verification:

```powershell
docker compose up -d postgres
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
```

Smoke API with real database:

```powershell
curl http://localhost:8000/health
curl "http://localhost:8000/manga?limit=10&offset=0"
curl "http://localhost:8000/chapters/latest?limit=10"
```

Expected current verification:

```text
pytest: 7 passed
dbt build: PASS=34 WARN=0 ERROR=0
GET /health: 200
GET /manga?limit=2: 200, count=10
GET /chapters/latest?limit=2: 200, count=10
Docker /health: 200
```

## Development Notes

Environment:

```text
DATABASE_URL=postgresql://web_manga:web_manga@localhost:5432/web_manga
```

Docker uses:

```text
DATABASE_URL=postgresql://web_manga:web_manga@postgres:5432/web_manga
```

If API queries fail with missing `gold` tables, run the Milestone 1 load flow and `dbt build` again.

## Next Milestone

After Milestone 2, the natural next step is Airflow orchestration:

```text
crawl raw
  -> raw to bronze
  -> bronze to silver
  -> load silver to PostgreSQL
  -> dbt build
  -> validate gold
```

Airflow should call existing scripts instead of rewriting transformation logic.
