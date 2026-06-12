from typing import Callable

import pytest
from playwright.sync_api import APIRequestContext, APIResponse


@pytest.fixture()
def api_login(
    api_request_context: APIRequestContext,
) -> Callable[..., APIResponse]:
    def _api_login(email: str, password: str) -> APIResponse:
        return api_request_context.post(
            "/auth/login",
            data={"email": email, "password": password, "otp": None},
        )

    return _api_login
