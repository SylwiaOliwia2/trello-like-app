DC := docker compose

API_PYTEST := python -m pytest -q apps/api/tests
E2E_PYTEST := python -m pytest -q e2e/tests

.PHONY: wait-api test-dev test-stage test-main test-api test-e2e test-all

wait-api:
	@echo "Waiting for API on http://127.0.0.1:8000/health..."
	@for i in $$(seq 1 30); do \
		curl -fsS http://127.0.0.1:8000/health >/dev/null && exit 0; \
		sleep 1; \
	done; \
	echo "API did not become ready in time"; \
	exit 1

# dev
test-dev:
	$(DC) down -v
	$(DC) up --build -d db api
	$(MAKE) wait-api
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST) -m 'smoke and not e2e'"

# stage
test-stage:
	$(DC) down -v
	$(DC) up --build -d db api web
	$(MAKE) wait-api
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST)"
	$(DC) --profile test run --rm e2e-test sh -c "$(E2E_PYTEST)"

# main
test-main:
	$(DC) down -v
	$(DC) up --build -d db api web
	$(MAKE) wait-api
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST) -m 'smoke or security'"
	$(DC) --profile test run --rm e2e-test sh -c "$(E2E_PYTEST) -m 'smoke or security'"

test-api:
	$(DC) down -v
	$(DC) up --build -d db api
	$(MAKE) wait-api
	$(DC) --profile test run --rm api-test sh -c "$(API_PYTEST)"

test-e2e:
	$(DC) down -v
	$(DC) up --build -d db api web
	$(MAKE) wait-api
	$(DC) --profile test run --rm e2e-test sh -c "$(E2E_PYTEST)"

test-all: test-stage
