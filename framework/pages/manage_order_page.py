"""Page object of the SHP Manage Order page ("All Orders" view)."""

from __future__ import annotations

import logging

from playwright.sync_api import Page

from framework.locators.manage_order_locators import PAGE_URL, ManageOrderLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ManageOrderPage(BasePage):
    FULL_TABLE_VIEWPORT = {"width": 2560, "height": 900}
    """Narrower pages fold the last columns into "+" rows (at 1280 px only 9 of the 16 headers render)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = ManageOrderLocators(page)

    def show_full_table(self) -> None:
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)

    def open_all_orders_from_sidebar(self) -> None:
        """Expand "Manage Order" and open its "All Orders" link.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'Manage Order' sidebar menu")
        self.click(self.locators.all_orders_link, "'All Orders' Manage Order sub-menu link")
        # The dashboard stays in the DOM until the route changes, so the tests start only once it has.
        self.page.wait_for_url(PAGE_URL)
