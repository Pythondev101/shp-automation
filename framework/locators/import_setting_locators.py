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

PARSE_HEADER_API_PATH = "/api/v1/setup/import/parse-header"
"""Where the Upload & Map step sends the file so the application reads its header row."""

ITEM_API_PATH = re.compile(r"/api/v1/setup/import/\d+$")
"""One import setting: PUT updates it, DELETE removes it."""

FILTER_PARAMS = {
    "name": "filter1",
    "setup_type": "filter2",
    "setup_files": "filter3",
    "status": "filter4",
}
"""Query parameter each filter is sent as, so a search can wait for its own table request.

The page also refetches unfiltered while a filter control is being changed, so waiting for
"a" table response would read the table between the two renders.
"""

NO_RESULTS_MESSAGE = "No setups found."
"""Shown in place of the rows when the filters match nothing (not the empty state)."""

STEP_ONE_BADGE = "1. Type & Name"
STEP_TWO_BADGE = "2. Upload & Map"
"""The two step indicators of the Add / Edit modal, as the application renders them."""

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

        # Add / Edit Import Setting modal. It is a Bootstrap modal without a dialog role, and
        # only one is ever open, so ".modal.show" addresses whichever one that is.
        self.modal: Locator = page.locator(".modal.show")
        self.modal_title: Locator = self.modal.locator(".modal-title")
        self.modal_body: Locator = self.modal.locator(".modal-body")
        self.modal_close_icon: Locator = self.modal.locator("button.btn-close")
        self.modal_cancel_button: Locator = self.modal.get_by_role("button", name="Cancel", exact=True)
        self.modal_next_button: Locator = self.modal.get_by_role("button", name="Next", exact=True)
        self.modal_back_button: Locator = self.modal.get_by_role("button", name="Back", exact=True)
        self.modal_save_button: Locator = self.modal.get_by_role("button", name="Save", exact=True)

        # Step 1 - Type & Name. The File Type choices are buttons; the selected one is "btn-primary".
        self.file_type_label: Locator = self._modal_label("File Type")
        self.file_type_buttons: Locator = self.file_type_label.locator("xpath=following-sibling::div[1]").get_by_role(
            "button"
        )
        self.modal_name_label: Locator = self._modal_label("Name")
        # The file input of step 2 carries "form-control" as well, so it is excluded here.
        self.modal_name_input: Locator = self.modal_body.locator("input.form-control:not([type='file'])")
        self.modal_type_label: Locator = self._modal_label("Select Type")
        self.modal_type_select: Locator = self.modal_body.locator("select.form-select").first

        # Step 2 - Upload & Map.
        self.modal_file_input: Locator = self.modal_body.locator("input[type='file']")
        self.modal_upload_label: Locator = self._modal_label("Upload File")
        self.mapping_table: Locator = self.modal_body.get_by_role("table")
        self.mapping_rows: Locator = self.mapping_table.locator("tbody tr")
        self.mapping_count_badge: Locator = self.modal_body.locator(".badge").filter(
            has_text=re.compile(r"columns linked")
        )

        # Delete confirmation and the read-only "View Linking" modal.
        self.delete_dialog: Locator = self.modal.filter(
            has=page.locator(".modal-title", has_text="Delete import setting?")
        )
        self.delete_dialog_confirm_button: Locator = self.delete_dialog.locator(".modal-footer .btn-danger")
        self.view_modal: Locator = self.modal.filter(
            has=page.get_by_role("columnheader", name="Linked With", exact=True)
        )
        self.view_modal_rows: Locator = self.view_modal.locator("tbody tr")
        self.view_modal_close_button: Locator = self.view_modal.get_by_role("button", name="Close", exact=True)

        self.no_results_message: Locator = self.empty_state_cell.get_by_text(NO_RESULTS_MESSAGE)

    # Step indicators and required markers of the modal

    def step_badge(self, text: str) -> Locator:
        """One of the two step indicators; the current step carries "bg-primary"."""
        return self.modal_body.locator(".badge").filter(has_text=text).first

    def required_marker(self, label: str) -> Locator:
        """The red asterisk the application renders after a required field's label."""
        return self._modal_label(label).locator(".text-danger")

    def file_type_button(self, label: str) -> Locator:
        return self.file_type_buttons.filter(has_text=re.compile(rf"^{re.escape(label)}$"))

    # Mapping table of step 2

    def mapping_row(self, index: int) -> Locator:
        return self.mapping_rows.nth(index)

    def mapping_column_name(self, index: int) -> Locator:
        """The "File Column" cell - the header the application read out of the uploaded file."""
        return self.mapping_row(index).locator("td").first

    def mapping_select(self, index: int) -> Locator:
        return self.mapping_row(index).locator("select")

    # Rows of the page's own table

    def row_for(self, name: str) -> Locator:
        """The data row whose Name cell is exactly this automation name."""
        return self.data_rows.filter(
            has=self.table.page.locator("td", has_text=re.compile(rf"^\s*{re.escape(name)}\s*$"))
        )

    @staticmethod
    def row_cell(row: Locator, column: str) -> Locator:
        """A cell of a row, addressed by its column header's position."""
        return row.locator("td").nth(COLUMN_HEADERS.index(column))

    @staticmethod
    def row_status_badge(row: Locator) -> Locator:
        return row.locator("td").nth(COLUMN_HEADERS.index("Status")).locator(".badge")

    @staticmethod
    def row_action_button(row: Locator, name: str) -> Locator:
        return row.get_by_role("button", name=name, exact=True)

    def _modal_label(self, text: str) -> Locator:
        """A modal field label, matched on its start: several carry a trailing "*" or "(CSV)"."""
        return self.modal_body.locator("label.form-label").filter(has_text=re.compile(rf"^\s*{re.escape(text)}"))

    def _label(self, text: str) -> Locator:
        return self._main.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(text)}\s*$"))

    def _labelled(self, label: str, tag: str) -> Locator:
        return self._label(label).locator(f"xpath=following-sibling::{tag}[1]")

    def column_cells(self, column: str) -> Locator:
        """Every data row's cell of one column - read in one call, so the rows cannot shift in between."""
        return self.data_rows.locator(f"td:nth-child({COLUMN_HEADERS.index(column) + 1})")

    def column_header(self, name: str) -> Locator:
        return self.table.get_by_role("columnheader", name=name, exact=True)
