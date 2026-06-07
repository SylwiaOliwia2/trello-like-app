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

## Run in CI

Workflows under `.github/workflows/` run on PRs to `dev` / `stage` / `main`.

Each run produces:

- **Allure results** are available at `https://sylwiaoliwia2.github.io/trello-like-app/<stage>/#`

## Tests

Tests to run before merge to branch:

- `make test-dev`
- `make test-stage`
- `make test-main`

Other

- `make test-api` - API only
- `make test-e2e` - E2E only

## Development

### Run a single test

Tests run inside the `test` profile containers. Override the pytest command to target one file, class, or test name. Make sure the app is up first (`docker compose up --build -d db api web`).

API:

- Single file: `docker compose --profile test run --rm api-test sh -c "python -m pytest apps/api/tests/test_board.py"`
- Single test: `docker compose --profile test run --rm api-test sh -c "python -m pytest apps/api/tests/test_board.py::test_owner_can_add_member"`
- By name match: `docker compose --profile test run --rm api-test sh -c "python -m pytest apps/api/tests -k add_member"`

E2E:

- Single file: `docker compose --profile test run --rm e2e-test sh -c "python -m pytest e2e/tests/test_board.py"`
- Single test: `docker compose --profile test run --rm e2e-test sh -c "python -m pytest e2e/tests/test_board.py::test_user_sees_all_his_boards_on_the_home_page"`
- By name match: `docker compose --profile test run --rm e2e-test sh -c "python -m pytest e2e/tests -k sees_all_his_boards"`

### Pre-commit hook (auto-format)

One-time setup:

- `python3 -m pip install --user pre-commit`
- if `pre-commit` command is not found, add local Python bin to PATH:
  - `export PATH="$HOME/.local/bin:$PATH"`
- `pre-commit install`

On every `git commit` auto-formats Python (ruff) + JS/Vue/JSON/MD (prettier).
Run on all files manually: `pre-commit run --all-files`.

### Query the database locally

Postgres runs in the `db` service (`app` / `app`).

- **Shell inside the DB container** (no local `psql` install needed):
  - App DB: `docker compose exec db psql -U app -d appdb`
  - Test DB (exists after the first `api-test` run): `docker compose exec db psql -U app -d appdb_test`
- **From your machine** (if `psql` is installed): `PGPASSWORD=app psql -h 127.0.0.1 -p 5432 -U app -d appdb`

Use `\dt` for tables, `\q` to quit.
