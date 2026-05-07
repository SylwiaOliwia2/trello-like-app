import pytest


@pytest.fixture()
def no_mfa_payload() -> dict[str, object]:
    return {
        "email": "no_mfa.user@example.com",
        "password": "StrongPass123!",
        "mfa_enabled": False,
    }


@pytest.fixture()
def mfa_payload() -> dict[str, object]:
    return {
        "email": "mfa.user@example.com",
        "password": "StrongPass123!",
        "mfa_enabled": True,
    }
