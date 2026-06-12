import re
from urllib.parse import parse_qs, urlparse
import requests
from playwright.sync_api import Page, expect
import pytest
import pyotp

from e2e.POM.login import LoginPage
from e2e.POM.home import HomePage


@pytest.mark.regression
@pytest.mark.e2e
def test_register_button_redirects_to_register_page(page: Page) -> None:
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.click_register_link()
    expect(page).to_have_url(re.compile(".*register"))


@pytest.mark.regression
@pytest.mark.e2e
def test_wrong_email_format_displays_error_message(page: Page) -> None:
    login_page = LoginPage(page)
    login_page.navigate()
    assert login_page.email_input.get_attribute("type") == "email"
    assert login_page.email_input.get_attribute("required") is not None


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.e2e
def test_login_password_is_masked(page: Page) -> None:
    login_page = LoginPage(page)
    login_page.navigate()

    assert login_page.password_input.get_attribute("type") == "password"


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.e2e
def test_not_authenticated_user_cannot_access_home_page(
    page: Page, e2e_api_url: str, api_session: requests.Session
) -> None:
    home_page = HomePage(page)
    home_page.navigate()

    expect(page).to_have_url(re.compile(".*login"))


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.e2e
def test_session_token_is_stored_after_succesfull_login(
    page: Page, registered_user: dict[str, str]
) -> None:
    login_page = LoginPage(page)
    login_page.navigate()

    access_token = page.evaluate("() => window.localStorage.getItem('auth_token')")
    assert access_token is None

    login_page.provide_email(registered_user["email"])
    login_page.provide_password(registered_user["password"])
    login_page.click_login()

    expect(page).to_have_url(re.compile(".*home"))

    access_token = page.evaluate("() => window.localStorage.getItem('auth_token')")
    assert access_token is not None


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.e2e
def test_wrong_password_does_not_allow_to_login(page: Page, registered_user) -> None:
    login_page = LoginPage(page)
    login_page.navigate()

    login_page.provide_email(registered_user["email"])
    login_page.provide_password("WRONG_PASSWORD")
    login_page.click_login()

    expect(page).to_have_url(re.compile(".*login"))
    expect(page.get_by_text(re.compile(r".*invalid.*", re.IGNORECASE))).to_be_visible()


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.e2e
def test_MFA_is_required_for_MFA_users(
    page: Page, registered_mfa_user: dict[str, str]
) -> None:
    login_page = LoginPage(page)
    login_page.navigate()

    login_page.provide_email(registered_mfa_user["email"])
    login_page.provide_password(registered_mfa_user["password"])
    login_page.click_login()

    expect(login_page.otp_input).to_be_visible()
    assert login_page.otp_input.get_attribute("required") is not None


@pytest.mark.regression
@pytest.mark.security
@pytest.mark.e2e
def test_mfa_user_is_prompted_for_mfa_on_every_login(
    page: Page, registered_mfa_user: dict[str, str]
):
    # login
    login_page = LoginPage(page)
    login_page.navigate()

    login_page.provide_email(registered_mfa_user["email"])
    login_page.provide_password(registered_mfa_user["password"])
    login_page.click_login()

    parsed = urlparse(registered_mfa_user["mfa_otpauth_url"])
    secret = parse_qs(parsed.query).get("secret", [""])[0]
    assert secret, "Missing TOTP secret in mfa_otpauth_url"
    otp = pyotp.TOTP(secret).now()

    login_page.otp_input.fill(otp)
    login_page.click_login()

    expect(page).to_have_url(re.compile(".*home"))

    # logout
    home_page = HomePage(page)

    home_page.click_logout()

    expect(page).to_have_url(re.compile(".*login"))

    # login again - should display MFA field again
    login_page = LoginPage(page)
    login_page.navigate()

    login_page.provide_email(registered_mfa_user["email"])
    login_page.provide_password(registered_mfa_user["password"])
    login_page.click_login()

    expect(login_page.otp_input).to_be_visible()
    assert login_page.otp_input.get_attribute("required") is not None
