from typing import Callable

from playwright.sync_api import Page, expect
import re
import pytest
from e2e.POM.home import HomePage


@pytest.mark.smoke
@pytest.mark.security
@pytest.mark.e2e
def test_session_terminates_after_logout(
    make_user_with_token: Callable[..., dict[str, str]],
    make_logged_in_page: Callable[[str], Page],
) -> None:
    user = make_user_with_token()
    page = make_logged_in_page(user["token"])
    home_page = HomePage(page)
    home_page.navigate()

    access_token = page.evaluate("() => window.localStorage.getItem('auth_token')")
    assert access_token is not None

    home_page.click_logout()

    expect(page).to_have_url(re.compile(".*login"))

    access_token = page.evaluate("() => window.localStorage.getItem('auth_token')")
    assert access_token is None
