from dataclasses import (
    dataclass,
)  # NOTE: dataclass could be replaced by Pydantic, but Pydantic is heavier and will be overkill here.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import User, hash_password
from apps.api.tests.helpers.login_helpers import (
    _login_json,
    get_user_by_email_for_test,
)

SEEDED_USER_PASSWORD = "StrongPass123!"
SEEDED_USER_NO_MFA_EMAIL = "fixture.user.no_mfa@example.com"
SEEDED_USER_WITH_MFA_EMAIL = "fixture.user.mfa@example.com"
BOARD_USER_EMAILS = [
    "board.user1@example.com",
    "board.user2@example.com",
    "board.user3@example.com",
    "board.user4@example.com",
]
# Fixed TOTP secret so tests can call `pyotp.TOTP(FIXED_MFA_SECRET_FOR_TESTS).now()`.
FIXED_MFA_SECRET_FOR_TESTS = "JBSWY3DPEHPK3PXP"


@dataclass
class LoggedInUser:
    user_id: int
    email: str
    password: str
    token: str

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def seed_baseline_users(session: Session) -> None:
    """
    Insert baseline test users into the database.
    """
    session.add_all(
        [
            User(
                email=SEEDED_USER_NO_MFA_EMAIL,
                password_hash=hash_password(SEEDED_USER_PASSWORD),
                mfa_enabled=False,
                mfa_secret=None,
            ),
            User(
                email=SEEDED_USER_WITH_MFA_EMAIL,
                password_hash=hash_password(SEEDED_USER_PASSWORD),
                mfa_enabled=True,
                mfa_secret=FIXED_MFA_SECRET_FOR_TESTS,
            ),
            *[
                User(
                    email=email,
                    password_hash=hash_password(SEEDED_USER_PASSWORD),
                    mfa_enabled=False,
                    mfa_secret=None,
                )
                for email in BOARD_USER_EMAILS
            ],
        ]
    )
    session.commit()


@pytest.fixture()
def registered_user_no_mfa(db_session: Session) -> User:
    user = get_user_by_email_for_test(db_session, SEEDED_USER_NO_MFA_EMAIL)
    assert user is not None, "baseline user missing; db_session seed may have failed"
    return user


@pytest.fixture()
def registered_user_with_mfa(db_session: Session) -> User:
    user = get_user_by_email_for_test(db_session, SEEDED_USER_WITH_MFA_EMAIL)
    assert user is not None, "baseline user missing; db_session seed may have failed"
    return user


@pytest.fixture()
def logged_in_users(client: TestClient, db_session: Session) -> list[LoggedInUser]:
    """
    Log in 4 seeded no-MFA users.
    Returns a list of logged-in users.
    """
    users: list[LoggedInUser] = []
    for email in BOARD_USER_EMAILS:
        db_row = get_user_by_email_for_test(db_session, email)
        assert db_row is not None, f"seeded user missing: {email}"

        response = client.post(
            "/auth/login",
            json=_login_json(email, SEEDED_USER_PASSWORD),
        )
        assert (
            response.status_code == 200
        ), f"login failed for {email}: {response.status_code} {response.text}"
        token = response.json()["access_token"]

        users.append(
            LoggedInUser(
                user_id=db_row.id,
                email=email,
                password=SEEDED_USER_PASSWORD,
                token=token,
            )
        )

    return users
