from sqlalchemy.orm import Session
from apps.api.models import BoardMembership
from apps.api.tests.helpers.login_helpers import get_user_by_email_for_test


def seed_board_members(
    session: Session, board_id: int, member_email_list: list[str], role: str = "member"
) -> None:
    for email in member_email_list:
        user = get_user_by_email_for_test(session, email)
        assert user is not None, f"seeded user missing: {email}"

        session.add(BoardMembership(board_id=board_id, user_id=user.id, role=role))

    session.commit()
