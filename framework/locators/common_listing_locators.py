"""Locators of the SHP Listing → Common Listing page (``/common-listing``).

Verified against the live page on 2026-09-22. The filter labels are not linked to their
controls, so each control is located as the sibling after its ``<label>`` ("SKU", "Title",
"Status" and "Product Id" are also column headers, so only labels are matched). The table
has an unnamed first column before "S.No". Listing data is deliberately not part of any locator.
"""

from __future__ import annotations

import re
from datetime import date

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/common-listing$")
LIST_API_PATH = "/api/v1/common-listing"
"""The request the first load, Search and Reset send for the table rows (``…/channels`` is another one)."""
CHANNELS_API_PATH = "/api/v1/common-listing/channels"
"""The request that fills the Channel Filter options; it is answered separately from the table rows."""

NO_PRODUCTS_MESSAGE = "No products found."
EMPTY_CELL = "—"
"""What a cell shows when the listing has no value for that column."""

COLUMN_HEADERS = (
    "S.No",
    "Edit",
    "Status",
    "Product Id",
    "Channel Name",
    "Title",
    "UPC",
    "Postal Code",
    "Sub Title",
    "SKU",
    "Quantity",
    "Start Price",
    "Details",
    "Item Specifics",
    "Images",
    "Item Description",
    "Conditional Description",
)
"""Every named column header, in the order the page renders them (after the unnamed first column)."""


class CommonListingLocators:
    """Every element the Common Listing tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: "Listing" is an accordion button whose nested list holds Common Listing, Drafts and Product Images.
        # Its name is wrapped in icon glyphs, so only the word itself is matched.
        listing_name = re.compile(r"^\W*Listing\W*$")
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_button: Locator = sidebar_menu.get_by_role("button", name=listing_name)
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(has=page.get_by_role("button", name=listing_name))
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.common_listing_link: Locator = self.sidebar_submenu.get_by_role("link", name="Common Listing", exact=True)

        # Page header area. The Help button's name starts with an icon glyph, so it is a substring match.
        self.page_heading: Locator = self._main.get_by_role("heading", name="Common Listing", exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        self.help_button: Locator = self._main.get_by_role("button", name="Help")
        self.create_listing_button: Locator = self._main.get_by_role("button", name="Create Listing", exact=True)
        # Create Listing opens a dropdown list of two buttons (the application calls the second "Multi Listing").
        self.single_listing_option: Locator = self._main.get_by_role("button", name="Single Listing", exact=True)
        self.multi_listing_option: Locator = self._main.get_by_role("button", name="Multi Listing", exact=True)
        # The menu's <ul> is not exposed with a list role, so it is the options' nearest list ancestor.
        self.create_listing_menu: Locator = self.single_listing_option.locator("xpath=ancestor::ul[1]")

        # Search / filter section.
        self.upc_number_input: Locator = self._labelled("UPC Number", "input")
        self.sku_input: Locator = self._labelled("SKU", "input")
        self.product_id_input: Locator = self._labelled("Product Id", "input")
        self.title_input: Locator = self._labelled("Title", "input")
        self.channel_select: Locator = self._labelled("Channel Filter", "select")
        self.status_select: Locator = self._labelled("Status", "select")
        # The visible date field; flatpickr keeps a hidden copy that has no role.
        self.published_date_input: Locator = self._main.get_by_role("textbox", name="Choose date range", exact=True)
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)
        # The flatpickr calendar renders outside the page and marks the open one with a class only.
        self._open_calendar: Locator = page.locator(".flatpickr-calendar.open")

        # Table and its "Show <n> entries" control, an unnamed select after the text "Show".
        self.show_entries_select: Locator = self._main.get_by_text("Show", exact=True).locator(
            "xpath=following::select[1]"
        )
        self.table: Locator = self._main.get_by_role("table").filter(
            has=page.get_by_role("columnheader", name="Channel Name", exact=True)
        )
        self.no_products_message: Locator = self.table.get_by_role("cell", name=NO_PRODUCTS_MESSAGE, exact=True)
        self.body_rows: Locator = self.table.locator("tbody tr")
        """Every body row, including the empty-state row."""
        self.data_rows: Locator = self.body_rows.filter(
            has_not=page.get_by_role("cell", name=NO_PRODUCTS_MESSAGE, exact=True)
        )

    def _labelled(self, label: str, tag: str) -> Locator:
        label_element = self._main.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(label)}\s*$"))
        return label_element.locator(f"xpath=following-sibling::{tag}[1]")

    def column_header(self, name: str) -> Locator:
        return self.table.get_by_role("columnheader", name=name, exact=True)

    def column_cells(self, header: str) -> Locator:
        """The ``header`` cells of every data row; the unnamed first column shifts the position by one."""
        return self.data_rows.locator(f"td:nth-child({COLUMN_HEADERS.index(header) + 2})")

    def calendar_day(self, day: date) -> Locator:
        """A day of the open By Published Date calendar, named like "September 22, 2026"."""
        return self._open_calendar.get_by_label(f"{day:%B} {day.day}, {day.year}", exact=True)
