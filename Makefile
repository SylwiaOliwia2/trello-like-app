DC := docker compose

REPORTS_DIR := reports
JUNIT_DIR := $(REPORTS_DIR)/junit
ALLURE_DIR := $(REPORTS_DIR)/allure-results

API_REPORT_FLAGS := --junitxml=$(JUNIT_DIR)/api.xml --alluredir=$(ALLURE_DIR)
E2E_REPORT_FLAGS := --junitxml=$(JUNIT_DIR)/e2e.xml --alluredir=$(ALLURE_DIR)

API_PYTEST := python -m pytest -q apps/api/tests $(API_REPORT_FLAGS)
E2E_PYTEST := python -m pytest -q e2e/tests $(E2E_REPORT_FLAGS)

E2E_DATABASE_URL := postgresql+psycopg2://app:app@db:5432/appdb_test_e2e

.PHONY: wait-api wait-db ensure-e2e-db up-e2e-stack reports-dir test-dev test-stage test-main test-api test-e2e test-all

reports-dir:
	@mkdir -p $(JUNIT_DIR) $(ALLURE_DIR)

wait-db:
	@echo "Waiting for Postgres..."
	@for i in $$(seq 1 30); do \
		$(DC) exec -T db pg_isready -U app >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	echo "Postgres did not become ready in time"; \
	exit 1

ensure-e2e-db: wait-db
	@echo "Ensuring database appdb_test_e2e exists..."
	@for i in $$(seq 1 30); do \
		if $(DC) exec -T db psql -U app -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='appdb_test_e2e'" 2>/dev/null | grep -q 1; then \
			exit 0; \
		fi; \
		if $(DC) exec -T db psql -U app -d postgres -c "CREATE DATABASE appdb_test_e2e" >/dev/null 2>&1; then \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Failed to create appdb_test_e2e"; \
	exit 1

up-e2e-stack: ensure-e2e-db
	$(DC) up --build -d --force-recreate api web

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
	$(DC) down
	$(DC) up --build -d db api
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST) -m 'smoke and not e2e'"

# stage
test-stage: export API_DATABASE_URL := $(E2E_DATABASE_URL)
test-stage: reports-dir
	$(DC) down
	$(DC) up --build -d db
	$(MAKE) up-e2e-stack
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST)"
	$(DC) --profile test run --build --rm e2e-test sh -c "$(E2E_PYTEST)"

# main
test-main: export API_DATABASE_URL := $(E2E_DATABASE_URL)
test-main: reports-dir
	$(DC) down
	$(DC) up --build -d db
	$(MAKE) up-e2e-stack
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST) -m 'smoke or security'"
	$(DC) --profile test run --build --rm e2e-test sh -c "$(E2E_PYTEST) -m 'smoke or security'"

test-api: reports-dir
	$(DC) down
	$(DC) up --build -d db api
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm api-test sh -c "$(API_PYTEST)"

test-e2e: export API_DATABASE_URL := $(E2E_DATABASE_URL)
test-e2e: reports-dir
	$(DC) down
	$(DC) up --build -d db
	$(MAKE) up-e2e-stack
	$(MAKE) wait-api
	$(DC) --profile test run --build --rm e2e-test sh -c "$(E2E_PYTEST)"

test-all: test-stage
