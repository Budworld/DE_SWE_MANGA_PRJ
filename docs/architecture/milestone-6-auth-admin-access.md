# Milestone 6: Local Auth & Admin Access Control

Milestone 6 protects the local admin dashboard with demo authentication.

```text
Env demo users -> signed bearer token -> admin API guard -> protected admin UI
```

## Goals

- Add a login flow for local demos.
- Protect `/admin` in the web app.
- Protect `/admin/*` endpoints in `manga-service`.
- Keep catalog, latest, detail, and reader endpoints public.
- Avoid production identity complexity until the auth-service milestone.

## Components

Auth API:

```text
POST /auth/login
GET /auth/me
```

Protected Admin API:

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
/login
/admin
```

## Local Users

Default local accounts:

```text
admin / admin   role: admin
reader / reader role: user
```

Override them with:

```text
AUTH_DEMO_ADMIN_USERNAME
AUTH_DEMO_ADMIN_PASSWORD
AUTH_DEMO_USER_USERNAME
AUTH_DEMO_USER_PASSWORD
AUTH_TOKEN_SECRET
AUTH_TOKEN_TTL_SECONDS
```

## Notes

- This milestone is local/demo auth only.
- Tokens are signed bearer tokens and stored in browser `localStorage`.
- `admin` role can access admin API and admin UI.
- `user` role can authenticate but receives `403` from admin API.
- Registration, password reset, refresh tokens, database users, OAuth, and api-gateway auth are deferred.

## Run

```powershell
docker compose up -d postgres airflow-webserver airflow-scheduler manga-service
cd apps/web
npm run dev
```

Open:

```text
http://localhost:5173/login
```

## Smoke

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/login -ContentType "application/json" -Body '{"username":"admin","password":"admin"}'
Invoke-RestMethod -Uri http://localhost:8000/auth/me -Headers @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri http://localhost:8000/admin/pipeline/summary -Headers @{ Authorization = "Bearer $($login.access_token)" }
```
