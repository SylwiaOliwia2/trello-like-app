import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.tests.helpers.login_helpers import get_user_by_email_for_test
from apps.api.tests.helpers.login_helpers import _totp_secret_from_otpauth_url


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
@pytest.mark.skip(reason="Bug to be resolved")
def test_register_with_mfa_returns_otpauth_url(
    client: TestClient,
    db_session: Session,
    mfa_payload: dict[str, object],
) -> None:
    """
    Requires `POST /auth/register/mfa/confirm` (not implemented yet) to finalize registration.
    """
    response = client.post("/auth/register", json=mfa_payload)

    assert response.status_code == 201
    body = response.json()

    assert body["email"] == mfa_payload["email"]
    assert body["mfa_enabled"] is True
    assert body["mfa_otpauth_url"].startswith("otpauth://totp/")

    db_session.expire_all()

    # User is not registered yet
    assert get_user_by_email_for_test(db_session, str(mfa_payload["email"])) is None

    # User scanned the QR / entered the secret in an authenticator app — first valid OTP.
    secret = _totp_secret_from_otpauth_url(body["mfa_otpauth_url"])
    otp = pyotp.TOTP(secret).now()

    confirm = client.post(
        "/auth/register/mfa/confirm",
        json={
            "email": mfa_payload["email"],
            "password": mfa_payload["password"],
            "otp": otp,
        },
    )
    assert confirm.status_code == 201

    db_session.expire_all()
    
    # User is registered after MFA confirmation
    user = get_user_by_email_for_test(db_session, str(mfa_payload["email"]))
    assert user is not None
    assert user.email == mfa_payload["email"]
    assert user.mfa_enabled is True
