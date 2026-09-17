"""Page object of the SHP Billing page."""

from __future__ import annotations

import logging

from playwright.sync_api import Page

from framework.locators.billing_locators import BillingLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class BillingPage(BasePage):
    # PATH is not set: the page is only reached through the sidebar, and its route is not verified yet.

    FULL_TABLE_VIEWPORT = {"width": 1600, "height": 900}
    """Viewport wide enough for every column, as on Manage Channel (D26), whose table component this page shares."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = BillingLocators(page)

    def show_full_table(self) -> None:
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)

    def open_from_sidebar(self) -> None:
        """Open the page the way a user does: "My Account" in the sidebar, then "Billing"."""
        self.click(self.locators.sidebar_my_account_menu, "'My Account' sidebar menu")
        self.click(self.locators.sidebar_billing_entry, "'Billing' sub-menu entry")
