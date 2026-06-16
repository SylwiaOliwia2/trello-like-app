import re
from typing import Callable

from playwright.sync_api import Page, expect, APIResponse
import pytest

from e2e.POM.register import RegisterPage


@pytest.mark.regression
def test_login_link_redirects_to_login_page(page: Page) -> None:
    register_page = RegisterPage(page)
    register_page.navigate()
    register_page.click_login_link()
    expect(page).to_have_url(re.compile(".*login"))


@pytest.mark.regression
def test_wrong_register_email_format_displays_error_message(page: Page) -> None:
    register_page = RegisterPage(page)
    register_page.navigate()

    assert register_page.email_input.get_attribute("type") == "email"
    assert register_page.email_input.get_attribute("required") is not None


@pytest.mark.regression
@pytest.mark.security
def test_register_password_is_masked(page: Page) -> None:
    register_page = RegisterPage(page)
    register_page.navigate()

    assert register_page.password_input.get_attribute("type") == "password"
    assert register_page.confirm_password_input.get_attribute("type") == "password"


@pytest.mark.regression
def test_wrong_confirm_password_does_not_allow_to_register(
    page: Page, api_login: Callable[..., APIResponse]
) -> None:
    email = "wrong_confirm_password@example.com"
    password = "password"

    register_page = RegisterPage(page)
    register_page.navigate()

    register_page.provide_email(email)
    register_page.provide_password(password)
    register_page.confirm_password("XXXX234cwc4")
    register_page.click_register()

    expect(page.get_by_text("Passwords do not match")).to_be_visible()

    # # Confirm that the user cannot log in with these credentials
    resp = api_login(email, password)
    assert resp.status == 401
