from sqlalchemy.orm import Session
import urllib.parse
from apps.api.main import User


def get_user_by_email_for_test(db_session: Session, email: str) -> User | None:
    return db_session.query(User).filter(User.email == email).first()


def _totp_secret_from_otpauth_url(otpauth_url: str) -> str:
    """Extract the shared secret from a standard `otpauth://totp/...` URI (as returned by the API)."""
    parsed = urllib.parse.urlparse(otpauth_url)
    secret = urllib.parse.parse_qs(parsed.query).get("secret", [None])[0]
    assert secret is not None
    return secret
