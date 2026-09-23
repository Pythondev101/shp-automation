"""Locators of the SHP My Account → SMTP Settings page (``/smtp-settings``).

Verified against the live page on 2026-09-23. The sortable column headers append a sort
glyph ("SMTP Host⇅"), so header names are matched as a substring, never exactly. The
"Show <n> entries" select carries an ``aria-label`` ("Entries per page"), which is what it
is addressed by. The empty state is one cell spanning every column, so it is what tells a
data row apart from the no-data row. No SMTP data is part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/smtp-settings$")
LIST_API_PATH = "/api/v1/smtp/list"
"""The request the page sends for the table rows on load."""

CREATE_API_PATH = "/api/v1/smtp"
"""The request the page sends when an SMTP setting is saved for the first time (POST)."""

RECORD_API_PATH = re.compile(r"/api/v1/smtp/\d+$")
"""The request the page sends when a setting is updated (PUT) or deleted (DELETE); the id is its own."""

ADD_MODAL_TITLE = "Add SMTP Settings"
EDIT_MODAL_TITLE = "Edit SMTP Settings"
DELETE_DIALOG_TITLE = "Delete SMTP settings?"

PAGE_HEADING = "SMTP Settings"
NO_SETTINGS_MESSAGE = "No SMTP settings yet"
"""The empty-state message shown while the account has no SMTP setting."""

COLUMN_HEADERS = (
    "S.No",
    "SMTP Host",
    "SMTP Port",
    "SMTP Username",
    "Status",
    "Action",
)
"""Every column header of the table, in the order the page renders them."""


class SmtpSettingsLocators:
    """Every element the SMTP Settings tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Sidebar: "My Account" is an accordion button whose nested list holds "SMTP Settings".
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_button: Locator = sidebar_menu.get_by_role("button", name="My Account")
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(has=page.get_by_role("button", name="My Account"))
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.smtp_settings_link: Locator = self.sidebar_submenu.get_by_role(
            "link", name=PAGE_HEADING, exact=True
        )

        # Page header area. Main holds a second navigation (Pagination) once settings exist,
        # so the breadcrumb is always addressed by its name.
        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING, exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        # The button's name starts with an icon glyph, so it is a substring match.
        self.add_new_button: Locator = self._main.get_by_role("button", name="Add New")

        # Table and its "Show <n> entries" control.
        self.show_entries_select: Locator = self._main.get_by_role(
            "combobox", name="Entries per page", exact=True
        )
        self.table: Locator = self._main.get_by_role("table")
        self.body_rows: Locator = self.table.locator("tbody tr")
        """Every body row, including the empty-state row."""
        # The empty state is one cell spanning every column; data rows have none.
        self.empty_state_cell: Locator = self.table.locator("tbody td[colspan]")
        self.data_rows: Locator = self.body_rows.filter(has_not=page.locator("td[colspan]"))
        self.no_settings_message: Locator = self.empty_state_cell.get_by_text(
            NO_SETTINGS_MESSAGE, exact=True
        )

        # Add / Edit modal. The application renders no ``role="dialog"``, so a modal is the shown
        # Bootstrap modal holding its own title; the delete confirmation is a second modal of the
        # same kind, which is why each one is addressed by its title.
        self.add_modal: Locator = self._modal(ADD_MODAL_TITLE)
        self.edit_modal: Locator = self._modal(EDIT_MODAL_TITLE)
        self.add_modal_title: Locator = self.add_modal.get_by_role(
            "heading", name=ADD_MODAL_TITLE, exact=True
        )
        self.edit_modal_title: Locator = self.edit_modal.get_by_role(
            "heading", name=EDIT_MODAL_TITLE, exact=True
        )

        # Delete confirmation.
        self.delete_dialog: Locator = self._modal(DELETE_DIALOG_TITLE)
        self.delete_dialog_title: Locator = self.delete_dialog.get_by_role(
            "heading", name=DELETE_DIALOG_TITLE, exact=True
        )
        self.delete_dialog_confirm_button: Locator = self.delete_dialog.get_by_role(
            "button", name="Delete", exact=True
        )
        self.delete_dialog_cancel_button: Locator = self.delete_dialog.get_by_role(
            "button", name="Cancel", exact=True
        )

    # Fields of the Add / Edit modal. The labels are not linked to their controls, so each field
    # is the sibling after its label; the label text differs between Add ("Password *") and Edit
    # ("Password (leave blank to keep)"), so a label is always matched from its start.

    def modal_host_input(self, modal: Locator) -> Locator:
        return self._modal_field(modal, "SMTP host", "input")

    def modal_port_input(self, modal: Locator) -> Locator:
        return self._modal_field(modal, "Port", "input")

    def modal_username_input(self, modal: Locator) -> Locator:
        return self._modal_field(modal, "Username", "input")

    def modal_password_input(self, modal: Locator) -> Locator:
        # The password sits in an input group next to its "Show password" toggle, so it is not
        # the label's own sibling but the input inside that group.
        return self._modal_label(modal, "Password").locator("xpath=following-sibling::div[1]//input")

    def modal_password_toggle(self, modal: Locator) -> Locator:
        return modal.get_by_role("button", name="Show password", exact=True)

    def modal_encryption_select(self, modal: Locator) -> Locator:
        return self._modal_field(modal, "Encryption", "select")

    def modal_from_email_input(self, modal: Locator) -> Locator:
        return self._modal_field(modal, "From email", "input")

    def modal_from_name_input(self, modal: Locator) -> Locator:
        return self._modal_field(modal, "From name", "input")

    def modal_save_button(self, modal: Locator) -> Locator:
        return modal.get_by_role("button", name="Save", exact=True)

    def modal_cancel_button(self, modal: Locator) -> Locator:
        return modal.get_by_role("button", name="Cancel", exact=True)

    def modal_invalid_fields(self, modal: Locator) -> Locator:
        """Fields the application has marked invalid, however it chooses to mark them."""
        return modal.locator("input.is-invalid, select.is-invalid, input[aria-invalid='true']")

    def modal_validation_messages(self, modal: Locator) -> Locator:
        """Validation text the modal shows, however the application renders it."""
        return modal.locator(".invalid-feedback, .text-danger:not(label .text-danger), [role='alert']")

    def _modal(self, title: str) -> Locator:
        return self._page.locator(".modal.show").filter(
            has=self._page.get_by_role("heading", name=title, exact=True)
        )

    def _modal_label(self, modal: Locator, label: str) -> Locator:
        return modal.locator("label.form-label").filter(
            has_text=re.compile(rf"^\s*{re.escape(label)}")
        )

    def _modal_field(self, modal: Locator, label: str, tag: str) -> Locator:
        return self._modal_label(modal, label).locator(f"xpath=following-sibling::{tag}[1]")

    # Table rows

    def row_for(self, username: str) -> Locator:
        """The single data row whose SMTP Username cell holds this exact value."""
        return self.data_rows.filter(has=self._page.get_by_role("cell", name=username, exact=True))

    def rows_with_username_prefix(self, prefix: str) -> Locator:
        """Every data row whose SMTP Username starts with this prefix (the automation's own rows)."""
        return self.data_rows.filter(
            has=self._page.get_by_role("cell", name=re.compile(rf"^{re.escape(prefix)}"))
        )

    def row_cell(self, row: Locator, index: int) -> Locator:
        """One cell of a row by its column position, 0-based (0 = S.No, 1 = SMTP Host, ...)."""
        return row.locator("td").nth(index)

    def row_status_badge(self, row: Locator) -> Locator:
        return row.locator("span.badge")

    def row_edit_button(self, row: Locator) -> Locator:
        return row.get_by_role("button", name="Edit", exact=True)

    def row_delete_button(self, row: Locator) -> Locator:
        return row.get_by_role("button", name="Delete", exact=True)

    def column_header(self, name: str) -> Locator:
        # Sortable headers append a sort glyph to their name, so the match is a substring.
        return self.table.get_by_role("columnheader", name=name)
