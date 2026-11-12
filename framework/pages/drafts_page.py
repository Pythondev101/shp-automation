"""Page object of the SHP Listing → Drafts page."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from playwright.sync_api import Page, Response

from framework.locators.drafts_locators import LIST_API_PATH, PAGE_URL, DraftsLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DraftsPage(BasePage):
    FULL_TABLE_VIEWPORT = {"width": 2560, "height": 900}
    """Wide enough for all 15 columns to render side by side."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = DraftsLocators(page)
        self.last_list_response: Response | None = None
        """The latest table request the page answered: first load or Show entries."""

    def open_from_sidebar(self) -> None:
        """Expand "Listing" (only while collapsed: clicking it again collapses it) and open its "Drafts" link."""
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'Listing' sidebar menu")
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.drafts_link, "'Drafts' Listing sub-menu link")
        self.last_list_response = response.value
        self.page.wait_for_url(PAGE_URL)
        # The body always ends up with a row: data or the empty-state message.
        self.locators.body_rows.first.wait_for()

    def entries_options(self) -> list[str]:
        return [label.strip() for label in self.locators.show_entries_select.locator("option").all_inner_texts()]

    def show_entries(self, count: str) -> None:
        """Choose a page size and wait for the table request it sends."""
        logger.info("Select %r in Show entries", count)
        with self.page.expect_response(self._is_list_response) as response:
            self.locators.show_entries_select.select_option(label=count)
        self.last_list_response = response.value

    def sort_by(self, header: str) -> None:
        """Click a sortable column header; the page sorts the loaded rows itself, without a request."""
        self.click(self.locators.column_header(header), f"'{header}' column header")

    def sort_indicator(self, header: str) -> str:
        return self.locators.column_header(header).inner_text().strip()[-1]

    def column_values(self, header: str) -> list[str]:
        return [text.strip() for text in self.locators.column_cells(header).all_inner_texts()]

    def select_first_row(self) -> None:
        logger.info("Tick the first draft row")
        self.locators.row_checkboxes.first.check()

    def select_all_rows(self) -> None:
        logger.info("Tick the select-all checkbox")
        self.locators.select_all_checkbox.check()

    def clear_selection(self) -> None:
        self.click(self.locators.clear_selection_button, "'Clear' selection button")

    def open_help(self) -> None:
        self.click(self.locators.help_button, "'Help' button")

    @staticmethod
    def _is_list_response(response: Response) -> bool:
        return urlparse(response.url).path == LIST_API_PATH and response.request.method == "GET"
