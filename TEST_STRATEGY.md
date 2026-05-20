# Test Strategy

## Purpose

This document defines a practical test strategy for this app. The goal is to show a realistic QA approach that is clear, lightweight, and suitable for a small full-stack project.

## Notes

This is a demo project, so the strategy is intentionally concise. The focus is on showing good QA judgment, practical prioritization, and a maintainable level of test coverage rather than enterprise-scale process.

## Scope

The strategy covers:

- API testing
- End-to-end testing
- Basic integration between frontend, backend, and database
- Selected non-functional checks such as security and accessibility

## Testing Lifecycle

Testing is iterative and done feature by feature. Each feature enters testing after implementation is finished, then is covered by the most appropriate level of tests.

## Repository

### Structure

- API tests are located in `apps/api/tests/`
- E2E tests are located in `e2e/tests/`
- E2E tests should follow the Page Object Model (POM)

### Test Technologies

- `Pytest` for API tests
- `Playwright` for E2E tests
- `Docker Compose` for local and CI test environments

## Test Levels

- API tests verify backend endpoints, response codes, and business logic
- Integration checks verify that frontend, backend, and database work together correctly
- E2E tests verify critical user flows from the user perspective
- Manual testing supports exploratory checks, UI review, and accessibility review

## Automated vs Manual Testing

Manual testing is used for:

- exploratory testing of new features before automation
- UX checks such as layout and alignment
- accessibility review

Automated testing is used for:

- stable and repeatable checks
- critical business flows
- regression coverage for areas with higher product risk

All automated tests should be committed to the `dev` branch first.

## Environments and Branches

The app uses 3 branches: `dev`, `stage`, and `main`.

| Branch  | Test scope                                                                                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dev`   | Fast smoke and integration checks on every PR. Focus on critical paths and basic communication between frontend, backend, and database. Total build and test time should stay within 10-15 minutes. |
| `stage` | Full regression, broader E2E coverage, security or performance checks if available. Run on every PR before release.                                                                                 |
| `main`  | Smoke checks for API, integration, and happy-path E2E flows, plus basic security checks. Run on every commit to the production branch.                                                              |

The CI environment should use `docker compose up`.

## Test database

Both CI and local tests use the same emepheral database. The test dabase uses **one connection** + transactions with savepoints (**rollback after each test**). Althought it doesn't imitate how production database works (multiple sessions, real commits), this approach is enough for this app.

## Prioritization

Testing follows a risk-based approach.

Priority formula:

```
3 x (risk) + 2 x (UX impact) + (frequency of occurrence)
```

This means:

- risk has the highest weight
- user impact (the risk, that the user will not use the app) has medium weight
- frequency of occurrence has the lowest weight

### Test Cases- priorites & traceability:

1. Login & Registration: https://docs.google.com/spreadsheets/d/1J6nITKuYAP6KUIV8YzeCP11Y-t-90ft3ngzVW1SsWuI/edit?usp=sharing

## Exit Criteria

A feature is ready to move to the next stage (`dev` -> `stage` -> `main`) when:

- acceptance criteria are covered
- critical defects are resolved
- relevant automated tests pass in CI
- manual checks do not reveal major UX or accessibility issues

For this demo project, acceptance criteria are based on documented feature goals (not external client sign-off). Each feature should include 3-5 simple criteria in the form: "Given/When/Then" or "User can ...".
