from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.environ.get("E2E_API_URL", "http://127.0.0.1:8000").rstrip("/")
