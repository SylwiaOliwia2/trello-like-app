DC := docker compose

REPORTS_DIR := reports
JUNIT_DIR := $(REPORTS_DIR)/junit
ALLURE_DIR := $(REPORTS_DIR)/allure-results

API_REPORT_FLAGS := --junitxml=$(JUNIT_DIR)/api.xml --alluredir=$(ALLURE_DIR)
E2E_REPORT_FLAGS := --junitxml=$(JUNIT_DIR)/e2e.xml --alluredir=$(ALLURE_DIR)

API_PYTEST := python -m pytest -q apps/api/tests $(API_REPORT_FLAGS)
E2E_PYTEST := python -m pytest -q e2e/tests $(E2E_REPORT_FLAGS)

.PHONY: wait-api reports-dir test-dev test-stage test-main test-api test-e2e test-all

reports-dir:
	@mkdir -p $(JUNIT_DIR) $(ALLURE_DIR)

wait-api:
	@echo "Waiting for API on http://127.0.0.1:8000/health..."
	@for i in $$(seq 1 30); do \
		curl -fsS http://127.0.0.1:8000/health >/dev/null && exit 0; \
		sleep 1; \
	done; \
	echo "API did not become ready in time"; \
	exit 1

# dev
test-dev: reports-dir
	$(DC) down -v
	$(DC) up --build -d db api
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST) -m 'smoke and not e2e'"

# stage
test-stage: reports-dir
	$(DC) down -v
	$(DC) up --build -d db api web
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST)"
	$(DC) --profile test run --build --rm e2e-test sh -c "$(E2E_PYTEST)"

# main
test-main: reports-dir
	$(DC) down -v
	$(DC) up --build -d db api web
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST) -m 'smoke or security'"
	$(DC) --profile test run --build --rm e2e-test sh -c "$(E2E_PYTEST) -m 'smoke or security'"

test-api: reports-dir
	$(DC) down -v
	$(DC) up --build -d db api
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST)"

test-e2e: reports-dir
	$(DC) down -v
	$(DC) up --build -d db api web
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm e2e-test sh -c "$(E2E_PYTEST)"

test-all: test-stage
