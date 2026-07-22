import os
from playwright.sync_api import Page, expect


class BoardPage:
    def __init__(self, page: Page):
        self.page = page
        self.back_button = page.locator('[data-testid="back-to-home"]')
        self.board_name = page.locator('[data-testid="board-name"]')
        self.board_load_error = page.locator('[data-testid="board-load-error"]')
        self.members_list = page.locator('[data-testid="members-list"]')
        self.add_member_button = page.locator('[data-testid="add-member-submit"]')
        self.new_member_dropdown = page.locator('[data-testid="add-member-select"]')
        self.delete_board_button = page.locator('[data-testid="delete-board"]')
        self.leave_board_button = page.locator('[data-testid="leave-board"]')
        self.delete_confirm_popup = page.locator('[data-testid="delete-board-confirm"]')
        self.confirm_delete_button = page.locator(
            '[data-testid="delete-board-confirm-yes"]'
        )
        self.cancel_delete_button = page.locator(
            '[data-testid="delete-board-confirm-no"]'
        )

    def navigate(self, board_id: int):
        base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173").rstrip("/")
        self.page.goto(f"{base_url}/boards/{board_id}")

    def open_delete_confirmation(self):
        self.delete_board_button.click()

    def confirm_delete(self):
        self.confirm_delete_button.click()

    def cancel_delete(self):
        self.cancel_delete_button.click()

    def add_board_member(self, email: str):
        self.new_member_dropdown.select_option(value=email)
        self.add_member_button.click()
        # wait for the member to be added. Otherwise may overlap when adding multiple users one after another.
        expect(self.add_member_button).to_be_disabled()

    def member_item(self, user_id: int):
        return self.page.locator(f'[data-testid="member-item-{user_id}"]')

    def member_role(self, user_id: int):
        return self.page.locator(f'[data-testid="member-role-{user_id}"]')

    def remove_member_button(self, user_id: int):
        return self.page.locator(f'[data-testid="remove-member-{user_id}"]')

    def remove_board_member(self, user_id: int):
        self.remove_member_button(user_id).click()

    def delete_board(self):
        self.open_delete_confirmation()
        self.confirm_delete()

    def remove_myself_from_the_board(self):
        self.leave_board_button.click()
