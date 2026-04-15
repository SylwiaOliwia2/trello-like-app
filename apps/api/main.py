from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import os

import jwt
import pyotp
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "postgresql+psycopg2://app:app@db:5432/appdb"
JWT_SECRET = "dev-secret-not-for-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class MfaCode(Base):
    __tablename__ = "mfa_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    otp_hash: Mapped[str] = mapped_column(String(64))
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


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
    id: int
    email: str
    mfa_enabled: bool
    mfa_otpauth_url: str | None = None


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    mfa_enabled: bool


class LoginPendingMfaResponse(BaseModel):
    mfa_required: bool = True


class HealthResponse(BaseModel):
    status: str


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

    current_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from error


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", maxsplit=1)[1]
    payload = decode_token(token)
    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    mfa_secret = pyotp.random_base32() if payload.mfa_enabled else None
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
        pyotp.TOTP(mfa_secret).provisioning_uri(name=payload.email, issuer_name="task-manager-app")
        if mfa_secret
        else None
    )
    return RegisterResponse(
        id=user.id,
        email=user.email,
        mfa_enabled=user.mfa_enabled,
        mfa_otpauth_url=mfa_otpauth_url,
    )


@app.post("/auth/login", response_model=TokenResponse | LoginPendingMfaResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse | LoginPendingMfaResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.mfa_enabled:
        if not payload.otp:
            return LoginPendingMfaResponse()
        if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(payload.otp, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

        mfa_log = MfaCode(user_id=user.id, otp_hash=hash_otp(payload.otp), used=True)
        db.add(mfa_log)
        db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


@app.get("/protected")
def protected(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"message": f"Hello {current_user.email}"}
