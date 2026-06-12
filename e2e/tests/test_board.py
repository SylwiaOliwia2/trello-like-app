from typing import Callable

import re
from playwright.sync_api import Page, expect, APIResponse
import pytest

from e2e.POM.board import BoardPage
from e2e.POM.home import HomePage


@pytest.mark.regression
@pytest.mark.e2e
def test_user_sees_all_his_boards_on_the_home_page(
    logged_in_page: Page,
    access_token: str,
    registered_user: dict[str, str],
    make_user_with_token: Callable[..., dict[str, str]],
    api_create_board: Callable[..., APIResponse],
    api_add_board_member: Callable[..., APIResponse],
) -> None:
    owned_board = api_create_board("Owned Board", token=access_token).json()

    other_user = make_user_with_token()
    member_board = api_create_board("Member Board", token=other_user["token"]).json()
    api_add_board_member(
        member_board["id"],
        registered_user["email"],
        token=other_user["token"],
    )

    page = logged_in_page
    home_page = HomePage(page)
    home_page.navigate()

    expect(home_page.board_link(owned_board["id"])).to_be_visible()
    expect(home_page.board_link(member_board["id"])).to_be_visible()


@pytest.mark.regression
@pytest.mark.e2e
def test_delete_board_asks_for_confirmation_first(
    logged_in_page: Page,
    access_token: str,
    api_create_board: Callable[..., APIResponse],
    api_get_board: Callable[..., APIResponse],
) -> None:
    board = api_create_board("Board To Keep", token=access_token).json()

    board_page = BoardPage(logged_in_page)
    board_page.navigate(board["id"])
    board_page.open_delete_confirmation()

    expect(board_page.confirm_delete_button).to_be_visible()
    expect(board_page.cancel_delete_button).to_be_visible()

    # confirm, that the board is NOT deleted yet
    response = api_get_board(board["id"], token=access_token)

    assert response.status == 200


@pytest.mark.regression
@pytest.mark.e2e
def test_owner_can_cancel_board_deletion(
    logged_in_page: Page,
    access_token: str,
    api_create_board: Callable[..., APIResponse],
    api_get_board: Callable[..., APIResponse],
) -> None:
    board = api_create_board("Board To Keep", token=access_token).json()

    board_page = BoardPage(logged_in_page)
    board_page.navigate(board["id"])
    board_page.open_delete_confirmation()
    board_page.cancel_delete()

    expect(board_page.delete_confirm_popup).not_to_be_visible()

    # confirm, that the board is NOT deleted
    response = api_get_board(board["id"], token=access_token)

    assert response.status == 200


@pytest.mark.regression
@pytest.mark.e2e
def test_deleted_board_disappears_from_home(
    logged_in_page: Page,
    access_token: str,
    api_create_board: Callable[..., APIResponse],
) -> None:
    board = api_create_board("Board To Delete", token=access_token).json()

    board_page = BoardPage(logged_in_page)
    board_page.navigate(board["id"])
    board_page.delete_board()

    expect(logged_in_page).to_have_url(re.compile(".*home"))

    home_page = HomePage(logged_in_page)
    expect(home_page.board_link(board["id"])).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.e2e
def test_deleted_board_disappears_from_member_home(
    logged_in_page: Page,
    access_token: str,
    make_user_with_token: Callable[..., dict[str, str]],
    make_logged_in_page: Callable[[str], Page],
    api_create_board: Callable[..., APIResponse],
    api_add_board_member: Callable[..., APIResponse],
) -> None:
    member = make_user_with_token()
    board = api_create_board("Shared Board", token=access_token).json()
    api_add_board_member(board["id"], member["email"], token=access_token)

    member_page = make_logged_in_page(member["token"])
    member_home = HomePage(member_page)
    expect(member_home.board_link(board["id"])).to_be_visible()

    # owner deletes the board
    board_page = BoardPage(logged_in_page)
    board_page.navigate(board["id"])
    board_page.delete_board()
    expect(logged_in_page).to_have_url(re.compile(".*home"))

    # the board disappears from the member's home page
    member_home.navigate()
    expect(member_home.board_link(board["id"])).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.e2e
