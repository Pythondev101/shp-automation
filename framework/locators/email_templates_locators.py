"""Locators of the SHP My Account → Email Templates page (``/email-templates``).

Verified against the live page on 2026-09-23. The filter labels are not linked to their
controls, so the name input is the sibling after its label; both selects carry an
``aria-label`` ("Status", "Entries per page"), which is what they are addressed by. The
sortable column headers append a sort glyph ("Name⇅"), so header names are matched as a
substring, never exactly. No email-template data is part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/email-templates$")
LIST_API_PATH = "/api/v1/email-templates"
"""The request the page sends for the table rows on load."""

PAGE_HEADING = "Email Templates"
NO_TEMPLATES_MESSAGE = "No email templates yet"
"""The empty-state message shown while the account has no template."""

FILTERED_EMPTY_MESSAGE = "No results match your filters"
"""The empty-state message shown when a filter matches no template (different from the one above)."""

ADD_TEMPLATE_MODAL_TITLE = "Add Template"
DELETE_DIALOG_TITLE = "Delete template?"

DELETE_API_PATH = re.compile(r"/api/v1/email-templates/\d+$")
"""The request the page sends when a template is deleted; the id is the template's own."""

COLUMN_HEADERS = (
    "S.No",
    "Name",
    "Subject",
    "Channel",
    "Status",
    "Actions",
)
"""Every column header of the table, in the order the page renders them."""


class EmailTemplatesLocators:
    """Every element the Email Templates tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Sidebar: "My Account" is an accordion button whose nested list holds "Email Templates".
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_button: Locator = sidebar_menu.get_by_role("button", name="My Account")
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(has=page.get_by_role("button", name="My Account"))
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.email_templates_link: Locator = self.sidebar_submenu.get_by_role(
            "link", name=PAGE_HEADING, exact=True
        )

        # Page header area. Main holds a second navigation ("Pagination") once templates exist.
        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING, exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        # The button's name starts with an icon glyph, so it is a substring match.
        self.add_template_button: Locator = self._main.get_by_role("button", name="Add Template")

        # Search / filter section.
        self.name_label: Locator = self._label("Name")
        self.name_input: Locator = self._labelled("Name", "input")
        self.status_select: Locator = self._main.get_by_role("combobox", name="Status", exact=True)
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)

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
        self.no_templates_message: Locator = self.empty_state_cell.get_by_text(
            NO_TEMPLATES_MESSAGE, exact=True
        )
        self.no_results_message: Locator = self.empty_state_cell.get_by_text(
            FILTERED_EMPTY_MESSAGE, exact=True
        )

        # Add Template modal. The application renders no ``role="dialog"``, so the modal is the
        # shown Bootstrap modal holding the "Add Template" title; the delete dialog is a second
        # modal of the same kind, which is why both are addressed by their own title.
        self.add_template_modal: Locator = self._modal(ADD_TEMPLATE_MODAL_TITLE)
        self.add_template_modal_title: Locator = self.add_template_modal.get_by_role(
            "heading", name=ADD_TEMPLATE_MODAL_TITLE, exact=True
        )
        # The modal labels are unlinked as well, so each field is the sibling after its label.
        self.modal_name_input: Locator = self._modal_field("Name", "input")
        self.modal_channel_store_id_input: Locator = self._modal_field("Channel store id", "input")
        self.modal_subject_input: Locator = self._modal_field("Subject", "input")
        # The "Body (HTML)" label sits in a flex row next to "Preview", so the textarea is not its
        # sibling; it is the modal's only textarea.
        self.modal_body_input: Locator = self.add_template_modal.locator("textarea")
        self.modal_save_button: Locator = self.add_template_modal.get_by_role(
            "button", name="Save", exact=True
        )
        self.modal_cancel_button: Locator = self.add_template_modal.get_by_role(
            "button", name="Cancel", exact=True
        )

        # Delete confirmation dialog.
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

    def _modal(self, title: str) -> Locator:
        return self._page.locator(".modal.show").filter(
            has=self._page.get_by_role("heading", name=title, exact=True)
        )

    def _modal_field(self, label: str, tag: str) -> Locator:
        # The required labels end in an asterisk and the optional one in "(optional)", so the label
        # name is matched from the start and never exactly.
        modal_label = self.add_template_modal.locator("label.form-label").filter(
            has_text=re.compile(rf"^\s*{re.escape(label)}")
        )
        return modal_label.locator(f"xpath=following-sibling::{tag}[1]")

    def _label(self, text: str) -> Locator:
        return self._main.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(text)}\s*$"))

    def _labelled(self, label: str, tag: str) -> Locator:
        return self._label(label).locator(f"xpath=following-sibling::{tag}[1]")

    def row_for(self, template_name: str) -> Locator:
        """The single data row of the template with this exact name."""
        return self.data_rows.filter(
            has=self._page.get_by_role("cell", name=template_name, exact=True)
        )

    def row_status_badge(self, row: Locator) -> Locator:
        return row.locator("span.badge")

    def row_delete_button(self, row: Locator) -> Locator:
        return row.get_by_role("button", name="Delete", exact=True)

    def status_option(self, label: str) -> Locator:
        """The Status option carrying this visible label, e.g. "Active"."""
        return self.status_select.locator("option").filter(
            has_text=re.compile(rf"^\s*{re.escape(label)}\s*$")
        )

    def column_header(self, name: str) -> Locator:
        # Sortable headers append a sort glyph to their name, so the match is a substring.
        return self.table.get_by_role("columnheader", name=name)
