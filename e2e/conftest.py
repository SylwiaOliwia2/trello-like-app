import os
from pathlib import Path
from typing import Callable, Generator
import uuid
import json
from urllib.parse import parse_qs, urlparse

import pytest
import pyotp
from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    sync_playwright,
    APIRequestContext,
)
import requests

from e2e.POM.home import HomePage
from e2e.tests.helpers.api_login_helpers import post_auth_login
from e2e.tests.fixtures.board_fixtures import (  # noqa: F401
    api_create_board,
    api_get_board,
)


@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Generator[Browser, None, None]:
    headless = os.getenv("E2E_HEADLESS", "true").lower() == "true"
    browser_instance = playwright.chromium.launch(headless=headless)
    yield browser_instance
    browser_instance.close()


@pytest.fixture(scope="function")
def page(
    request: pytest.FixtureRequest, browser: Browser
) -> Generator[Page, None, None]:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173")
    context = browser.new_context(base_url=base_url)
    context.set_default_timeout(10_000)
    context.set_default_navigation_timeout(10_000)
    test_page = context.new_page()
    request.node.page = test_page  # NOTE: this line is required for the pytest hooks
    yield test_page
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or report.passed:
        return

    page = getattr(item, "page", None)
    if page is None:
        return

    screenshots_dir = Path("e2e/artifacts/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshot_name = f"{item.name}_{uuid.uuid4()}.png".replace("/", "_").replace(
        " ", "_"
    )
    page.screenshot(path=str(screenshots_dir / screenshot_name), full_page=True)


@pytest.fixture(scope="session")
def e2e_api_url() -> str:
    return os.getenv("E2E_API_URL", "http://127.0.0.1:8000").rstrip("/")


@pytest.fixture()
def api_session() -> requests.Session:
    return requests.Session()


@pytest.fixture()
def make_user(
    e2e_api_url: str, api_session: requests.Session
) -> Callable[..., dict[str, str]]:
    def _make_user(password: str = "StrongPass123!") -> dict[str, str]:
        email = f"e2e_{uuid.uuid4().hex}@example.com"
        payload = {"email": email, "password": password, "mfa_enabled": False}
        resp = api_session.post(
            f"{e2e_api_url}/auth/register", json=payload, timeout=10
        )
        resp.raise_for_status()
        return {"id": id, "email": email, "password": password}

    return _make_user


@pytest.fixture()
def make_user_with_token(
    e2e_api_url: str,
    api_session: requests.Session,
    make_user: Callable[..., dict[str, str]],
) -> Callable[..., dict[str, str]]:
    def _make_user_with_token(password: str = "StrongPass123!") -> dict[str, str]:
        user = make_user(password=password)
        resp = post_auth_login(
            e2e_api_url=e2e_api_url,
            api_session=api_session,
            email=user["email"],
            password=user["password"],
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError(f"Expected access_token in response, got: {resp.json()}")
        return {**user, "token": str(token)}

    return _make_user_with_token


@pytest.fixture()
def registered_user(
    make_user: Callable[..., dict[str, str]],
) -> dict[str, str]:
    return make_user()


@pytest.fixture()
def registered_mfa_user(
    e2e_api_url: str, api_session: requests.Session
) -> dict[str, str]:
    email = f"e2e_mfa_{uuid.uuid4().hex}@example.com"
    password = "StrongPass123!"
    payload = {"email": email, "password": password, "mfa_enabled": True}
    resp = api_session.post(f"{e2e_api_url}/auth/register", json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    otpauth_url = str(data.get("mfa_otpauth_url") or "")
    parsed = urlparse(otpauth_url)
    secret = parse_qs(parsed.query).get("secret", [""])[0]
    if not secret:
        raise RuntimeError(f"Expected secret in mfa_otpauth_url, got: {data}")
    otp = pyotp.TOTP(secret).now()

    confirm_resp = api_session.post(
        f"{e2e_api_url}/auth/register/confirm",
        json={
            "registration_token": data.get("registration_token"),
            "otp": otp,
        },
        timeout=10,
    )
    confirm_resp.raise_for_status()

    return {
        "email": email,
        "password": password,
        "mfa_otpauth_url": otpauth_url,
    }


@pytest.fixture()
def access_token(
    e2e_api_url: str, api_session: requests.Session, registered_user: dict[str, str]
) -> str:
    resp = api_session.post(
        f"{e2e_api_url}/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
            "otp": None,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Expected access_token in response, got: {data}")
    return str(token)


@pytest.fixture()
def logged_in_page(page: Page, access_token: str) -> Page:
    token_js = json.dumps(access_token)
    page.context.add_init_script(
        f'window.localStorage.setItem("auth_token", {token_js});'
    )

    home_page = HomePage(page)
    home_page.navigate()
    home_page.title.wait_for()
    return page


@pytest.fixture()
def make_logged_in_page(
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

        home_page = HomePage(new_page)
        home_page.navigate()
        home_page.title.wait_for()
        return new_page

    yield _make_logged_in_page

    for context in contexts:
        context.close()


@pytest.fixture(scope="session")
def api_request_context(
    e2e_api_url: str,
    playwright: Playwright,
) -> Generator[APIRequestContext, None, None]:
    request_context = playwright.request.new_context(
        base_url=f"{e2e_api_url}",
    )
    yield request_context
    request_context.dispose()
