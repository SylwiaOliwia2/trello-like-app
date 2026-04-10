# Tech stack and deployment (decision log)


## Stack

| Layer | Choice | Notes |
|--------|--------|--------|
| **Frontend** | Vue 3 + Vite | **Deploy:** Railway static first; optional later: fork and add **S3 + CloudFront** (same app; staying on one provider is simplest). |
| **Backend** | Railway API from this repo | **Postgres** (plugin). Per env: separate DBs or **three Railway projects** (dev / stage / prod) for a simple demo. |
| **CI / CD** | GitHub Actions | Build → **Railway CLI or API** deploy; **run DB migrations** on deploy. |
| **Auth** | JWT (or session); MFA later | Document API base URL + auth in README. |

No AWS stack, as AWS is more setup-demanding, but similar in testing. In this app we focus on testing.

---

## Repository: one repo for tests and app

**Single repo (monorepo)** with clear folders, e.g. `apps/web`, `apps/api`, `tests/e2e` (or `packages/…` if you prefer).  One PR shows app + test changes; one Actions workflow; easy local `docker compose` for “app + DB”; matches “portfolio shows I own the full system.” Slightly more path discipline in workflows.

Separate repo for tests would be beneficial in real-life projects. It would be an overkill for testing-demo app (devops-demanding).

---

## Tests

- **Unit / API tests (fast):** use `ubuntu-latest` or default backend container. Runner with `pnpm/npm test` — no extra container required.
- **E2E (Playwright/Cypress):** use either:
  - **Official Playwright/Cypress Docker image** as the job container, or  
  - **Service containers** in Actions for Postgres if the API runs in-process against a real DB in CI.

---

## Branches: `dev`, `stage`, `prod`

**Recommendation (simple, common):**

| Branch | Role | Deploy target |
|--------|------|----------------|
| **`main`** | Production-ready code | **prod** environment (manual or tagged release). |
| **`dev`** | Integration line | **dev** environment (auto on push). |
| **`stage`** | Pre-release QA | **stage** environment (auto or manual). |

You can also use **environment protection** on GitHub (required reviewers for `prod`) instead of relying only on branch names.

---

## Run tests on every branch or only on `stage`?

| Test type | When to run |
|-----------|-------------|
| **Lint, unit, API contract** | **Every PR** (and often on push to `main` / `develop`). Fast feedback. |
| **Full E2E against a deployed URL** | **`stage` (and optionally `main` after deploy)** — E2E needs a **stable, known URL** and seeded data. Running full E2E on every feature branch is possible if each PR gets a **preview environment** (more setup/cost). |
| **E2E against ephemeral stack in CI** | **Every PR** if you **docker compose up** app + DB in the workflow (no cloud deploy). Good for portfolio; you pay with longer CI minutes. |

**Practical default for a cheap demo:**  
- PR: **fast tests** (Lint, unit, API contract).  
- **`stage`:** **deploy + E2E against stage URL**.  
- **`prod`:** **smoke** or subset after deploy.

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
