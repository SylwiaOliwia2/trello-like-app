from playwright.sync_api import Page, expect
import re
import pytest
from e2e.POM.home import HomePage


@pytest.mark.smoke
@pytest.mark.security
@pytest.mark.e2e
def test_session_terminates_after_logout(logged_in_page: Page) -> None:
    page = logged_in_page
    home_page = HomePage(page)
    home_page.navigate()

    access_token = page.evaluate("() => window.localStorage.getItem('auth_token')")
    assert access_token is not None

    home_page.click_logout()

    expect(page).to_have_url(re.compile(".*login"))

    access_token = page.evaluate("() => window.localStorage.getItem('auth_token')")
    assert access_token is None
