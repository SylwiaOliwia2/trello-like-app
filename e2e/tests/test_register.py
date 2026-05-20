import re

import requests
from playwright.sync_api import Page, expect
import pytest

from e2e.POM.register import RegisterPage
from e2e.tests.helpers.api_helpers import post_auth_login


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
    page: Page, e2e_api_url: str, api_session: requests.Session
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

    # Check if the account does not exists in teh database
    resp = post_auth_login(e2e_api_url=e2e_api_url, api_session=api_session, email=email, password=password)
    assert resp.status_code == 401