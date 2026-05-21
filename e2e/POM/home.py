import os
from playwright.sync_api import Page


class HomePage:
    def __init__(self, page: Page):
        self.page = page
        self.logout_button = page.locator('[data-testid="logout-button"]')
        self.title = page.locator('[data-testid="home-title"]')

    def navigate(self):
        base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173").rstrip("/")
        self.page.goto(f"{base_url}/home")

    def click_logout(self):
        self.logout_button.click()
