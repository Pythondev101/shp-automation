"""Locators of the SHP Order Logs → Order Processing page (``/order-logs/processing``).

Verified against the live page on 2026-09-22. The filter labels are not linked to their
controls, so each control is found as the one following its label. Order data is
deliberately not part of any locator.
"""

from __future__ import annotations

import re
from datetime import date

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/order-logs/processing$")
LIST_API_PATH = "/api/v1/order-logs/processing"
"""The request Search, Reset and the first load send for the table rows."""

NO_RECORDS_MESSAGE = "No records found."

COLUMN_HEADERS = (
    "S.No",
    "Status",
    "Order ID",
    "Order Status",
    "Total",
    "Buyer",
    "Qty",
    "Part #",
    "Order Date",
)
"""Every column header of the table, in the order the page renders them."""


class OrderProcessingLocators:
    """Every element the Order Processing tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: "Order Logs" is an accordion button whose nested list holds "Order Processing" and "Order Tracking".
        # Its name starts with an icon glyph, so it is a substring match.
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_button: Locator = sidebar_menu.get_by_role("button", name="Order Logs")
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(has=page.get_by_role("button", name="Order Logs"))
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.order_processing_link: Locator = self.sidebar_submenu.get_by_role(
            "link", name="Order Processing", exact=True
        )

        # Page header area.
        self.page_heading: Locator = self._main.get_by_role("heading", name="Order Processing Logs", exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")

        # Search / filter section.
        self.order_status_select: Locator = self._labelled("Order Status", "select")
        # The visible date field; flatpickr keeps a hidden copy that has no role.
        self.date_range_input: Locator = self._main.get_by_role("textbox", name="Choose date range", exact=True)
        self.buyer_input: Locator = self._labelled("Buyer", "input")
        self.part_number_input: Locator = self._labelled("Part #", "input")
        self.order_id_input: Locator = self._labelled("Order ID", "input")
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)
        # The flatpickr calendar renders outside the page and marks the open one with a class only.
        self._open_calendar: Locator = page.locator(".flatpickr-calendar.open")

        # Table and its "Show <n> entries" control, an unnamed select after the text "Show".
        self.show_entries_select: Locator = self._main.get_by_text("Show", exact=True).locator(
            "xpath=following::select[1]"
        )
        self.table: Locator = self._main.get_by_role("table").filter(
            has=page.get_by_role("columnheader", name=_header_name("Order ID"))
        )
        self.no_records_message: Locator = self.table.get_by_role("cell", name=NO_RECORDS_MESSAGE, exact=True)
        self.body_rows: Locator = self.table.locator("tbody tr")
        """Every body row, including the empty-state row."""
        self.data_rows: Locator = self.body_rows.filter(
            has_not=page.get_by_role("cell", name=NO_RECORDS_MESSAGE, exact=True)
        )

    def _labelled(self, label: str, tag: str) -> Locator:
        # Only the label: "Order Status" and "Order ID" are also column headers.
        label_element = self._main.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(label)}\s*$"))
        return label_element.locator(f"xpath=following-sibling::{tag}[1]")

    def column_header(self, name: str) -> Locator:
        return self.table.get_by_role("columnheader", name=_header_name(name))

    def column_cells(self, header: str) -> Locator:
        """The ``header`` cells of every data row; cells have no name, so the column is addressed by position."""
        return self.data_rows.locator(f"td:nth-child({COLUMN_HEADERS.index(header) + 1})")

    def calendar_day(self, day: date) -> Locator:
        """A day of the open Date Range calendar, named like "September 14, 2026"."""
        return self._open_calendar.get_by_label(f"{day:%B} {day.day}, {day.year}", exact=True)


def _header_name(name: str) -> re.Pattern[str]:
    """A column header's name. Since 2026-09-25 sortable headers end with a sort glyph ("⇅", or "▼" / "▲"
    on the sorted column), which is allowed; "Order ID" still does not match "Order ID Extra"."""
    return re.compile(rf"^{re.escape(name)}\W*$")
