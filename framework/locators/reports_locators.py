"""Locators of the SHP Reports page (``/reports``), Order Report tab.

Verified against the live page on 2026-09-22. The filter controls carry an ``aria-label``;
the table headers carry a sort glyph (e.g. "Channel⇅", "Request Date▼"), so headers are
matched by prefix. Report data is deliberately not part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/reports$")
ORDER_REPORT_API_PATH = "/api/v1/reports/orders"
"""The request the first load, Search and Reset send for the Order Report rows."""

NO_RESULTS_MESSAGE = "No results match your filters"
EMPTY_CELL = "—"
"""What a cell shows when the report request has no value for that column."""

REPORT_TABS = ("Order Report", "Inventory Report", "Listing Report", "Stock Report")

COLUMN_HEADERS = (
    "S.No",
    "Channel",
    "Order Status",
    "By Order Date",
    "By Creation Date",
    "Buyer Name",
    "Part Number",
    "Order Id",
    "Request Date",
    "Download",
)
"""Every Order Report column header, in the order the page renders them."""


class ReportsLocators:
    """Every element the Order Report tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        main = page.get_by_role("main")
        # The link name starts with an icon glyph, so it is a substring match.
        self.sidebar_reports_link: Locator = page.get_by_role("complementary").get_by_role("link", name="Reports")

        # Page header area; Help and Request Report names start with an icon glyph.
        self.page_heading: Locator = main.get_by_role("heading", name="Reports", exact=True)
        self.breadcrumb: Locator = main.get_by_role("navigation", name="breadcrumb")
        self.help_button: Locator = main.get_by_role("button", name="Help")
        self.request_report_button: Locator = main.get_by_role("button", name="Request Report")
        self._tab_list: Locator = main.get_by_role("list").filter(
            has=page.get_by_role("button", name="Order Report", exact=True)
        )

        # Search / filter section.
        self.channel_select: Locator = main.get_by_role("combobox", name="Channel", exact=True)
        self.order_status_select: Locator = main.get_by_role("combobox", name="Order Status", exact=True)
        self.buyer_name_input: Locator = main.get_by_role("textbox", name="Buyer Name", exact=True)
        self.part_number_input: Locator = main.get_by_role("textbox", name="Part#", exact=True)
        self.order_id_input: Locator = main.get_by_role("textbox", name="Order ID", exact=True)
        self.search_button: Locator = main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = main.get_by_role("button", name="Reset", exact=True)
        self.show_entries_select: Locator = main.get_by_role("combobox", name="Entries per page", exact=True)

        # Table.
        self.table: Locator = main.get_by_role("table").filter(
            has=page.get_by_role("columnheader", name=re.compile(r"^Request Date"))
        )
        self.no_results_message: Locator = self.table.get_by_text(NO_RESULTS_MESSAGE)
        self.body_rows: Locator = self.table.locator("tbody tr")
        """Every body row, including the empty-state row."""
        self.data_rows: Locator = self.body_rows.filter(has_not_text=NO_RESULTS_MESSAGE)

        # Footer.
        self.showing_entries_text: Locator = main.get_by_text(re.compile(r"^Showing \d+ to \d+ of \d+ entries$"))
        pagination = main.get_by_role("navigation", name="Pagination")
        self.previous_button: Locator = pagination.get_by_role("button", name="Previous", exact=True)
        self.page_number_button: Locator = pagination.get_by_role("button", name=re.compile(r"^\d+$")).first
        self.next_button: Locator = pagination.get_by_role("button", name="Next", exact=True)

    def report_tab(self, name: str) -> Locator:
        return self._tab_list.get_by_role("button", name=name, exact=True)

    def column_header(self, name: str) -> Locator:
        return self.table.get_by_role("columnheader", name=re.compile(rf"^{re.escape(name)}\W*$"))

    def column_cells(self, header: str) -> Locator:
        """The ``header`` cells of every data row; cells have no name, so the column is addressed by position."""
        return self.data_rows.locator(f"td:nth-child({COLUMN_HEADERS.index(header) + 1})")
