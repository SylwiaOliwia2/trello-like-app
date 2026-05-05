import re

from playwright.sync_api import Page, expect

from e2e.POM.register import RegisterPage


def test_login_link_redirects_to_login_page(page: Page) -> None:
    register_page = RegisterPage(page)
    register_page.navigate()
    register_page.click_login_link()
    expect(page).to_have_url(re.compile(".*login"))
