---
name: CI/CD and Railway setup
overview: Define a monorepo layout, Railway projects/services for dev/stage/prod, and GitHub Actions + Environments so you can implement Phase 1 and deploy with migrations, matching [notes/TECH_STACK.md](notes/TECH_STACK.md) and [notes/features_development.plan.md](notes/features_development.plan.md).
todos:
  - id: scaffold-monorepo
    content: Add pnpm workspace, apps/web + apps/api skeleton, root scripts, docker-compose Postgres
    status: pending
  - id: railway-project-envs
    content: Create Railway project with dev/stage/prod envs; Postgres + API + static web per env; env vars and URLs documented
    status: pending
  - id: gha-ci
    content: "Add .github/workflows/ci.yml: lint, unit/API tests, build on PR and main branches"
    status: pending
  - id: gha-deploy
    content: Add deploy workflows for dev/stage/main + Railway token/secrets; migrations on deploy
    status: pending
  - id: gha-e2e-smoke
    content: Add stage E2E job + prod smoke; stage seed data script when e2e package exists
    status: pending
  - id: github-settings
    content: Configure GitHub Environments, branch protection, concurrency groups
    status: pending
isProject: false
---

## 1. Repository structure (before or as part of Phase 1)

Create a minimal app:

- `apps/web` — Vue 3 + Vite (build → static assets).
- `apps/api` — HTTP API + migration runner (use alembic or Django). Use Python.
- database
- `tests/e2e` — Playwright (or Cypress) added when you wire stage E2E. Use JavaScript. 
- `docker-compose.yml`

The app should have `/health` endpoint and a minimal "Hello World" frontend.


## 2. GitHub Actions workflows (concrete split)

Define one CI workflow triggered by `pull_request` to `dev|stage|main` and by `push` to those branches, then gate test depth by branch:
- on `dev` run fast checks only (`lint`, type-check, unit tests) for quick feedback; or even less - **TO BE DEFINED** 
- on `stage` run everything from `dev` plus API/integration tests and a full E2E suite against stage services;
- on `main` run **smoke tests only** (or everything from `stage` plus a short post-deploy smoke E2E pack against production-critical paths.)

---