import os
import json
import uuid
from typing import Callable, Generator
from urllib.parse import parse_qs, urlparse

import pytest
import pyotp
from playwright.sync_api import APIRequestContext, APIResponse, Browser, Page

from e2e.POM.home import HomePage
from e2e.tests.helpers.db_cleanup import delete_user


def _register_page_for_screenshots(request: pytest.FixtureRequest, page: Page) -> None:
    """Track a page on the test node so the failure hook can screenshot it."""
    pages = getattr(request.node, "pages", None)
    if pages is None:
        pages = []
        request.node.pages = pages
    pages.append(page)


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


@pytest.fixture()
def make_user(
    api_request_context: APIRequestContext,
) -> Generator[Callable[..., dict[str, str]], None, None]:
    """Register users via API; delete them (in reverse) on teardown."""
    created_ids: list[int] = []

    def _make_user(password: str = "StrongPass123!") -> dict[str, str]:
        email = f"e2e_{uuid.uuid4().hex}@example.com"
        resp = api_request_context.post(
            "/auth/register",
            data={"email": email, "password": password, "mfa_enabled": False},
        )
        if not resp.ok:
            raise RuntimeError(f"Register failed: {resp.status} {resp.text()}")
        user_id = resp.json().get("id")
        if user_id is None:
            raise RuntimeError(
                f"Expected user id in register response, got: {resp.json()}"
            )
        created_ids.append(int(user_id))
        return {"id": str(user_id), "email": email, "password": password}

    yield _make_user

    for user_id in reversed(created_ids):
        delete_user(user_id)


@pytest.fixture()
def make_user_with_token(
    make_user: Callable[..., dict[str, str]],
    api_request_context: APIRequestContext,
) -> Generator[Callable[..., dict[str, str]], None, None]:
    """Register + login users; user rows are cleaned up by `make_user` teardown."""

    def _make_user_with_token(password: str = "StrongPass123!") -> dict[str, str]:
        user = make_user(password=password)
        resp = api_request_context.post(
            "/auth/login",
            data={
                "email": user["email"],
                "password": user["password"],
                "otp": None,
            },
        )
        if not resp.ok:
            raise RuntimeError(f"Login failed: {resp.status} {resp.text()}")
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError(f"Expected access_token in response, got: {resp.json()}")
        return {**user, "token": str(token)}

    yield _make_user_with_token


@pytest.fixture()
def make_mfa_user(
    api_request_context: APIRequestContext,
) -> Generator[Callable[..., dict[str, str]], None, None]:
    """Register MFA users via API; delete them (in reverse) on teardown."""
    created_ids: list[int] = []

    def _make_mfa_user(password: str = "StrongPass123!") -> dict[str, str]:
        email = f"e2e_mfa_{uuid.uuid4().hex}@example.com"
        resp = api_request_context.post(
            "/auth/register",
            data={"email": email, "password": password, "mfa_enabled": True},
        )
        if not resp.ok:
            raise RuntimeError(f"Register failed: {resp.status} {resp.text()}")
        data = resp.json()
        otpauth_url = str(data.get("mfa_otpauth_url") or "")
        parsed = urlparse(otpauth_url)
        secret = parse_qs(parsed.query).get("secret", [""])[0]
        if not secret:
            raise RuntimeError(f"Expected secret in mfa_otpauth_url, got: {data}")
        otp = pyotp.TOTP(secret).now()

        confirm_resp = api_request_context.post(
            "/auth/register/confirm",
            data={
                "registration_token": data.get("registration_token"),
                "otp": otp,
            },
        )
        if not confirm_resp.ok:
            raise RuntimeError(
                f"MFA confirm failed: {confirm_resp.status} {confirm_resp.text()}"
            )
        user_id = confirm_resp.json().get("id")
        if user_id is None:
            raise RuntimeError(
                f"Expected user id in confirm response, got: {confirm_resp.json()}"
            )
        created_ids.append(int(user_id))
        return {
            "id": str(user_id),
            "email": email,
            "password": password,
            "mfa_otpauth_url": otpauth_url,
        }

    yield _make_mfa_user

    for user_id in reversed(created_ids):
        delete_user(user_id)


@pytest.fixture()
def make_logged_in_page(
    request: pytest.FixtureRequest,
    browser: Browser,
) -> Generator[Callable[[str], Page], None, None]:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173")
    contexts = []

    def _make_logged_in_page(token: str) -> Page:
        context = browser.new_context(base_url=base_url)
        context.set_default_timeout(10_000)
        context.set_default_navigation_timeout(10_000)
        token_js = json.dumps(token)
        context.add_init_script(
            f'window.localStorage.setItem("auth_token", {token_js});'
        )
        contexts.append(context)
        new_page = context.new_page()
        _register_page_for_screenshots(request, new_page)

        home_page = HomePage(new_page)
        home_page.navigate()
        home_page.title.wait_for()
        return new_page

    yield _make_logged_in_page

    for context in contexts:
        context.close()
