"""Page object of the SHP Listing → Common Listing page."""

from __future__ import annotations

import logging
from datetime import date
from urllib.parse import urlparse

from playwright.sync_api import Locator, Page, Response

from framework.locators.common_listing_locators import (
    CHANNELS_API_PATH,
    EMPTY_CELL,
    LIST_API_PATH,
    PAGE_URL,
    CommonListingLocators,
)
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class CommonListingPage(BasePage):
    FULL_TABLE_VIEWPORT = {"width": 2560, "height": 900}
    """Wide enough for all 17 column headers to render side by side."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = CommonListingLocators(page)
        self.last_list_response: Response | None = None
        """The latest table request the page answered: first load, Search or Reset."""

    def open_from_sidebar(self) -> None:
        """Expand "Listing" and open its "Common Listing" link.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'Listing' sidebar menu")
        # The Channel Filter options arrive in their own request; reading them before it answers finds none.
        with self.page.expect_response(self._is_channels_response), self.page.expect_response(
            self._is_list_response
        ) as response:
            self.click(self.locators.common_listing_link, "'Common Listing' Listing sub-menu link")
        self.last_list_response = response.value
        self.page.wait_for_url(PAGE_URL)

    def open_create_listing_menu(self) -> None:
        self.click(self.locators.create_listing_button, "'Create Listing' button")

    def expand_single_listing(self) -> None:
        """Open the "Single Listing" sub-menu; it reveals "Manual" and "Generate Listing By AI".

        "Single Listing" only toggles the sub-menu, it navigates nowhere.
        """
        self.click(self.locators.single_listing_option, "'Single Listing' Create Listing option")
        self.locators.manual_option.wait_for()

    def choose_manual_single_listing(self) -> None:
        """Pick "Manual" in the open Single Listing sub-menu; it opens the Add New Listing page."""
        self.click(self.locators.manual_option, "'Manual' Single Listing option")

    @staticmethod
    def option_labels(select: Locator) -> list[str]:
        """Labels of a filter dropdown except its first, default option ("All Channels" / "All")."""
        return [label.strip() for label in select.locator("option").all_inner_texts()[1:]]

    def select_option(self, select: Locator, label: str, description: str) -> None:
        logger.info("Select %r in %s", label, description)
        select.select_option(label=label)

    def first_value(self, header: str) -> str | None:
        """The first non-empty ``header`` value of the visible rows, or None when no row has one."""
        for text in self.locators.column_cells(header).all_inner_texts():
            if text.strip() and text.strip() != EMPTY_CELL:
                return text.strip()
        return None

    def choose_published_date_range(self, start: date, end: date) -> None:
        """Pick ``start`` and then ``end`` in the By Published Date calendar; the same day twice selects one day."""
        self.click(self.locators.published_date_input, "By Published Date field")
        self.click(self.locators.calendar_day(start), f"calendar day {start:%Y-%m-%d}")
        self.click(self.locators.calendar_day(end), f"calendar day {end:%Y-%m-%d}")

    def apply_filters(self) -> None:
        """Press Search and wait for the request it sends (it sends none while the filters are unchanged)."""
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.search_button, "Search button")
        self.last_list_response = response.value

    def reset_filters(self) -> None:
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.reset_button, "Reset button")
        self.last_list_response = response.value

    @staticmethod
    def _is_channels_response(response: Response) -> bool:
        return urlparse(response.url).path == CHANNELS_API_PATH and response.request.method == "GET"

    @staticmethod
    def _is_list_response(response: Response) -> bool:
        return urlparse(response.url).path == LIST_API_PATH and response.request.method == "GET"
