import re

from playwright.sync_api import Page, expect

from e2e.POM.login import LoginPage


def test_register_button_redirects_to_register_page(page: Page) -> None:
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.click_register_link()
    expect(page).to_have_url(re.compile(".*register"))
