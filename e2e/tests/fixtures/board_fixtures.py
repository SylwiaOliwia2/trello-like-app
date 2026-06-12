from typing import Callable

import pytest
from playwright.sync_api import APIRequestContext, APIResponse


@pytest.fixture()
def api_create_board(
    api_request_context: APIRequestContext,
) -> Callable[..., APIResponse]:
    def _api_create_board(name: str, token: str | None = None) -> APIResponse:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return api_request_context.post("/boards", data={"name": name}, headers=headers)

    return _api_create_board


@pytest.fixture()
def api_get_board(
    api_request_context: APIRequestContext,
) -> Callable[..., APIResponse]:
    def _api_get_board(board_id: int, token: str | None = None) -> APIResponse:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return api_request_context.get(f"/boards/{board_id}", headers=headers)

    return _api_get_board


@pytest.fixture()
def api_add_board_member(
    api_request_context: APIRequestContext,
) -> Callable[..., APIResponse]:
    def _api_add_board_member(
        board_id: int, email: str, token: str | None = None
    ) -> APIResponse:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return api_request_context.post(
            f"/boards/{board_id}/members", data={"email": email}, headers=headers
        )

    return _api_add_board_member


@pytest.fixture()
def get_board_member_id_by_email(
    api_get_board: Callable[..., APIResponse],
) -> Callable[..., int]:
    def _get_board_member_id_by_email(
        board_id: int, email: str, token: str | None = None
    ) -> int:
        response = api_get_board(board_id, token=token)
        if not response.ok:
            raise RuntimeError(f"Failed to get board {board_id}: {response.status}")
        return next(
            m["user_id"] for m in response.json()["members"] if m["email"] == email
        )

    return _get_board_member_id_by_email
