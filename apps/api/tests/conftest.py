import os

# Set up database URL for tests
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://app:app@db:5432/appdb_test",
)

pytest_plugins = [
    "apps.api.tests.fixtures.user_fixtures",
    "apps.api.tests.fixtures.login_fixture",
    "apps.api.tests.helpers.db_fixtures",
]
