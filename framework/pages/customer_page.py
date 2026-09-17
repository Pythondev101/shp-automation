"""Page object of the SHP Customer page."""

from __future__ import annotations

import logging

from playwright.sync_api import Page

from framework.locators.customer_locators import CustomerLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class CustomerPage(BasePage):
    # PATH is not set: the page is only reached through the sidebar, and its route is not verified yet.

    FULL_TABLE_VIEWPORT = {"width": 1600, "height": 900}
    """Viewport wide enough for the table's columns, as on Manage Channel (D26)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = CustomerLocators(page)

    def show_full_table(self) -> None:
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)

    def open_from_sidebar(self) -> None:
        """Open the page the way a user does: the "Customer" sidebar entry."""
        self.click(self.locators.sidebar_menu_entry, "'Customer' sidebar menu")
