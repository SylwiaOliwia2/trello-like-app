# Minimal QA Demo App

## Stack
- `apps/web`: Vue 3 + Vite
- `apps/api`: FastAPI (`/health`)
- `docker compose`: local and CI runtime

## Run locally (Docker only)
1. Start app:
   - `docker compose up --build`
2. Open:
   - web: `http://127.0.0.1:5173`
   - api health: `http://127.0.0.1:8000/health`
3. Stop:
   - `docker compose down`

## Run in CI (Docker Compose)
Use the same command in your CI job:
- `docker compose up --build -d`
- `curl -f http://127.0.0.1:8000/health`
- `docker compose down -v`

Tests are intentionally skipped for now.
