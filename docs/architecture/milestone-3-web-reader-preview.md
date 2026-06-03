# Milestone 3: Web Reader Preview With Real Images

Milestone 3 adds a browser UI that reads manga catalog data from `manga-service` and displays real MangaDex images.

## Goal

Show a usable manga browsing experience:

```text
Gold tables -> manga-service API -> React web UI
                           |
                           -> MangaDex cover CDN
                           -> MangaDex at-home page image metadata
```

## Image Strategy

Cover images:

```text
https://uploads.mangadex.org/covers/{source_manga_id}/{cover_file_name}
```

Chapter page images:

```text
GET /chapters/{source_chapter_id}/pages?quality=data_saver
GET /chapters/{source_chapter_id}/pages?quality=full
```

The API fetches MangaDex at-home metadata live and returns image URLs. It does not download image binaries or persist page metadata yet.

## Web Views

```text
/catalog
/manga/:manga_id
/latest
/chapters/:source_chapter_id/read
```

Behavior:

- Catalog shows cover images, search, status filter, original language filter.
- Manga detail shows a large cover, metadata, tags, description, and chapter list.
- Latest shows latest chapters with cover thumbnails.
- Reader displays vertical manga pages and supports `data_saver/full` quality toggle.

## Build And Run

Start backend:

```powershell
docker compose up -d postgres
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\dbt.exe" build --project-dir services/dbt --profiles-dir services/dbt
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn app.main:app --app-dir services/manga-service --host 0.0.0.0 --port 8000
```

Start frontend:

```powershell
cd apps/web
npm install
npm run dev
```

Build frontend:

```powershell
cd apps/web
npm run build
```

## Verification

API:

```text
GET /manga includes cover_url
GET /manga/{manga_id} includes cover_url
GET /chapters/{source_chapter_id}/pages returns image URLs
invalid quality returns 422
```

Current local verification:

```text
pytest services/manga-service/tests: 9 passed
npm run build in apps/web: passed
dbt build: PASS=34 WARN=0 ERROR=0
GET /manga includes a real cover_url
```

Network note:

```text
MangaDex at-home may return 502 if the current network/proxy blocks api.mangadex.org/at-home.
The web reader handles this with an error state.
```

Frontend:

- Catalog loads with covers.
- Detail page loads cover and chapters.
- Latest page loads latest chapters.
- Reader loads page images.
- Broken image/network failure has fallback or error state.

## Later DE Work

The live at-home lookup is intentional for UI preview. A later DE milestone should ingest `at_home` metadata into Raw/Bronze/Silver and optionally cache image metadata.
