from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.api.models import Board, BoardMembership, User


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
