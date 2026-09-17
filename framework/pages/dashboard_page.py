"""Page object of the SHP dashboard, the page a successful sign-in lands on."""

from __future__ import annotations

from playwright.sync_api import Page

from framework.locators.dashboard_locators import DashboardLocators
from framework.pages.base_page import BasePage


class DashboardPage(BasePage):
    PATH = "/dashboard"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = DashboardLocators(page)

    def sign_out(self) -> None:
        """Sign out through the header profile menu; the header is on every signed-in page."""
        self.click(self.locators.profile_button, "header profile button")
        self.click(self.locators.sign_out_button, "'Sign out' in the profile menu")
