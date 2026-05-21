import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from apps.api.config import CORS_ORIGINS
from apps.api.db import Base, SessionLocal, engine, get_db
from apps.api.models import Board, BoardMembership, MfaCode, User
from apps.api.routers.auth import router as auth_router
from apps.api.routers.boards import router as boards_router
from apps.api.routers.health import router as health_router
from apps.api.security import hash_otp, hash_password, verify_password

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(boards_router)


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


__all__ = [
    "Base",
    "Board",
    "BoardMembership",
    "MfaCode",
    "SessionLocal",
    "User",
    "app",
    "engine",
    "get_db",
    "hash_otp",
    "hash_password",
    "verify_password",
]
