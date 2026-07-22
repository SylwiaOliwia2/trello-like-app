from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.models import User
from apps.api.security import decode_token


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
