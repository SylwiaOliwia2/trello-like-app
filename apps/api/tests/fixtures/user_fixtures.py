import pytest
from sqlalchemy.orm import Session

from apps.api.main import User, hash_password
from apps.api.tests.helpers.login_helpers import get_user_by_email_for_test

SEEDED_USER_PASSWORD = "StrongPass123!"
SEEDED_USER_NO_MFA_EMAIL = "fixture.user.no_mfa@example.com"
SEEDED_USER_WITH_MFA_EMAIL = "fixture.user.mfa@example.com"
# Fixed TOTP secret so tests can call `pyotp.TOTP(FIXED_MFA_SECRET_FOR_TESTS).now()`.
FIXED_MFA_SECRET_FOR_TESTS = "JBSWY3DPEHPK3PXP"


def seed_baseline_users(session: Session) -> None:
    """Insert the two baseline accounts; `session.commit()` becomes a savepoint release under test harness."""
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
