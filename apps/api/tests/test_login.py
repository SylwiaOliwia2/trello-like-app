import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import MfaCode, User
from apps.api.tests.fixtures.user_fixtures import (
    FIXED_MFA_SECRET_FOR_TESTS,
    SEEDED_USER_PASSWORD,
    SEEDED_USER_WITH_MFA_EMAIL,
)
from apps.api.tests.helpers.login_helpers import _login_json


@pytest.mark.smoke
def test_login_without_mfa_returns_access_token(
    client: TestClient,
    registered_user_no_mfa: User,
) -> None:
    response = client.post(
        "/auth/login",
        json=_login_json(registered_user_no_mfa.email, SEEDED_USER_PASSWORD),
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.smoke
def test_login_with_mfa_valid_otp_returns_access_token(
    client: TestClient,
    db_session: Session,
    registered_user_with_mfa: User,
) -> None:
    otp = pyotp.TOTP(FIXED_MFA_SECRET_FOR_TESTS).now()
    response = client.post(
        "/auth/login",
        json=_login_json(SEEDED_USER_WITH_MFA_EMAIL, SEEDED_USER_PASSWORD, otp=otp),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data

    db_session.expire_all()
    # test if succesfull login created exactly one MFA code  
    assert db_session.query(MfaCode).filter(MfaCode.user_id == registered_user_with_mfa.id).count() == 1
