from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.deps import get_current_user
from apps.api.models import Board, BoardMembership, User
from apps.api.schemas.board import (
    AddMemberRequest,
    BoardCreateRequest,
    BoardDetail,
    BoardMemberInfo,
    BoardSummary,
    UserSummary,
)
from apps.api.services.boards import (
    get_board_or_404,
    get_membership,
    require_board_member,
    require_board_owner,
)

router = APIRouter(tags=["boards"])


@router.get("/boards", response_model=list[BoardSummary])
def list_boards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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


@router.post(
    "/boards", response_model=BoardSummary, status_code=status.HTTP_201_CREATED
)
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


@router.get("/boards/{board_id}", response_model=BoardDetail)
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


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.post(
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


@router.delete(
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


@router.post("/boards/{board_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
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


@router.get("/users", response_model=list[UserSummary])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserSummary]:
    users = db.query(User).order_by(User.email.asc()).all()
    return [UserSummary(id=u.id, email=u.email) for u in users]
