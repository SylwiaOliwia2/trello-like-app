import os
from pathlib import Path
from typing import Generator
import uuid

import pytest
from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    sync_playwright,
    APIRequestContext,
)

from e2e.tests.fixtures.login_fixtures import _register_page_for_screenshots

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


@pytest.fixture(scope="function")
def page(
    request: pytest.FixtureRequest, browser: Browser
) -> Generator[Page, None, None]:
    # NOTE: shall we ui=nify it with make_logged_in_page?
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
