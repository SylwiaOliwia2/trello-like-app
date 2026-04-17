import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.tests.helpers.login_helpers import get_user_by_email_for_test


@pytest.mark.smoke
def test_register_without_mfa_returns_201(
    client: TestClient,
    db_session: Session,
    no_mfa_payload: dict[str, object],
) -> None:
    response = client.post("/auth/register", json=no_mfa_payload)

    assert response.status_code == 201
    body = response.json()

    assert body["email"] == "no_mfa.user@example.com"
    assert body["mfa_enabled"] is False
    assert body["mfa_otpauth_url"] is None

    db_session.expire_all()
    user = get_user_by_email_for_test(db_session, "no_mfa.user@example.com")
    assert user is not None
    assert user.email == "no_mfa.user@example.com"
    assert user.mfa_enabled is False


@pytest.mark.smoke
def test_register_with_mfa_returns_otpauth_url(
    client: TestClient,
    db_session: Session,
    mfa_payload: dict[str, object],
) -> None:
    response = client.post("/auth/register", json=mfa_payload)

    assert response.status_code == 201
    body = response.json()

    # API RESPONSE CHECKS
    # assert body["email"] == "mfa.user@example.com"
    assert body["mfa_enabled"] is True
    # assert body["mfa_otpauth_url"] is not None
    assert body["mfa_otpauth_url"].startswith("otpauth://totp/")

    # DATABASE CHECKS - user not registered yet
    user = get_user_by_email_for_test("mfa.user@example.com")
    assert user is None

    # TODO: here the MFA confirmation should take place 
