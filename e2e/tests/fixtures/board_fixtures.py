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
