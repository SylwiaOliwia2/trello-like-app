"""Database bootstrap and pytest fixtures for `client` and `db_session`."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from apps.api.main import Base, SessionLocal, app, engine


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


@pytest.fixture(autouse=True)
def reset_test_database_tables() -> Generator[None, None, None]:
    """Ensure schema exists and clear data between tests for repeatable runs."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        session.commit()
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
