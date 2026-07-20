from sqlalchemy.orm import Session

from apps.api.models import Board, BoardMembership
from apps.api.tests.helpers.login_helpers import get_user_by_email_for_test


def seed_board_members(
    session: Session, board_id: int, member_email_list: list[str], role: str = "member"
) -> None:
    # TODO: board membership should be cleaned up in this function?
    for email in member_email_list:
        user = get_user_by_email_for_test(session, email)
        assert user is not None, f"seeded user missing: {email}"

        session.add(BoardMembership(board_id=board_id, user_id=user.id, role=role))

    session.commit()


def _delete_board(session: Session, board_id: int) -> None:
    """Delete a board and its memberships."""
    session.query(BoardMembership).filter(BoardMembership.board_id == board_id).delete(
        synchronize_session=False
    )
    session.query(Board).filter(Board.id == board_id).delete(synchronize_session=False)
    session.commit()
