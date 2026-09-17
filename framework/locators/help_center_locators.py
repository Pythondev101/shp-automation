"""Locators of the SHP Help Center page.

The table controls and pagination follow the Manage Channel page, which uses the
same table component. Case values (case ids, descriptions, priorities, statuses,
dates) are never written into a locator: rows are found by text the caller passes,
e.g. the unique description of the case the automation raised.
"""

from __future__ import annotations

import re
from datetime import date

from playwright.sync_api import Locator, Page

PAGE_HEADING = "Help Center"

COLUMN_HEADERS = (
    "S.No",
    "Case Id",
    "Description",
    "File",
    "Priority",
    "Status",
    "Chat",
    "Action",
    "Date & Time",
)
"""Every column header of the Help Center table, in the order the page renders them."""

ENTRY_COUNT_TEXT = re.compile(r"^Showing .+ entries$")
"""The entry count line; the numbers in it are data and are not matched."""

CASE_RAISED_MESSAGE = "Case raised successfully."
NO_CASES_TEXT = "No cases found."
CASE_UPDATED_MESSAGE = "Case updated successfully."
CASE_DELETED_MESSAGE = "Case deleted successfully."
CLOSED_CASE_CHAT_NOTICE = "This case is closed and can no longer receive replies."


class HelpCenterLocators:
    """Every element the Help Center tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Sidebar: the only menu entry these tests click.
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_entry: Locator = sidebar_menu.get_by_role("link", name="Help Center")

        # Page header area. The title may repeat as a card title, so the first heading is taken.
        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING, exact=True).first
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        # The button name starts with an icon glyph / "+", so it is matched as a substring.
        self.raise_new_case_button: Locator = self._main.get_by_role("button", name="Raise New Case")

        # Filter bar. "Search", "Priority" and "Status" also name a button or column header, so labels
        # are taken from label elements only. The two dropdowns have no accessible name and their labels
        # are unlinked, so each is the first select after its label (as on My Profile, D37).
        self.search_label: Locator = self._label("Search")
        self.search_input: Locator = self._main.get_by_role("textbox", name="Case ID / Subject / Description", exact=True)
        self.priority_select: Locator = self._label("Priority").locator("xpath=following::select[1]")
        self.status_select: Locator = self._label("Status").locator("xpath=following::select[1]")
        self.date_range_input: Locator = self._main.get_by_role("textbox", name="Choose date range", exact=True)
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)
        # The Date Range picker (flatpickr) renders its calendar outside the page and marks the open
        # one with a class only (D39).
        self._open_calendar: Locator = page.locator(".flatpickr-calendar.open")

        # Table and its "Show <n> entries" control, an unnamed select after the text "Show".
        self.show_entries_select: Locator = self._main.get_by_text("Show", exact=True).locator(
            "xpath=following::select[1]"
        )
        self.table: Locator = self._main.get_by_role("table")
        self.case_rows: Locator = self.table.locator("tbody tr")
        self.no_cases_row: Locator = self.case_rows.filter(has_text=NO_CASES_TEXT)

        # Footer: entry count and pagination. The current page number is marked with a class only (D28).
        self.entry_count: Locator = self._main.get_by_text(ENTRY_COUNT_TEXT)
        self.pagination: Locator = self._main.get_by_role("navigation", name="Pagination")
        self.previous_button: Locator = self.pagination.get_by_role("button", name="Previous", exact=True)
        self.next_button: Locator = self.pagination.get_by_role("button", name="Next", exact=True)
        self.current_page: Locator = self.pagination.locator("li.active").get_by_role("button")

        # The Raise New Case form and a case's chat are both a modal without a dialog role; the open
        # one carries the class "show", as on Manage Channel (D29). Its labels are unlinked too.
        self.modal: Locator = page.locator(".modal.show")
        self.new_case_heading: Locator = self.modal.get_by_role("heading", name="Raise New Case", exact=True)
        self.new_case_priority_select: Locator = self._modal_field("Priority", "select")
        self.new_case_subject_input: Locator = self._modal_field("Subject", "input")
        self.new_case_description_input: Locator = self._modal_field("Description", "textarea")
        self.raise_case_button: Locator = self.modal.get_by_role("button", name="Raise Case", exact=True)
        self.cancel_new_case_button: Locator = self.modal.get_by_role("button", name="Cancel", exact=True)
        # Toasts are rendered outside main.
        self.case_raised_toast: Locator = page.get_by_role("status").filter(has_text=CASE_RAISED_MESSAGE)

        # Edit Case is the same modal form, prefilled: the new_case_* field locators above apply to it too.
        self.edit_case_heading: Locator = self.modal.get_by_role("heading", name="Edit Case", exact=True)
        self.update_case_button: Locator = self.modal.get_by_role("button", name="Update", exact=True)
        self.case_updated_toast: Locator = page.get_by_role("status").filter(has_text=CASE_UPDATED_MESSAGE)

        # Delete confirmation modal.
        self.delete_case_heading: Locator = self.modal.get_by_role("heading", name="Delete this case?", exact=True)
        self.confirm_delete_button: Locator = self.modal.get_by_role("button", name="Delete", exact=True)
        self.case_deleted_toast: Locator = page.get_by_role("status").filter(has_text=CASE_DELETED_MESSAGE)

        # Chat modal: its heading reads "Case <case id>" followed by the status badge.
        self.chat_heading: Locator = self.modal.get_by_role("heading")
        self.chat_reply_input: Locator = self.modal.get_by_role("textbox", name="Write a reply…", exact=True)
        self.chat_send_button: Locator = self.modal.get_by_role("button", name="Send", exact=True)
        self.chat_closed_notice: Locator = self.modal.get_by_text(CLOSED_CASE_CHAT_NOTICE, exact=True)

    def _label(self, text: str) -> Locator:
        return self._main.locator("label").filter(has_text=re.compile(rf"^{text}$"))

    def _modal_field(self, label: str, kind: str) -> Locator:
        # Required labels end with " *", so the label is matched on its first word.
        return self.modal.locator("label").filter(has_text=re.compile(rf"^{label}\b")).locator(
            f"xpath=following::{kind}[1]"
        )

    def column_header(self, name: str) -> Locator:
        """Column header ``name``; matched as a substring because sortable headers append a glyph."""
        return self._main.get_by_role("columnheader", name=name)

    def case_row(self, text: str) -> Locator:
        """The listed case rows containing ``text``, e.g. a case's unique description."""
        return self.case_rows.filter(has_text=text)

    def case_row_by_id(self, case_id: str) -> Locator:
        """The listed case row whose Case Id cell reads exactly ``case_id``."""
        id_cell = self._page.locator(_cell_selector("Case Id"), has_text=re.compile(rf"^{re.escape(case_id)}$"))
        return self.case_rows.filter(has=id_cell)

    def rows_with_status(self, status: str) -> Locator:
        """The listed case rows whose Status cell reads exactly ``status``."""
        status_cell = self._page.locator(_cell_selector("Status"), has_text=re.compile(rf"^{re.escape(status)}$"))
        return self.case_rows.filter(has=status_cell)

    def cell(self, row: Locator, header: str) -> Locator:
        """The cell of ``row`` under column ``header``."""
        return row.locator(_cell_selector(header))

    def column_cells(self, header: str) -> Locator:
        """The cells of every listed case row under column ``header``."""
        return self.case_rows.locator(_cell_selector(header))

    def chat_button(self, row: Locator) -> Locator:
        # The button name starts with an icon glyph, so it is matched as a substring.
        return row.get_by_role("button", name="Chat")

    def edit_button(self, row: Locator) -> Locator:
        # The icon buttons' accessible name comes from their glyph; "Edit" / "Delete" is only their title.
        return row.get_by_title("Edit", exact=True)

    def delete_button(self, row: Locator) -> Locator:
        return row.get_by_title("Delete", exact=True)

    def delete_confirmation_text(self, case_id: str) -> Locator:
        return self.modal.get_by_text(f"Delete case {case_id}? This cannot be undone.", exact=True)

    def selected_option(self, select: Locator) -> Locator:
        return select.locator("option:checked")

    def chat_message(self, text: str) -> Locator:
        return self.modal.get_by_text(text, exact=True)

    def calendar_day(self, day: date) -> Locator:
        """A day of the open Date Range calendar, named like "September 14, 2026"."""
        return self._open_calendar.get_by_label(f"{day:%B} {day.day}, {day.year}", exact=True)


def _cell_selector(header: str) -> str:
    # Cells carry no name of their own, so a column is addressed by its position in the verified header order (D38).
    return f"td:nth-child({COLUMN_HEADERS.index(header) + 1})"
