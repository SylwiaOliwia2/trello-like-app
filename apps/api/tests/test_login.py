import pyotp
import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import MfaCode, User
from apps.api.tests.fixtures.user_fixture import (
    FIXED_MFA_SECRET_FOR_TESTS,
    SEEDED_USER_PASSWORD,
    SEEDED_USER_WITH_MFA_EMAIL,
)
from apps.api.tests.helpers.login_helpers import _login_json


@pytest.mark.smoke
@pytest.mark.API
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
@pytest.mark.API
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
    assert (
        db_session.query(MfaCode)
        .filter(MfaCode.user_id == registered_user_with_mfa.id)
        .count()
        == 1
    )


@pytest.mark.smoke
@pytest.mark.API
def test_login_with_wrong_password_does_not_return_access_token(
    client: TestClient,
    registered_user_no_mfa: User,
) -> None:
    response = client.post(
        "/auth/login",
        json=_login_json(registered_user_no_mfa.email, "WRONG_PASSWORD"),
    )

    assert response.status_code == 401
    data = response.json()
    assert "access_token" not in data

    # TODO: add similar test for MFA login


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.API
def test_user_with_MFA_enabled_can_not_log_in_with_empty_MFA_code(
    client: TestClient,
    registered_user_with_mfa: User,
) -> None:
    response = client.post(
        "/auth/login",
        json=_login_json(SEEDED_USER_WITH_MFA_EMAIL, SEEDED_USER_PASSWORD, otp=None),
    )
    assert response.status_code == 401
    data = response.json()
    assert "access_token" not in data


@pytest.mark.smoke
@pytest.mark.security
@pytest.mark.API
def test_login_sql_injection_attempt_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json=_login_json("sqli.user@example.com", "x' OR '1'='1"),
    )

    assert response.status_code == 401
    data = response.json()
    assert "access_token" not in data


@pytest.mark.smoke
@pytest.mark.security
@pytest.mark.API
def test_login_xss_attempt_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json=_login_json("xss.user@example.com", "<img src=x onerror=alert(1)>"),
    )

    assert response.status_code == 401
    data = response.json()
    assert "access_token" not in data


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.API
def test_expired_OTP_does_not_allow_to_login(
    client: TestClient,
    registered_user_with_mfa: User,
) -> None:
    otp = pyotp.TOTP(FIXED_MFA_SECRET_FOR_TESTS).at(int(time.time()) - 120)
    response = client.post(
        "/auth/login",
        json=_login_json(SEEDED_USER_WITH_MFA_EMAIL, SEEDED_USER_PASSWORD, otp=otp),
    )
    assert response.status_code == 401
    data = response.json()
    assert "access_token" not in data


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.API
@pytest.mark.skip(reason="Not implemented yet.")
def test_login_with_validated_OTP_does_not_allow_to_login(
    client: TestClient,
) -> None:
    otp = pyotp.TOTP(FIXED_MFA_SECRET_FOR_TESTS).now()

    # login first time with valid OTP - OK
    response = client.post(
        "/auth/login",
        json=_login_json(SEEDED_USER_WITH_MFA_EMAIL, SEEDED_USER_PASSWORD, otp=otp),
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # login second time with the same (not expired) OTP - NOT ALLOWED
    response = client.post(
        "/auth/login",
        json=_login_json(SEEDED_USER_WITH_MFA_EMAIL, SEEDED_USER_PASSWORD, otp=otp),
    )
    assert response.status_code == 401
    data = response.json()
    assert "access_token" not in data


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.API
def test_login_with_wrong_OTP_does_not_allow_to_login(
    client: TestClient,
) -> None:
    wrong_otp = "123456"

    response = client.post(
        "/auth/login",
        json=_login_json(
            SEEDED_USER_WITH_MFA_EMAIL, SEEDED_USER_PASSWORD, otp=wrong_otp
        ),
    )
    assert response.status_code == 401
    data = response.json()
    assert "access_token" not in data
