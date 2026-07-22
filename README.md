# Pytest automation for a Trello-like app

This repo’s main purpose is **QA**: API tests (pytest), E2E UI tests (Playwright), CI, reporting, and issue tracking.

The Trello-like app (Vue + FastAPI, WIP) exists only as a **product under test** — effort went into the tests, not app polish. Due to that the app code was AI-assisted (Cursor).

---

## QA artifacts

| Artifact                | Link                                                                                                                                                                                                                                                                                            |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Found issues            | [GitHub Issues](https://github.com/SylwiaOliwia2/trello-like-app/issues)                                                                                                                                                                                                                        |
| CI workflows            | [GitHub Actions](https://github.com/SylwiaOliwia2/trello-like-app/actions)                                                                                                                                                                                                                      |
| Allure reports          | [dev](https://sylwiaoliwia2.github.io/trello-like-app/dev/) · [stage](https://sylwiaoliwia2.github.io/trello-like-app/stage/) · [main](https://sylwiaoliwia2.github.io/trello-like-app/main/)                                                                                                   |
| E2E failure screenshots | CI artifacts on PRs to **stage** / **main** (`e2e-screenshots-*`). Not uploaded on PRs to **dev**. Example: [run 26209428356](https://github.com/SylwiaOliwia2/trello-like-app/actions/runs/26209428356) — upload step ran, but **no screenshots** were produced (due to no Playwright errors). |

---

## Notes

Docs under [`notes/`](notes/) explain the thinking behind the project:

| File                                                 | What you’ll find                                        |
| ---------------------------------------------------- | ------------------------------------------------------- |
| [TEST_STRATEGY.md](notes/TEST_STRATEGY.md)           | Test levels, scope, and prioritization for this app     |
| [ITERATIONS.md](notes/ITERATIONS.md)                 | Phased feature plan and acceptance criteria             |
| [TECH_STACK.md](notes/TECH_STACK.md)                 | Stack choices and why (app + CI focused on testability) |
| [TECHNICAL_COMMANDS.md](notes/TECHNICAL_COMMANDS.md) | How to run the app and tests locally / in CI            |

---

## Development

See [notes/TECHNICAL_COMMANDS.md](notes/TECHNICAL_COMMANDS.md) for Docker, `make` targets, single-test commands, and DB access.
