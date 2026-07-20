from collections.abc import Callable, Generator
from dataclasses import (
    dataclass,
)  # NOTE: dataclass could be replaced by Pydantic, but Pydantic is heavier and will be overkill here.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import User, hash_password
from apps.api.models import Board, BoardMembership, MfaCode
from apps.api.tests.helpers.login_helpers import _login_json

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


def _delete_user(session: Session, user_id: int) -> None:
    """Delete a user and rows that reference it."""

    session.query(BoardMembership).filter(BoardMembership.user_id == user_id).delete(
        synchronize_session=False
    )
    session.query(MfaCode).filter(MfaCode.user_id == user_id).delete(
        synchronize_session=False
    )
    session.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    session.commit()


@pytest.fixture()
def user_factory(
    db_session: Session,
) -> Generator[Callable[..., User], None, None]:
    """Create users for a test; delete them (in reverse) on teardown."""
    created_ids: list[int] = []

    def _create_user(
        *,
        email: str,
        password: str = SEEDED_USER_PASSWORD,
        mfa_enabled: bool = False,
        mfa_secret: str | None = None,
    ) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            mfa_enabled=mfa_enabled,
            mfa_secret=mfa_secret,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        created_ids.append(user.id)
        return user

    yield _create_user

    for user_id in reversed(created_ids):
        _delete_user(db_session, user_id)


@pytest.fixture()
def registered_user_no_mfa(
    user_factory: Callable[..., User],
) -> Generator[User, None, None]:
    user = user_factory(
        email=SEEDED_USER_NO_MFA_EMAIL,
        password=SEEDED_USER_PASSWORD,
        mfa_enabled=False,
        mfa_secret=None,
    )
    yield user


@pytest.fixture()
def registered_user_with_mfa(
    user_factory: Callable[..., User],
) -> Generator[User, None, None]:
    user = user_factory(
        email=SEEDED_USER_WITH_MFA_EMAIL,
        password=SEEDED_USER_PASSWORD,
        mfa_enabled=True,
        mfa_secret=FIXED_MFA_SECRET_FOR_TESTS,
    )
    yield user


@pytest.fixture()
def board_users(
    user_factory: Callable[..., User],
) -> Generator[list[User], None, None]:
    users = [
        user_factory(email=email, password=SEEDED_USER_PASSWORD)
        for email in BOARD_USER_EMAILS
    ]
    yield users


@pytest.fixture()
def logged_in_users(
    client: TestClient,
    board_users: list[User],
    owned_boards: list[Board],
) -> list[LoggedInUser]:
    """Log in the 4 board users after their owned boards exist."""
    _ = owned_boards
    users: list[LoggedInUser] = []
    for board_user in board_users:
        response = client.post(
            "/auth/login",
            json=_login_json(board_user.email, SEEDED_USER_PASSWORD),
        )
        assert (
            response.status_code == 200
        ), f"login failed for {board_user.email}: {response.status_code} {response.text}"
        users.append(
            LoggedInUser(
                user_id=board_user.id,
                email=board_user.email,
                password=SEEDED_USER_PASSWORD,
                token=response.json()["access_token"],
            )
        )
    return users
