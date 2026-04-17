from sqlalchemy.orm import Session

from apps.api.main import User


def get_user_by_email_for_test(db_session: Session, email: str) -> User | None:
    return db_session.query(User).filter(User.email == email).first()
