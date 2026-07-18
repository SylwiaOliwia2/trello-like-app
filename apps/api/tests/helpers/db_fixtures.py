"""Database bootstrap and pytest fixtures for `client` and `db_session`."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from apps.api.main import Base, app, engine, get_db


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database_exists() -> None:
    """Create the Postgres database named in DATABASE_URL if it is missing."""
    url = make_url(os.environ["DATABASE_URL"])
    if not url.database:
        raise RuntimeError("DATABASE_URL must include a database name")

    maintenance = url.set(database="postgres")
    admin_engine = create_engine(maintenance, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def init_database_schema(ensure_test_database_exists: None) -> None:
    # ensure it will never run on production database, only on test database
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session(init_database_schema: None) -> Generator[Session, None, None]:
    connection = engine.connect()
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
