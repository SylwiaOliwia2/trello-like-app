# Tech stack and deployment


## Stack

| Layer | Choice |
|--------|--------|
| **Frontend** | Vue 3 + Vite |
| **Backend** | Postgres of SQLite, needed some tool for DB  versions management (ex. Django, alembic) |
| **API** | DRF or FastAPI |
| **CI / CD** | GitHub Actions |
| **Auth** | JWT (or session); MFA |

No AWS stack, as AWS is more setup-demanding, but similar in testing. This app is focused on testing.

---

## Repository: one repo for tests and app

**Single repo** with clear folders, e.g. `apps/web`, `apps/api`, `tests/e2e` (or `packages/…` if you prefer). one Actions workflow; Each service (frontend, db, API, E2E tests) should have their own container. The app is being deployed using `docker compose`.

Separate repo for tests would be beneficial in real-life projects. It would be an overkill for testing-demo app (devops-demanding).

---

## Tests

- **Unit / API tests (fast):**
- **E2E (Playwright/Cypress):** use either:
  - **Official Playwright/Cypress Docker image** as the job container
---

## Branches: `dev`, `stage`, `prod`

---

## Deployment

No deployment, as this app focus on tests. Runtests in CI against emepheral app (run in CI from `docker compose`).

---

## Test strategy

| Branch| When and what to run |
|-----------|-------------|
| `dev` | **Smoke tests** except Smoke E2E tests. Run on **every PR** - fast tests of crucial parts (API, optionally security). The build should + tests should take up to 10 - 15 min. Focus on integration: frontend, backend and db comunicate with each other. |
| `stage` | Full regression + full E2E + security + performance (if they exists). Run on **every PR**. |
| `main` |  **Smoke tests** for API, integration and E2E (happy paths). Security. Run on **every PR**. |

Frequently changing code - test early (dev / stage).
Stable code - later test.

---

## Legacy thoughts

### Repository
I thought about Github + actions for CI / CD

### CI / CD
The app needs CI to run the tests and CD for deployment.

### Tests
Don't generate any code or setup for tests. However I need to define upfront about the test environment (tests in a separate container / separate app?). 

### Frontend
My idea is S3 → host static files (Vue build) + CloudFront. It needs to be deployed by CD. Let me know if you have any idea how to make it cheaper.

### Backend
Something as cheap as possible. My ideas:
- DynamoDB + Lambda → almost free at low usage. Cheaper that RDS
- Railway (Postgres) or similar apps - I've never been using it

### API
I want the API to be publicly available after login (so that I can test the API). My ideas:
- Lambda + API Gateway
- Railway

Compare costs and architecture (SQL vs NoSQL) of AWS vs Railway solution.
