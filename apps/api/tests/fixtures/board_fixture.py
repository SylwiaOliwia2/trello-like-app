from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from apps.api.main import User
from apps.api.models import Board, BoardMembership


def _delete_boards(session: Session, board_ids: list[int]) -> None:
    if not board_ids:
        return
    session.query(BoardMembership).filter(
        BoardMembership.board_id.in_(board_ids)
    ).delete(synchronize_session=False)
    session.query(Board).filter(Board.id.in_(board_ids)).delete(
        synchronize_session=False
    )
    session.commit()


@pytest.fixture()
def owned_boards(
    db_session: Session, board_users: list[User]
) -> Generator[list[Board], None, None]:
    """
    Create one empty board per board user (owner membership included).
    Delete memberships + boards on teardown.
    """
    boards: list[Board] = []
    for owner in board_users:
        board = Board(name=f"{owner.id}_owner_id_board", owner_id=owner.id)
        db_session.add(board)
        db_session.flush()
        db_session.add(
            BoardMembership(board_id=board.id, user_id=owner.id, role="owner")
        )
        boards.append(board)
    db_session.commit()

    yield boards

    _delete_boards(db_session, [board.id for board in boards])
