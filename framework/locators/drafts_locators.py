"""Locators of the SHP Listing → Drafts page (``/drafts``).

Verified against the live page on 2026-11-12. The page has no search or filter fields: its only
controls are Help, "Show <n> entries", sortable column headers, a selection checkbox per row and
the pagination. Ticking a row reveals a bar with "<n> selected", Resume Drafts, Delete Drafts and
Clear. Draft data is deliberately not part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

from framework.locators.common_listing_locators import CommonListingLocators

PAGE_URL = re.compile(r"/drafts$")
LIST_API_PATH = "/api/v1/drafts"
"""The request the first load and "Show entries" send for the table rows; sorting sends none."""

NO_DRAFTS_MESSAGE = "No drafts found."
EXPIRY_NOTE = "Drafts expire and are automatically deleted 60 days after the last updated date."
HELP_DIALOG_HEADING = "How Drafts work"

SELECT_COLUMN = ""
"""The unnamed second column: it holds the selection checkboxes."""
TABLE_COLUMNS = (
    "S.No",
    SELECT_COLUMN,
    "Action",
    "Photo",
    "Title",
    "Custom SKU",
    "Listing Type",
    "Duration",
    "Start Price",
    "Buy It Now",
    "Shipping Cost",
    "Quantity",
    "Created Date",
    "Updated Date",
    "Expiration Date",
)
"""Every column, in the order the page renders them."""
COLUMN_HEADERS = tuple(column for column in TABLE_COLUMNS if column != SELECT_COLUMN)
SORTABLE_HEADERS = (
    "Title",
    "Custom SKU",
    "Listing Type",
    "Duration",
    "Start Price",
    "Quantity",
    "Created Date",
    "Updated Date",
    "Expiration Date",
)
"""Headers that carry a sort indicator: "⇅" unsorted, "▲" ascending, "▼" descending."""
UNSORTED_INDICATOR = "⇅"
SORTED_INDICATORS = ("▲", "▼")


class DraftsLocators:
    """Every element the Drafts tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: Drafts sits in the same "Listing" accordion as Common Listing.
        sidebar = CommonListingLocators(page)
        self.sidebar_menu_button: Locator = sidebar.sidebar_menu_button
        self.sidebar_submenu: Locator = sidebar.sidebar_submenu
        self.drafts_link: Locator = self.sidebar_submenu.get_by_role("link", name="Drafts", exact=True)

        # Page header area. The Help button's name starts with an icon glyph, so it is a substring match.
        self.page_heading: Locator = self._main.get_by_role("heading", name="Drafts", exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        self.help_button: Locator = self._main.get_by_role("button", name="Help")
        self.help_dialog_heading: Locator = page.get_by_role("dialog").get_by_text(HELP_DIALOG_HEADING, exact=True)
        self.expiry_note: Locator = self._main.get_by_text(EXPIRY_NOTE, exact=True)

        # Controls a search / filter section would hold; the page has none of them today.
        self.text_inputs: Locator = self._main.locator("input:not([type='checkbox'])")
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)

        # Table and its "Show <n> entries" control, an unnamed select after the text "Show".
        self.show_entries_select: Locator = self._main.get_by_text("Show", exact=True).locator(
            "xpath=following::select[1]"
        )
        self.table: Locator = self._main.get_by_role("table").filter(has=page.get_by_role("columnheader", name="Photo"))
        self.select_all_checkbox: Locator = self.table.locator("thead input[type='checkbox']")
        self.no_drafts_message: Locator = self.table.get_by_role("cell", name=NO_DRAFTS_MESSAGE, exact=True)
        self.body_rows: Locator = self.table.locator("tbody tr")
        """Every body row, including the empty-state row."""
        self.data_rows: Locator = self.body_rows.filter(
            has_not=page.get_by_role("cell", name=NO_DRAFTS_MESSAGE, exact=True)
        )
        self.row_checkboxes: Locator = self.data_rows.locator("input[type='checkbox']")

        # Shown only while the table has rows.
        self.entries_info: Locator = self._main.get_by_text(re.compile(r"^Showing \d+ to \d+ of \d+ entries$"))
        self.previous_page_button: Locator = self._main.get_by_role("button", name="Previous", exact=True)
        self.next_page_button: Locator = self._main.get_by_role("button", name="Next", exact=True)

        # Bar shown only while at least one row is ticked.
        self.selected_count: Locator = self._main.get_by_text(re.compile(r"^\d+ selected$"))
        self.resume_drafts_button: Locator = self._main.get_by_role("button", name="Resume Drafts", exact=True)
        self.delete_drafts_button: Locator = self._main.get_by_role("button", name="Delete Drafts", exact=True)
        self.clear_selection_button: Locator = self._main.get_by_role("button", name="Clear", exact=True)

    def column_header(self, name: str) -> Locator:
        """The header called ``name``; a sortable header's name ends with its sort indicator."""
        return self.table.get_by_role("columnheader", name=re.compile(rf"^{re.escape(name)}\W*$"))

    def column_cells(self, header: str) -> Locator:
        return self.data_rows.locator(f"td:nth-child({TABLE_COLUMNS.index(header) + 1})")
