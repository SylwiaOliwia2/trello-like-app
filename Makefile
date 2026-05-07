DC := docker compose

API_PYTEST := python -m pytest -q apps/api/tests
E2E_PYTEST := python -m pytest -q e2e/tests

.PHONY: test-dev test-stage test-main test-all

# dev
test-dev:
	$(DC) down -v
	$(DC) up --build -d db api
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST) -m 'smoke and not e2e'"

# stage
test-stage:
	$(DC) down -v
	$(DC) up --build -d db api web
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST)"
	$(DC) --profile test run --rm e2e-test sh -c "$(E2E_PYTEST)"

# main
test-main:
	$(DC) down -v
	$(DC) up --build -d db api web
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST) -m 'smoke or security'"
	$(DC) --profile test run --rm e2e-test sh -c "$(E2E_PYTEST) -m 'smoke or security'"

test-api:
	$(DC) down -v
	$(DC) up --build -d db api
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST)"

test-e2e:
	$(DC) down -v
	$(DC) up --build -d db api web
	$(DC) --profile test run --rm e2e-test sh -c "$(E2E_PYTEST)"

test-all: test-stage
