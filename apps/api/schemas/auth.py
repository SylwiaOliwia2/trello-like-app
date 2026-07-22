from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_enabled: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    otp: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    id: int | None = None
    email: str
    mfa_enabled: bool
    mfa_otpauth_url: str | None = None
    registration_token: str | None = None
    registration_pending: bool = False


class ConfirmRegisterRequest(BaseModel):
    registration_token: str
    otp: str


class LegacyConfirmRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    otp: str


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    mfa_enabled: bool


class PendingRegistration(BaseModel):
    email: str
    password_hash: str
    mfa_enabled: bool
    mfa_secret: str
    created_at: datetime
