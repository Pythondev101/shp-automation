"""Locators of the SHP Active Listing page (a channel's product list, e.g. ``/active-listing/ebay/<id>``).

Verified against the live page on 2026-09-15. The channel is not hard-coded: the page is
opened from whichever channel link the "Active Listing" sidebar sub-menu lists first, and
the heading is "<Channel> All Product". Product data is deliberately not part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/active-listing/")

PAGE_HEADING = re.compile(r"\bAll Product\b", re.IGNORECASE)
"""The page heading is "<Channel> All Product"; the channel part is dynamic."""

COLUMN_HEADERS = (
    "S.No",
    "Edit",
    "Status",
    "Title",
    "Product Id",
    "UPC Number",
    "Postal Code",
    "Sub Title",
    "SKU",
    "Quantity",
    "Start Price",
    "Category",
    "Listing Type",
    "Details",
    "Item Specifics",
    "Images",
    "Item Description",
    "Policies",
)
"""Every column header of the product table, in the order the page renders them."""


class ActiveListingLocators:
    """Every element the Active Listing tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: "Active Listing" is an accordion button whose nested list holds one link per channel.
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_button: Locator = sidebar_menu.get_by_role("button", name="Active Listing")
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(
            has=page.get_by_role("button", name="Active Listing")
        )
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.first_channel_link: Locator = self.sidebar_submenu.get_by_role("link").first

        # Page header area. The Help button's name may start with an icon glyph, so it is a substring match.
        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING).first
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        self.help_button: Locator = self._main.get_by_role("button", name="Help")

        # Filter bar. Labels are unlinked; the inputs are named by their placeholders.
        self.upc_number_label: Locator = self._label("UPC Number")
        self.upc_number_input: Locator = self._main.get_by_role("textbox", name="UPC Number", exact=True)
        self.sku_label: Locator = self._label("SKU")
        self.sku_input: Locator = self._main.get_by_role("textbox", name="Product SKU", exact=True)
        self.title_label: Locator = self._label("Title")
        self.title_input: Locator = self._main.get_by_role("textbox", name="Product Title", exact=True)
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)

        # Table controls. The unnamed "Show <n> entries" select is the page's only dropdown.
        self.show_entries_select: Locator = self._main.get_by_role("combobox")
        self.show_all_columns_button: Locator = self._main.get_by_role("button", name="Show all columns")
        self.table: Locator = self._main.get_by_role("table")
        self.table_rows: Locator = self.table.locator("tbody tr")
        # A data row has one cell per column; the empty-state message is a single cell spanning the table.
        self.first_row_cells: Locator = self.table_rows.first.locator("td")
        self.loading_row: Locator = self.table_rows.filter(has_text=re.compile(r"loading", re.IGNORECASE))

    def _label(self, text: str) -> Locator:
        # "SKU", "Title" and "UPC Number" also name column headers, so labels are taken from label elements only.
        return self._main.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(text)}\s*$", re.IGNORECASE))

    def column_header(self, name: str) -> Locator:
        """Column header ``name``; a sortable header appends a glyph, so only a following word breaks the match."""
        return self._main.get_by_role("columnheader", name=re.compile(rf"^\W*{re.escape(name)}(?!\w)"))
