from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import os

import jwt
from fastapi import HTTPException, status

from apps.api.config import JWT_ALGORITHM, JWT_EXPIRATION_HOURS, JWT_SECRET


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt_b64, digest_b64 = hashed.split("$", maxsplit=1)
        salt = base64.b64decode(salt_b64.encode())
        expected_digest = base64.b64decode(digest_b64.encode())
    except (ValueError, TypeError):
        return False

    current_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 100000
    )
    return hmac.compare_digest(current_digest, expected_digest)


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRATION_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from error
