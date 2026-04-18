## 1. Repository structure (before or as part of Phase 1)

Create a minimal app:

- `apps/web` — Vue 3 + Vite (build → static assets).
- `apps/api` — HTTP API + migration runner (use alembic or Django). Use Python.
- database
- `tests/e2e` — Playwright (or Cypress) added when you wire stage E2E. Use Python. 
- `docker-compose.yml`

The app should have a `/health` endpoint and a minimal "Hello World" frontend.

---

## 2. GitHub Actions workflows (concrete split)

Define one CI workflow triggered by `pull_request` to `dev|stage|main` and by `push` to those branches, then gate test depth by branch:
- on `dev` smoke tests for API (integration?)  
- on `stage` run a full E2E and API suite (smoke, regression) against stage services;
- on `main` run **smoke tests only** against production-critical paths. Security. Run on every commit.

---