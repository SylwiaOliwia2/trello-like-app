from collections.abc import Generator
from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import os
import secrets
import time

import jwt
import pyotp
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://web:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://app:app@db:5432/appdb"
)
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class MfaCode(Base):
    __tablename__ = "mfa_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    otp_hash: Mapped[str] = mapped_column(String(64))
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class BoardMembership(Base):
    __tablename__ = "board_memberships"
    __table_args__ = (
        UniqueConstraint("board_id", "user_id", name="uq_board_membership"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))  # "owner" or "member"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


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


class HealthResponse(BaseModel):
    status: str


class PendingRegistration(BaseModel):
    email: str
    password_hash: str
    mfa_enabled: bool
    mfa_secret: str
    created_at: datetime


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


def get_db() -> Generator[Session, None, None]:
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


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )
    token = authorization.split(" ", maxsplit=1)[1]
    payload = decode_token(token)
    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@app.on_event("startup")
def on_startup() -> None:
    max_attempts = 15
    delay_seconds = 1
    last_error: Exception | None = None
    for _ in range(max_attempts):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as error:
            last_error = error
            time.sleep(delay_seconds)
    if last_error:
        raise last_error


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
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
            name=payload.email, issuer_name="task-manager-app"
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
            name=payload.email, issuer_name="task-manager-app"
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


@app.post(
    "/auth/register/confirm",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_register(
    payload: ConfirmRegisterRequest, db: Session = Depends(get_db)
) -> RegisterResponse:
    cleanup_expired_pending_registrations()
    return confirm_pending_registration(payload.registration_token, payload.otp, db)


@app.post(
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


@app.post("/auth/login", response_model=TokenResponse)
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


@app.get("/auth/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


# NOTE: JWT-protected smoke endpoint
@app.get("/protected")
def protected(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"message": f"Hello {current_user.email}"}


# --------------------- Boards ---------------------


class BoardCreateRequest(BaseModel):
    name: str


class BoardSummary(BaseModel):
    id: int
    name: str
    owner_id: int
    role: str  # caller's role on this board


class BoardMemberInfo(BaseModel):
    user_id: int
    email: str
    role: str


class BoardDetail(BaseModel):
    id: int
    name: str
    owner_id: int
    role: str
    members: list[BoardMemberInfo]


class UserSummary(BaseModel):
    id: int
    email: str


class AddMemberRequest(BaseModel):
    email: EmailStr


def get_membership(db: Session, board_id: int, user_id: int) -> BoardMembership | None:
    return (
        db.query(BoardMembership)
        .filter(
            BoardMembership.board_id == board_id,
            BoardMembership.user_id == user_id,
        )
        .first()
    )


def require_board_member(db: Session, board: Board, user: User) -> BoardMembership:
    membership = get_membership(db, board.id, user.id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a board member",
        )
    return membership


def require_board_owner(db: Session, board: Board, user: User) -> BoardMembership:
    membership = require_board_member(db, board, user)
    if membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the board owner can perform this action",
        )
    return membership


def get_board_or_404(db: Session, board_id: int) -> Board:
    board = db.get(Board, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Board not found"
        )
    return board


@app.get("/boards", response_model=list[BoardSummary])
def list_boards(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BoardSummary]:
    rows = (
        db.query(Board, BoardMembership)
        .join(BoardMembership, BoardMembership.board_id == Board.id)
        .filter(BoardMembership.user_id == current_user.id)
        .order_by(Board.created_at.desc())
        .all()
    )
    return [
        BoardSummary(
            id=board.id,
            name=board.name,
            owner_id=board.owner_id,
            role=membership.role,
        )
        for board, membership in rows
    ]


@app.post("/boards", response_model=BoardSummary, status_code=status.HTTP_201_CREATED)
def create_board(
    payload: BoardCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardSummary:
    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Board name is required"
        )
    board = Board(name=name, owner_id=current_user.id)
    db.add(board)
    db.flush()
    db.add(BoardMembership(board_id=board.id, user_id=current_user.id, role="owner"))
    db.commit()
    db.refresh(board)
    return BoardSummary(
        id=board.id, name=board.name, owner_id=board.owner_id, role="owner"
    )


@app.get("/boards/{board_id}", response_model=BoardDetail)
def get_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardDetail:
    board = get_board_or_404(db, board_id)
    membership = require_board_member(db, board, current_user)

    rows = (
        db.query(BoardMembership, User)
        .join(User, User.id == BoardMembership.user_id)
        .filter(BoardMembership.board_id == board.id)
        .order_by(BoardMembership.role.desc(), User.email.asc())
        .all()
    )
    members = [
        BoardMemberInfo(user_id=user.id, email=user.email, role=m.role)
        for m, user in rows
    ]
    return BoardDetail(
        id=board.id,
        name=board.name,
        owner_id=board.owner_id,
        role=membership.role,
        members=members,
    )


@app.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    board = get_board_or_404(db, board_id)
    require_board_owner(db, board, current_user)

    db.query(BoardMembership).filter(BoardMembership.board_id == board.id).delete()
    db.delete(board)
    db.commit()


@app.post(
    "/boards/{board_id}/members",
    response_model=BoardMemberInfo,
    status_code=status.HTTP_201_CREATED,
)
def add_board_member(
    board_id: int,
    payload: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardMemberInfo:
    board = get_board_or_404(db, board_id)
    require_board_owner(db, board, current_user)

    target = db.query(User).filter(User.email == payload.email).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    existing = get_membership(db, board.id, target.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a board member",
        )

    membership = BoardMembership(board_id=board.id, user_id=target.id, role="member")
    db.add(membership)
    db.commit()
    return BoardMemberInfo(user_id=target.id, email=target.email, role="member")


@app.delete(
    "/boards/{board_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_board_member(
    board_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    board = get_board_or_404(db, board_id)
    require_board_owner(db, board, current_user)

    if user_id == board.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot be removed from their own board",
        )

    membership = get_membership(db, board.id, user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    db.delete(membership)
    db.commit()


@app.post("/boards/{board_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    board = get_board_or_404(db, board_id)
    membership = require_board_member(db, board, current_user)

    if membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot leave the board. Delete it instead.",
        )

    db.delete(membership)
    db.commit()


@app.get("/users", response_model=list[UserSummary])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserSummary]:
    users = db.query(User).order_by(User.email.asc()).all()
    return [UserSummary(id=u.id, email=u.email) for u in users]
