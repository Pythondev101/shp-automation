"""Locators of the SHP Customer page.

Written from the Customer screenshot and the patterns verified on Help Center, whose
filter bar and table component this page shares. Customer data (names, addresses,
phones, order ids) is deliberately not part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_HEADING = "Customer"

COLUMN_HEADERS = (
    "S.No",
    "Channel",
    "Order ID",
    "Buyer User ID",
    "Name",
    "Street 1",
    "Street 2",
    "State/Province",
    "Country",
    "Phone",
    "Postal Code",
    "Address ID",
    "Address Owner",
    "Created",
)
"""Every column header of the customer table, in the order the page renders them."""

ACCESS_LOGGING_TEXT = re.compile(r"access.*\blog|\blog.*access", re.IGNORECASE)
"""The access-logging notice; only its subject is matched, not its exact wording."""

EXPORT_INFO_TEXT = re.compile(r"From.*To.*Export", re.IGNORECASE)
"""The hint that a From and To date must be selected to enable Export."""

EMPTY_STATE_TEXT = re.compile(r"^\s*No\b.*\b(found|available|data|records?)\b", re.IGNORECASE)
"""The table's message row when it holds no customers."""


class CustomerLocators:
    """Every element the Customer tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_entry: Locator = sidebar_menu.get_by_role("link", name="Customer")

        # Page header area. The title may repeat as a card title, so the first heading is taken.
        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING, exact=True).first
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        # The button name may start with an icon glyph, so it is matched as a substring.
        self.export_button: Locator = self._main.get_by_role("button", name="Export")
        self.access_logging_message: Locator = self._main.get_by_text(ACCESS_LOGGING_TEXT).first

        # Filter bar. Labels are unlinked, so each field is the first control after its label (D37 pattern).
        self.customer_name_label: Locator = self._label("Customer Name")
        self.customer_name_input: Locator = self.customer_name_label.locator("xpath=following::input[1]")
        self.order_id_label: Locator = self._label("Order Id")
        self.order_id_input: Locator = self.order_id_label.locator("xpath=following::input[1]")
        self.date_range_input: Locator = self._main.get_by_role("textbox", name="Choose date range", exact=True)
        self.channel_select: Locator = self._label("Channel").locator("xpath=following::select[1]")
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)
        self.export_info_text: Locator = self._main.get_by_text(EXPORT_INFO_TEXT).first

        # Table and its "Show <n> entries" control, an unnamed select after the text "Show".
        self.show_entries_select: Locator = self._main.get_by_text("Show", exact=True).locator(
            "xpath=following::select[1]"
        )
        self.table: Locator = self._main.get_by_role("table")
        self.table_rows: Locator = self.table.locator("tbody tr")
        # A data row has one cell per column; the empty-state message is a single cell spanning the table.
        self.first_row_cells: Locator = self.table_rows.first.locator("td")
        self.loading_row: Locator = self.table_rows.filter(has_text=re.compile(r"loading", re.IGNORECASE))
        self.empty_state_row: Locator = self.table_rows.filter(has_text=EMPTY_STATE_TEXT)

    def _label(self, text: str) -> Locator:
        # "Channel" also names a column header, so labels are taken from label elements only.
        return self._main.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(text)}\s*$", re.IGNORECASE))

    def column_header(self, name: str) -> Locator:
        """Column header ``name``; a sortable header may append a glyph, so only a following word breaks the match."""
        # "/" is escaped too: Playwright's selector parser ends a regex at an unescaped "/" (State/Province).
        pattern = re.escape(name).replace("/", r"\/")
        return self._main.get_by_role("columnheader", name=re.compile(rf"^\W*{pattern}(?!\w)"))
