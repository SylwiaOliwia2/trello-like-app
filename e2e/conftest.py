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
    APIResponse,
)
import requests

from e2e.POM.home import HomePage

pytest_plugins = [
    "e2e.tests.fixtures.board_fixtures",
    "e2e.tests.fixtures.login_fixtures",
]


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


def _register_page_for_screenshots(request: pytest.FixtureRequest, page: Page) -> None:
    pages = getattr(request.node, "pages", None)
    if pages is None:
        pages = []
        request.node.pages = pages
    pages.append(page)


@pytest.fixture(scope="function")
def page(
    request: pytest.FixtureRequest, browser: Browser
) -> Generator[Page, None, None]:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173")
    context = browser.new_context(base_url=base_url)
    context.set_default_timeout(10_000)
    context.set_default_navigation_timeout(10_000)
    test_page = context.new_page()
    _register_page_for_screenshots(request, test_page)
    yield test_page
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or report.passed:
        return

    pages = getattr(item, "pages", None) or []
    if not pages:
        return

    screenshots_dir = Path("e2e/artifacts/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    for index, page in enumerate(pages):
        screenshot_name = f"{item.name}_{index}_{uuid.uuid4()}.png".replace(
            "/", "_"
        ).replace(" ", "_")
        try:
            page.screenshot(path=str(screenshots_dir / screenshot_name), full_page=True)
        except Exception:
            # page/context may already be closed - skip it
            pass


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
    make_user: Callable[..., dict[str, str]],
    api_login: Callable[..., APIResponse],
) -> Callable[..., dict[str, str]]:
    def _make_user_with_token(password: str = "StrongPass123!") -> dict[str, str]:
        user = make_user(password=password)
        resp = api_login(user["email"], user["password"])
        if not resp.ok:
            raise RuntimeError(f"Login failed: {resp.status} {resp.text()}")
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError(f"Expected access_token in response, got: {resp.json()}")
        return {**user, "token": str(token)}

    return _make_user_with_token


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
