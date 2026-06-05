from sqlalchemy.orm import Session

from apps.api.models import Board, BoardMembership
from apps.api.tests.fixtures.user_fixture import BOARD_USER_EMAILS
from apps.api.tests.helpers.login_helpers import get_user_by_email_for_test


def seed_board_per_user(
    session: Session, board_user_email_list: list[str] = BOARD_USER_EMAILS
) -> None:
    """
    Seed one empty board per board user (that user as the owner).
    """
    for email in board_user_email_list:
        owner = get_user_by_email_for_test(session, email)
        assert owner is not None, f"seeded user missing: {email}"

        board = Board(name=f"{owner.id}_owner_id_board", owner_id=owner.id)
        session.add(board)
        session.flush()
        session.add(BoardMembership(board_id=board.id, user_id=owner.id, role="owner"))

    session.commit()
