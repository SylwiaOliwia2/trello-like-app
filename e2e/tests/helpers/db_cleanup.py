"""Direct DB cleanup for e2e fixtures (no delete-user API)."""

from apps.api.db import SessionLocal
from apps.api.models import Board, BoardMembership, MfaCode, User


def delete_user(user_id: int) -> None:
    """Delete a user and related boards/memberships/mfa rows."""
    # TODO: Keep only user deletion. Board deletion should be in a separate function for cleaner function.
    session = SessionLocal()
    try:
        owned_board_ids = [
            row[0]
            for row in session.query(Board.id).filter(Board.owner_id == user_id).all()
        ]
        if owned_board_ids:
            session.query(BoardMembership).filter(
                BoardMembership.board_id.in_(owned_board_ids)
            ).delete(synchronize_session=False)
            session.query(Board).filter(Board.id.in_(owned_board_ids)).delete(
                synchronize_session=False
            )

        session.query(BoardMembership).filter(
            BoardMembership.user_id == user_id
        ).delete(synchronize_session=False)
        session.query(MfaCode).filter(MfaCode.user_id == user_id).delete(
            synchronize_session=False
        )
        session.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()