def test_removed_board_member_does_not_have_access_to_board(
    make_user_with_token: Callable[..., dict[str, str]],
    make_logged_in_page: Callable[[str], Page],
    api_create_board: Callable[..., APIResponse],
    api_add_board_member: Callable[..., APIResponse],
) -> None:
    owner = make_user_with_token()
    board = api_create_board("Shared Board", token=owner["token"]).json()

    member = make_user_with_token()
    member_id = api_add_board_member(
        board["id"], member["email"], token=owner["token"]
    ).json()["user_id"]

    member_page = make_logged_in_page(member["token"])
    member_home = HomePage(member_page)
    expect(member_home.board_link(board["id"])).to_be_visible()

    # owner removes the member using the "Remove" button in the UI
    owner_page = make_logged_in_page(owner["token"])
    owner_board_page = BoardPage(owner_page)
    owner_board_page.navigate(board["id"])
    owner_board_page.remove_board_member(member_id)
    expect(owner_board_page.member_item(member_id)).not_to_be_visible()

    # the member can no longer see the board on the Home page
    member_home.navigate()
    expect(member_home.board_link(board["id"])).not_to_be_visible()

    # the member can no longer open the board link
    member_board_page = BoardPage(member_page)
    member_board_page.navigate(board["id"])
    expect(member_board_page.board_load_error).to_be_visible()
    expect(member_board_page.board_name).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.e2e
def test_owner_can_add_member_using_dropdown_list(
    make_logged_in_page: Callable[[str], Page],
    make_user_with_token: Callable[..., dict[str, str]],
    api_create_board: Callable[..., APIResponse],
    get_board_member_id_by_email: Callable[..., int],
) -> None:
    owner = make_user_with_token()
    board = api_create_board("Shared Board", token=owner["token"]).json()
    member = make_user_with_token()

    # owner opens the board and adds the member via the dropdown
    owner_page = make_logged_in_page(owner["token"])
    board_page = BoardPage(owner_page)
    board_page.navigate(board["id"])
    board_page.add_board_member(member["email"])

    # the member now has API access to the board
    member_id = get_board_member_id_by_email(
        board["id"], member["email"], token=owner["token"]
    )
    expect(board_page.member_item(member_id)).to_be_visible()


@pytest.mark.regression
@pytest.mark.e2e
def test_board_owner_sees_board_members_along_with_roles(
    make_user_with_token: Callable[..., dict[str, str]],
    make_logged_in_page: Callable[[str], Page],
    api_create_board: Callable[..., APIResponse],
    get_board_member_id_by_email: Callable[..., int],
) -> None:
    owner = make_user_with_token()
    board = api_create_board("Shared Board", token=owner["token"]).json()
    member_1 = make_user_with_token()
    member_2 = make_user_with_token()

    # owner opens the board and adds the member via the dropdown
    owner_page = make_logged_in_page(owner["token"])
    board_page = BoardPage(owner_page)
    board_page.navigate(board["id"])
    board_page.add_board_member(member_1["email"])
    board_page.add_board_member(member_2["email"])

    # TODO: shall front dev generate the same test-id's for all users? Then we can access them as .all() and compare values inside list (it will be easier for QA)
    member_1_id = get_board_member_id_by_email(
        board["id"],
        member_1["email"],
        token=member_1["token"],
    )

    expect(board_page.member_item(member_1_id)).to_be_visible()
    expect(board_page.member_role(member_1_id)).to_have_text("member")

    member_2_id = get_board_member_id_by_email(
        board["id"],
        member_2["email"],
        token=member_2["token"],
    )

    expect(board_page.member_item(member_2_id)).to_be_visible()
    expect(board_page.member_role(member_2_id)).to_have_text("member")

    owner_id = get_board_member_id_by_email(
        board["id"], owner["email"], token=owner["token"]
    )

    expect(board_page.member_item(owner_id)).to_be_visible()
    expect(board_page.member_role(owner_id)).to_have_text("owner")


@pytest.mark.regression
@pytest.mark.e2e
def test_board_member_can_leave_the_board(
    make_logged_in_page: Callable[[str], Page],
    make_user_with_token: Callable[..., dict[str, str]],
    api_create_board: Callable[..., APIResponse],
    api_get_board: Callable[..., APIResponse],
    api_add_board_member: Callable[..., APIResponse],
) -> None:
    owner = make_user_with_token()
    board = api_create_board("Shared Board", token=owner["token"]).json()
    member = make_user_with_token()

    api_add_board_member(board["id"], member["email"], token=owner["token"])

    # user opens the board and leaves
    member_page = make_logged_in_page(member["token"])
    board_page = BoardPage(member_page)
    board_page.navigate(board["id"])
    board_page.remove_myself_from_the_board()

    # the member is sent back home and the board is gone from there
    expect(member_page).to_have_url(re.compile(".*home"))
    member_home = HomePage(member_page)
    expect(member_home.board_link(board["id"])).not_to_be_visible()

    # the member no longer has API access to the board
    member_view = api_get_board(board["id"], token=member["token"])
    assert member_view.status == 403

    # confirm, that th ebaord still exists
    owner_view = api_get_board(board["id"], token=owner["token"])
    assert owner_view.status == 200
