import os
from playwright.sync_api import Locator, Page


class HomePage:
    def __init__(self, page: Page):
        self.page = page
        self.logout_button = page.locator('[data-testid="logout-button"]')
        self.title = page.locator('[data-testid="home-title"]')
        self.create_board_button = page.locator('[data-testid="create-board-submit"]')
        self.board_name_input = page.locator('[data-testid="create-board-name"]')
        self.boards_list = page.locator('[data-testid="boards-list"]')

    def navigate(self):
        base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173").rstrip("/")
        self.page.goto(f"{base_url}/home")

    def click_logout(self):
        self.logout_button.click()

    def create_board(self, board_name):
        self.board_name_input.fill(board_name)
        self.create_board_button.click()

    def board_link(self, board_id: int) -> Locator:
        return self.boards_list.locator(f'[data-testid="board-link-{board_id}"]')
