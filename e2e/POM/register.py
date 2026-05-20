import os


class RegisterPage:
    def __init__(self, page):
        self.page = page
        self.email_input = page.locator('[data-testid="register-email"]')
        self.password_input = page.locator('[data-testid="register-password"]')
        self.confirm_password_input = page.locator(
            '[data-testid="register-password-confirm"]'
        )
        self.register_button = page.locator('[data-testid="register-submit"]')
        self.mfa_enabled_checkbox = page.locator('[data-testid="register-mfa-enabled"]')
        self.login_link = page.locator('[data-testid="go-to-login"]')

    def navigate(self):
        base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173").rstrip("/")
        self.page.goto(f"{base_url}/register")

    def provide_email(self, email):
        self.email_input.fill(email)

    def provide_password(self, password):
        self.password_input.fill(password)

    def confirm_password(self, password):
        self.confirm_password_input.fill(password)

    def click_register(self):
        self.register_button.click()

    def enable_MFA(self):
        self.mfa_enabled_checkbox.check()

    def click_login_link(self):
        self.login_link.click()

    def register_no_MFA(self, email, password):
        self.provide_email(email)
        self.provide_password(password)
        self.confirm_password(password)
        self.click_register()
