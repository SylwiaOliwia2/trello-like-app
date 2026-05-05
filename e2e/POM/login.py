import os

from playwright.sync_api import Page

from e2e.POM.home import HomePage

class LoginPage:
    def __init__(self, page):
        self.page = page
        self.email_input = page.locator('[data-testid="login-email"]')
        self.password_input = page.locator('[data-testid="login-password"]')
        self.login_button = page.locator('[data-testid="login-submit"]')
        self.register_link = page.locator('[data-testid="go-to-register"]')

    def navigate(self):
        base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173").rstrip("/")
        self.page.goto(f"{base_url}/login")

    def provide_email(self, email):
        self.email_input.fill(email)

    def provide_password(self, password):
        self.password_input.fill(password)

    def click_login(self):
        self.login_button.click()

    def click_register_link(self):
        self.register_link.click()

    def login_no_MFA(self, email, password):
        self.provide_email(email)
        self.provide_password(password)
        self.click_login()
        return HomePage(self.page)