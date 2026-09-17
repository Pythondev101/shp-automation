"""Page object of the SHP Active Listing page (one channel's product list)."""

from __future__ import annotations

import logging

from playwright.sync_api import Page

from framework.locators.active_listing_locators import ActiveListingLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ActiveListingPage(BasePage):
    # PATH is not set: the route holds the channel's platform and id, so the page is reached through the sidebar.

    FULL_TABLE_VIEWPORT = {"width": 2560, "height": 900}
    """Below this width the table removes its last columns from the DOM (18 headers render at 2560 px)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = ActiveListingLocators(page)

    def show_full_table(self) -> None:
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)

    def open_first_channel_from_sidebar(self) -> str:
        """Expand "Active Listing" and open the first channel it lists; returns that channel's name.

        The channel is not hard-coded, so the test keeps working when channels are renamed or added.
        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'Active Listing' sidebar menu")
        channel = self.locators.first_channel_link.inner_text().strip()
        self.click(self.locators.first_channel_link, f"'{channel}' Active Listing sub-menu link")
        return channel
