from datetime import UTC, datetime, timedelta

import pyotp
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.api.models import User
from apps.api.schemas.auth import PendingRegistration, RegisterResponse

PENDING_REGISTRATION_TTL = timedelta(minutes=10)
pending_registrations: dict[str, PendingRegistration] = {}


def cleanup_expired_pending_registrations() -> None:
    now = datetime.now(UTC)
    expired = [
        token
        for token, pending in pending_registrations.items()
        if pending.created_at + PENDING_REGISTRATION_TTL < now
    ]
    for token in expired:
        pending_registrations.pop(token, None)


def confirm_pending_registration(
    registration_token: str,
    otp: str,
    db: Session,
) -> RegisterResponse:
    pending = pending_registrations.get(registration_token)
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired registration token",
        )

    if db.query(User).filter(User.email == pending.email).first():
        pending_registrations.pop(registration_token, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    if not pyotp.TOTP(pending.mfa_secret).verify(otp, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP"
        )

    user = User(
        email=pending.email,
        password_hash=pending.password_hash,
        mfa_enabled=pending.mfa_enabled,
        mfa_secret=pending.mfa_secret,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    pending_registrations.pop(registration_token, None)

    return RegisterResponse(
        id=user.id,
        email=user.email,
        mfa_enabled=user.mfa_enabled,
    )
