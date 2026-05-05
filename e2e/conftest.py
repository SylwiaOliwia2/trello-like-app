import os
from pathlib import Path
from typing import Generator
import uuid

import pytest
from playwright.sync_api import Browser, Page, Playwright, sync_playwright


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
def page(request: pytest.FixtureRequest, browser: Browser) -> Generator[Page, None, None]:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173")
    context = browser.new_context(base_url=base_url)
    context.set_default_timeout(10_000)
    context.set_default_navigation_timeout(10_000)
    test_page = context.new_page()
    request.node.page = test_page # NOTE: this line is required for the pytest hooks
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
    screenshot_name = f"{item.name}_{uuid.uuid4()}.png".replace("/", "_").replace(" ", "_")
    page.screenshot(path=str(screenshots_dir / screenshot_name), full_page=True)
