"""Page object of the SHP Reports page, Order Report tab."""

from __future__ import annotations

import logging
import re

from playwright.sync_api import Locator, Page, Response

from framework.locators.reports_locators import EMPTY_CELL, ORDER_REPORT_API_PATH, PAGE_URL, ReportsLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)

ACTIVE_TAB = re.compile(r"\bactive\b")


class ReportsPage(BasePage):
    FULL_TABLE_VIEWPORT = {"width": 2560, "height": 900}
    """Narrower viewports fold the last columns into a "+" expand row and shift the cells."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = ReportsLocators(page)
        self.last_list_response: Response | None = None
        """The latest Order Report request the page answered: first load, Search or Reset."""

    def open_from_sidebar(self) -> None:
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.sidebar_reports_link, "'Reports' sidebar link")
        self.last_list_response = response.value
        self.page.wait_for_url(PAGE_URL)

    def open_order_report_tab(self) -> None:
        """Open the Order Report tab; it is the default tab, so it is clicked only while another one is active."""
        tab = self.locators.report_tab("Order Report")
        tab.wait_for()
        if ACTIVE_TAB.search(tab.get_attribute("class") or ""):
            return
        with self.page.expect_response(self._is_list_response) as response:
            self.click(tab, "'Order Report' tab")
        self.last_list_response = response.value

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
    def _is_list_response(response: Response) -> bool:
        return ORDER_REPORT_API_PATH in response.url and response.request.method == "GET"
