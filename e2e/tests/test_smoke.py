from __future__ import annotations

from playwright.sync_api import Page, expect


def test_app_header_and_api_health(page: Page, api_base_url: str) -> None:
    # TODO: replace it with real, valuable tests
    page.goto("/login")
    expect(page.get_by_test_id("app-header")).to_have_text("Task Manager App")

    response = page.request.get(f"{api_base_url}/health")
    expect(response).to_be_ok()
    assert response.json() == {"status": "ok"}
