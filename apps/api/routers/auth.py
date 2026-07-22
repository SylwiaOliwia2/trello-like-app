from datetime import UTC, datetime
import secrets

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.config import MFA_ISSUER_NAME
from apps.api.db import get_db
from apps.api.deps import get_current_user
from apps.api.models import MfaCode, User
from apps.api.schemas.auth import (
    ConfirmRegisterRequest,
    CurrentUserResponse,
    LegacyConfirmRegisterRequest,
    LoginRequest,
    PendingRegistration,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from apps.api.security import (
    create_access_token,
    hash_otp,
    hash_password,
    verify_password,
)
from apps.api.services.auth import (
    cleanup_expired_pending_registrations,
    confirm_pending_registration,
    pending_registrations,
)

router = APIRouter(tags=["auth"])


@router.post(
    "/auth/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest, db: Session = Depends(get_db)
) -> RegisterResponse:
    cleanup_expired_pending_registrations()
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    mfa_secret = pyotp.random_base32() if payload.mfa_enabled else None
    if payload.mfa_enabled and mfa_secret:
        registration_token = secrets.token_urlsafe(32)
        pending_registrations[registration_token] = PendingRegistration(
            email=payload.email,
            password_hash=hash_password(payload.password),
            mfa_enabled=True,
            mfa_secret=mfa_secret,
            created_at=datetime.now(UTC),
        )
        mfa_otpauth_url = pyotp.TOTP(mfa_secret).provisioning_uri(
            name=payload.email, issuer_name=MFA_ISSUER_NAME
        )
        return RegisterResponse(
            email=payload.email,
            mfa_enabled=True,
            mfa_otpauth_url=mfa_otpauth_url,
            registration_token=registration_token,
            registration_pending=True,
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        mfa_enabled=payload.mfa_enabled,
        mfa_secret=mfa_secret,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    mfa_otpauth_url = (
        pyotp.TOTP(mfa_secret).provisioning_uri(
            name=payload.email, issuer_name=MFA_ISSUER_NAME
        )
        if mfa_secret
        else None
    )
    return RegisterResponse(
        id=user.id,
        email=user.email,
        mfa_enabled=user.mfa_enabled,
        mfa_otpauth_url=mfa_otpauth_url,
    )


@router.post(
    "/auth/register/confirm",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_register(
    payload: ConfirmRegisterRequest, db: Session = Depends(get_db)
) -> RegisterResponse:
    cleanup_expired_pending_registrations()
    return confirm_pending_registration(payload.registration_token, payload.otp, db)


@router.post(
    "/auth/register/mfa/confirm",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_register_legacy(
    payload: LegacyConfirmRegisterRequest, db: Session = Depends(get_db)
) -> RegisterResponse:
    cleanup_expired_pending_registrations()
    matching_token = next(
        (
            token
            for token, pending in pending_registrations.items()
            if pending.email == payload.email
            and verify_password(payload.password, pending.password_hash)
        ),
        None,
    )
    if not matching_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired pending registration",
        )

    return confirm_pending_registration(matching_token, payload.otp, db)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if user.mfa_enabled:
        if not payload.otp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA code required"
            )
        if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(
            payload.otp, valid_window=1
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP"
            )

        mfa_log = MfaCode(user_id=user.id, otp_hash=hash_otp(payload.otp), used=True)
        db.add(mfa_log)
        db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


# NOTE: JWT-protected smoke endpoint
@router.get("/protected")
def protected(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"message": f"Hello {current_user.email}"}
