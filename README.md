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
   - api swagger: `http://127.0.0.1:8000/docs`
3. Stop:
   - `docker compose down`


## Run in CI (Docker Compose)
**Note**: CI skipped as for now.

~~Use the same command in your CI job:~~
~~- `docker compose up --build -d`~~
~~- `curl -f http://127.0.0.1:8000/health`~~
~~- `docker compose down -v`~~

## API tests
- Run with Docker Compose:
  - `docker compose --profile test run --rm api-test`
- Detached app + test flow (CI-friendly):
  - `docker compose up --build -d`
  - `docker compose --profile test run --rm api-test`
  - `docker compose down -v`

## Development

### Query the database locally
Postgres runs in the `db` service (`app` / `app`).

- **Shell inside the DB container** (no local `psql` install needed):
  - App DB: `docker compose exec db psql -U app -d appdb`
  - Test DB (exists after the first `api-test` run): `docker compose exec db psql -U app -d appdb_test`
- **From your machine** (if `psql` is installed): `PGPASSWORD=app psql -h 127.0.0.1 -p 5432 -U app -d appdb`

Use `\dt` for tables, `\q` to quit.
