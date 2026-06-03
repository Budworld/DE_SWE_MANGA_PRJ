# Web App

React/Vite manga preview app that reads from `manga-service`.

## Data Flow

```text
Gold tables -> manga-service API -> web UI
```

Images:

- Covers use `cover_url` built by the API from MangaDex `source_manga_id + cover_file_name`.
- Reader pages use live MangaDex at-home image metadata via `GET /chapters/{source_chapter_id}/pages`.

## Install

```powershell
cd apps/web
npm install
```

## Run

Start the API first:

```powershell
docker compose up -d postgres
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn app.main:app --app-dir services/manga-service --host 0.0.0.0 --port 8000
```

Then run the web app:

```powershell
cd apps/web
npm run dev
```

Optional API URL:

```powershell
$env:VITE_MANGA_API_URL="http://localhost:8000"
```

## Build

```powershell
cd apps/web
npm run build
```

## Notes

If MangaDex at-home is blocked by the current network/proxy, the reader page shows an error state. Catalog, detail, and latest views still use cover images from `cover_url`.
