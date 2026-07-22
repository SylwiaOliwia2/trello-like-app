import allure
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import Board, BoardMembership
from apps.api.tests.fixtures.user_fixture import LoggedInUser
from apps.api.tests.helpers.board_helpers import _delete_board, seed_board_members

pytestmark = allure.epic("Board")


@allure.feature("membership")
@pytest.mark.API
def test_board_owner_can_add_board_member(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[3]
    board_member = logged_in_users[2]
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    response = client.post(
        f"/boards/{board.id}/members",
        json={"email": board_member.email},
        headers=logged_in_users[3].auth_headers,
    )

    assert response.status_code == 201

    response_json = response.json()

    assert response_json["user_id"] == board_member.user_id
    assert response_json["email"] == board_member.email
    assert response_json["role"] == "member"

    # confirm, that the board_member has access to the board
    response_retrive = client.get(
        f"/boards/{board.id}",
        headers=board_member.auth_headers,
    )

    assert response_retrive.status_code == 200
    assert response_retrive.json()["id"] == board.id


@allure.feature("management")
@pytest.mark.API
def test_user_can_not_create_board_with_empty_name(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    response = client.post(
        "/boards",
        json={"name": ""},
        headers=logged_in_users[0].auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Board name is required"

    db_session.expire_all()
    assert (
        db_session.query(Board).filter(Board.name == "").count() == 0
    ), "Board with empty name can not be created!"


@allure.feature("membership")
@pytest.mark.API
def test_user_sees_only_the_boards_that_he_belongs_to(
    client: TestClient,
    logged_in_users: list[LoggedInUser],
) -> None:
    user_0_token = logged_in_users[0].auth_headers

    # TODO: check also for membership (as for now the user is not a member of any board)

    response = client.get("/boards/", headers=user_0_token)

    expected_board_name = f"{logged_in_users[0].user_id}_owner_id_board"

    assert response.status_code == 200
    boards = response.json()
    assert len(boards) == 1
    assert boards[0]["name"] == expected_board_name


@allure.feature("membership")
@pytest.mark.API
def test_user_can_not_access_board_that_he_doesnt_belong_to(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    user_1_board = (
        db_session.query(Board)
        .filter(Board.owner_id == logged_in_users[1].user_id)
        .one()
    )
    user_0_token = logged_in_users[0].auth_headers

    response = client.get(f"/boards/{user_1_board.id}", headers=user_0_token)

    assert response.status_code == 403
    assert response.json()["detail"] == "Not a board member"


@allure.feature("membership")
@pytest.mark.API
def test_user_can_not_add_to_board_not_registered_email(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[0]
    non_registered_email = "qwerty@qwerty.com"
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    response = client.post(
        f"/boards/{board.id}/members",
        json={"email": non_registered_email},
        headers=logged_in_users[0].auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    db_session.expire_all()

    assert (
        db_session.query(BoardMembership)
        .filter(
            BoardMembership.board_id == board.id,
            BoardMembership.user_id != board_owner.user_id,
        )
        .count()
        == 0
    ), "Not registered email can not be a board member!!"


@allure.feature("management")
@pytest.mark.API
def test_unauthenticated_user_cannot_list_boards(
    client: TestClient,
) -> None:
    response = client.get("/boards/", headers=None)

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


@allure.feature("membership")
@pytest.mark.API
def test_board_owner_can_not_remove_himself_from_the_board_members(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[0]
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    response = client.delete(
        f"/boards/{board.id}/members/{board_owner.user_id}",
        headers=board_owner.auth_headers,
    )

    assert response.status_code == 400

    # double check, that the owner still has an access
    response_confirmation = client.get(
        f"/boards/{board.id}", headers=board_owner.auth_headers
    )

    assert response_confirmation.status_code == 200

    board_details = response_confirmation.json()

    assert board_details["id"] == board.id
    assert board_details["owner_id"] == board_owner.user_id
    assert len(board_details["members"]) == 1
    assert board_details["members"][0]["user_id"] == board_owner.user_id
    assert board_details["members"][0]["role"] == "owner"


@allure.feature("management")
@pytest.mark.API
def test_board_owner_can_delete_the_board(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[0]
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    response_delete = client.delete(
        f"/boards/{board.id}",
        headers=board_owner.auth_headers,
    )

    assert response_delete.status_code == 204

    response_retrive = client.get(
        f"/boards/{board.id}",
        headers=board_owner.auth_headers,
    )

    assert response_retrive.status_code == 404
    assert response_retrive.json()["detail"] == "Board not found"


@allure.feature("membership")
@pytest.mark.API
def test_board_member_has_no_access_after_board_is_deleted(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[3]
    board_member = logged_in_users[2]
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    seed_board_members(db_session, board.id, [board_member.email])

    response_delete = client.delete(
        f"/boards/{board.id}",
        headers=board_owner.auth_headers,
    )

    assert response_delete.status_code == 204

    response_retrive = client.get(
        f"/boards/{board.id}",
        headers=board_member.auth_headers,
    )

    assert response_retrive.status_code == 404
    assert response_retrive.json()["detail"] == "Board not found"


@allure.feature("management")
@pytest.mark.API
def test_user_can_create_a_board_and_becomes_board_owner(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[0]
    board_name = "Example board"

    response_create = client.post(
        "/boards",
        json={"name": board_name},
        headers=board_owner.auth_headers,
    )

    assert response_create.status_code == 201

    response_json = response_create.json()

    assert response_json["owner_id"] == board_owner.user_id
    assert response_json["role"] == "owner"
    assert response_json["name"] == board_name
    assert "id" in response_json and isinstance(response_json["id"], int)

    response_retrive = client.get(
        f"/boards/{response_json["id"]}",
        headers=board_owner.auth_headers,
    )

    assert response_retrive.status_code == 200

    board_details = response_retrive.json()

    assert board_details["owner_id"] == board_owner.user_id
    assert board_details["role"] == "owner"
    assert board_details["name"] == board_name
    assert board_details["id"] == response_json["id"]
    assert len(board_details["members"]) == 1

    board_member = board_details["members"][0]

    assert board_member["user_id"] == board_owner.user_id
    assert board_member["email"] == board_owner.email
    assert board_member["role"] == "owner"

    _delete_board(db_session, response_json["id"])


@allure.feature("membership")
@pytest.mark.API
def test_board_member_can_not_delete_the_board(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[3]
    board_member = logged_in_users[2]
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    seed_board_members(db_session, board.id, [board_member.email])

    response_delete = client.delete(
        f"/boards/{board.id}",
        headers=board_member.auth_headers,
    )

    assert response_delete.status_code == 403

    # confirm, that the board is not deleted
    response_retrive = client.get(
        f"/boards/{board.id}",
        headers=board_member.auth_headers,
    )

    assert response_retrive.status_code == 200
    assert response_retrive.json()["id"] == board.id


@allure.feature("membership")
@pytest.mark.API
def test_board_member_can_not_remove_other_users_from_the_board(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[3]
    board_member = logged_in_users[2]
    other_board_member = logged_in_users[1]
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    seed_board_members(
        db_session, board.id, [board_member.email, other_board_member.email]
    )

    response_delete = client.delete(
        f"/boards/{board.id}/members/{other_board_member.user_id}",
        headers=board_member.auth_headers,
    )

    assert response_delete.status_code == 403

    # confirm, that the other_board_member has access to the board
    response_retrive = client.get(
        f"/boards/{board.id}",
        headers=other_board_member.auth_headers,
    )

    assert response_retrive.status_code == 200
    assert response_retrive.json()["id"] == board.id


@allure.feature("membership")
@pytest.mark.API
def test_board_owner_can_not_add_member_twice(
    client: TestClient,
    db_session: Session,
    logged_in_users: list[LoggedInUser],
) -> None:
    board_owner = logged_in_users[3]
    board_member = logged_in_users[2]
    board = db_session.query(Board).filter(Board.owner_id == board_owner.user_id).one()

    response = client.post(
        f"/boards/{board.id}/members",
        json={"email": board_member.email},
        headers=logged_in_users[3].auth_headers,
    )

    assert response.status_code == 201

    # add the same user once again
    response_2 = client.post(
        f"/boards/{board.id}/members",
        json={"email": board_member.email},
        headers=logged_in_users[3].auth_headers,
    )

    assert response_2.status_code == 400

    # confirm, that the member is only once added to board.
    db_session.expire_all()

    assert (
        db_session.query(BoardMembership)
        .filter(
            BoardMembership.board_id == board.id,
            BoardMembership.user_id != board_member.user_id,
        )
        .count()
        == 1
    ), "User has been added twice to the board!"
