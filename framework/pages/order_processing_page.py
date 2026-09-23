"""Page object of the SHP Order Logs → Order Processing page."""

from __future__ import annotations

import logging
from datetime import date

from playwright.sync_api import Page, Response

from framework.locators.order_processing_locators import LIST_API_PATH, PAGE_URL, OrderProcessingLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class OrderProcessingPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = OrderProcessingLocators(page)
        self.last_list_response: Response | None = None
        """The latest table request the page answered: first load, Search or Reset."""

    def open_from_sidebar(self) -> None:
        """Expand "Order Logs" and open its "Order Processing" link.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'Order Logs' sidebar menu")
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.order_processing_link, "'Order Processing' Order Logs sub-menu link")
        self.last_list_response = response.value
        self.page.wait_for_url(PAGE_URL)

    def status_options(self) -> list[str]:
        """Labels of the Order Status dropdown except the default "All"; empty while SHP has no status."""
        labels = [label.strip() for label in self.locators.order_status_select.locator("option").all_inner_texts()]
        return [label for label in labels if label != "All"]

    def select_order_status(self, label: str) -> None:
        logger.info("Select %r in Order Status filter", label)
        self.locators.order_status_select.select_option(label=label)

    def choose_date_range(self, start: date, end: date) -> None:
        """Pick ``start`` and then ``end`` in the Date Range calendar; the same day twice selects one day."""
        self.click(self.locators.date_range_input, "Date Range field")
        self.click(self.locators.calendar_day(start), f"calendar day {start:%Y-%m-%d}")
        self.click(self.locators.calendar_day(end), f"calendar day {end:%Y-%m-%d}")

    def apply_filters(self) -> None:
        """Press Search and wait for the table request it sends."""
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.search_button, "Search button")
        self.last_list_response = response.value

    def reset_filters(self) -> None:
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.reset_button, "Reset button")
        self.last_list_response = response.value

    @staticmethod
    def _is_list_response(response: Response) -> bool:
        return LIST_API_PATH in response.url and response.request.method == "GET"
