from typing import Callable

import re
import requests
from playwright.sync_api import Page, expect
import pytest

from e2e.POM.board import BoardPage
from e2e.POM.home import HomePage
from e2e.tests.helpers.api_board_helpers import (
    add_user_to_board,
    get_board,
    post_create_board,
)


@pytest.mark.regression
@pytest.mark.e2e
def test_user_sees_all_his_boards_on_the_home_page(
    logged_in_page: Page,
    e2e_api_url: str,
    api_session: requests.Session,
    access_token: str,
    registered_user: dict[str, str],
    make_user_with_token: Callable[..., dict[str, str]],
) -> None:
    owned_board = post_create_board(
        e2e_api_url, api_session, "Owned Board", token=access_token
    ).json()

    other_user = make_user_with_token()
    member_board = post_create_board(
        e2e_api_url, api_session, "Member Board", token=other_user["token"]
    ).json()
    add_user_to_board(
        e2e_api_url,
        api_session,
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
    e2e_api_url: str,
    api_session: requests.Session,
    access_token: str,
) -> None:
    board = post_create_board(
        e2e_api_url, api_session, "Board To Keep", token=access_token
    ).json()

    board_page = BoardPage(logged_in_page)
    board_page.navigate(board["id"])
    board_page.open_delete_confirmation()

    expect(board_page.confirm_delete_button).to_be_visible()
    expect(board_page.cancel_delete_button).to_be_visible()

    # confirm, that the board is NOT deleted yet
    response = get_board(e2e_api_url, api_session, board["id"], token=access_token)

    assert response.status_code == 200


@pytest.mark.regression
@pytest.mark.e2e
def test_owner_can_cancel_board_deletion(
    logged_in_page: Page,
    e2e_api_url: str,
    api_session: requests.Session,
    access_token: str,
) -> None:
    board = post_create_board(
        e2e_api_url, api_session, "Board To Keep", token=access_token
    ).json()

    board_page = BoardPage(logged_in_page)
    board_page.navigate(board["id"])
    board_page.open_delete_confirmation()
    board_page.cancel_delete()

    expect(board_page.delete_confirm_popup).not_to_be_visible()

    # confirm, that the board is NOT deleted
    response = get_board(e2e_api_url, api_session, board["id"], token=access_token)

    assert response.status_code == 200


@pytest.mark.regression
@pytest.mark.e2e
def test_deleted_board_disappears_from_home(
    logged_in_page: Page,
    e2e_api_url: str,
    api_session: requests.Session,
    access_token: str,
) -> None:
    board = post_create_board(
        e2e_api_url, api_session, "Board To Delete", token=access_token
    ).json()

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
    e2e_api_url: str,
    api_session: requests.Session,
    access_token: str,
    make_user_with_token: Callable[..., dict[str, str]],
    make_logged_in_page: Callable[[str], Page],
) -> None:
    member = make_user_with_token()
    board = post_create_board(
        e2e_api_url, api_session, "Shared Board", token=access_token
    ).json()
    add_user_to_board(
        e2e_api_url, api_session, board["id"], member["email"], token=access_token
    )

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
