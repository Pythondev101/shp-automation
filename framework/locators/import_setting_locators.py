"""Locators of the SHP Setup → Import Setting page (``/setup/import``).

Verified against the live page on 2026-09-23. The filter labels are not linked to their
controls, so each control is the sibling after its label. While the account has no import
setting the page opens an onboarding dialog ("New to import settings? Start here") over
itself on every load; it carries a second table, so the page's own table is identified by
its "View Linking" column header. No import-setting data is part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/setup/import$")
LIST_API_PATH = "/api/v1/setup/import"
"""The request the first load sends for the table rows."""

NO_SETTINGS_MESSAGE = "You don’t have any import settings yet."
"""The empty-state message; the apostrophe is U+2019, as the application renders it."""

COLUMN_HEADERS = (
    "S.No",
    "Name",
    "Setup Type",
    "Setup Files",
    "View Linking",
    "Status",
    "Action",
)
"""Every column header of the table, in the order the page renders them."""


class ImportSettingLocators:
    """Every element the Import Setting tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: "Setup" is an accordion button whose nested list holds "Import Setting".
        # Its name starts with an icon glyph, so it is a substring match.
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_button: Locator = sidebar_menu.get_by_role("button", name="Setup")
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(has=page.get_by_role("button", name="Setup"))
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.import_setting_link: Locator = self.sidebar_submenu.get_by_role(
            "link", name="Import Setting", exact=True
        )

        # Page header area. Main holds a second navigation ("Pagination") once import settings exist.
        self.page_heading: Locator = self._main.get_by_role("heading", name="Setup Import List", exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        self.help_button: Locator = self._main.get_by_role("button", name="Help & sample files")
        # The button names start with an icon glyph, so they are substring matches. The empty state
        # holds a second "Add Setup" button; the header one comes first in the DOM.
        self.add_setup_button: Locator = self._main.get_by_role("button", name="Add Setup").first

        # The onboarding dialog the page opens over itself while no import setting exists.
        self.guide_dialog: Locator = page.get_by_role("dialog")
        self.guide_dialog_close_button: Locator = self.guide_dialog.locator("button.btn-close")

        # Search / filter section.
        self.name_label: Locator = self._label("By Name")
        self.name_input: Locator = self._labelled("By Name", "input")
        self.setup_type_select: Locator = self._labelled("By Setup Type", "select")
        self.setup_files_select: Locator = self._labelled("By Setup Files", "select")
        self.status_select: Locator = self._labelled("By Status", "select")
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)

        # Table and its "Show <n> entries" control, an unnamed select after the text "Show".
        self.show_entries_select: Locator = self._main.get_by_text("Show", exact=True).locator(
            "xpath=following::select[1]"
        )
        self.table: Locator = self._main.get_by_role("table").filter(
            has=page.get_by_role("columnheader", name="View Linking", exact=True)
        )
        self.body_rows: Locator = self.table.locator("tbody tr")
        """Every body row, including the empty-state row."""
        # The empty state is one cell spanning every column; data rows have none.
        self.empty_state_cell: Locator = self.table.locator("tbody td[colspan]")
        self.data_rows: Locator = self.body_rows.filter(has_not=page.locator("td[colspan]"))
        self.no_settings_message: Locator = self.empty_state_cell.get_by_text(NO_SETTINGS_MESSAGE).first
        self.empty_state_add_setup_button: Locator = self.empty_state_cell.get_by_role("button", name="Add Setup")
        self.read_guide_button: Locator = self.empty_state_cell.get_by_role("button", name="Read the guide first")

    def _label(self, text: str) -> Locator:
        return self._main.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(text)}\s*$"))

    def _labelled(self, label: str, tag: str) -> Locator:
        return self._label(label).locator(f"xpath=following-sibling::{tag}[1]")

    def column_header(self, name: str) -> Locator:
        return self.table.get_by_role("columnheader", name=name, exact=True)
