"""Page object of the SHP Help Center page."""

from __future__ import annotations

import logging
import re
from datetime import date

from playwright.sync_api import Locator, Page, Response

from framework.locators.help_center_locators import HelpCenterLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class HelpCenterPage(BasePage):
    # PATH is not set: the page is only reached through the sidebar.

    FULL_TABLE_VIEWPORT = {"width": 1600, "height": 900}
    """Viewport wide enough for every column, as on Manage Channel (D26), whose table component this page shares."""

    CASE_LIST_API = "/api/v1/help-center?"
    """The request that loads the case list; Search and Reset send it again with the chosen filters."""

    CASE_API = re.compile(r"/api/v1/help-center/\d+$")
    """One case: GET loads the Edit form, PUT saves it, DELETE removes the case."""

    AUTOMATION_CASE_DESCRIPTION_PREFIX = "Automation test case description "
    """Every case the automation raises has a description starting with this; only such cases can be deleted."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = HelpCenterLocators(page)

    def show_full_table(self) -> None:
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)

    def open_from_sidebar(self) -> None:
        """Open the page the way a user does: the "Help Center" sidebar entry; wait for its case list."""
        with self.page.expect_response(self._is_case_list_response):
            self.click(self.locators.sidebar_menu_entry, "'Help Center' sidebar menu")

    # Raise New Case

    def open_new_case_form(self) -> None:
        self.click(self.locators.raise_new_case_button, "'+ Raise New Case' button")

    def fill_new_case(self, priority: str, subject: str, description: str) -> None:
        self._select(self.locators.new_case_priority_select, priority, "new case Priority")
        self.fill(self.locators.new_case_subject_input, subject, "new case Subject")
        self.fill(self.locators.new_case_description_input, description, "new case Description")

    def submit_new_case(self) -> None:
        self.click(self.locators.raise_case_button, "'Raise Case' button")

    def raise_case(self, priority: str, subject: str, description: str) -> None:
        self.open_new_case_form()
        self.fill_new_case(priority, subject, description)
        self.submit_new_case()

    def case_id_of(self, row: Locator) -> str:
        return self.locators.cell(row, "Case Id").inner_text().strip()

    # Search and filters

    def enter_search_text(self, text: str) -> None:
        self.fill(self.locators.search_input, text, "Search field")

    def select_priority(self, label: str) -> None:
        self._select(self.locators.priority_select, label, "Priority filter")

    def select_status(self, label: str) -> None:
        self._select(self.locators.status_select, label, "Status filter")

    def choose_date_range(self, start: date, end: date) -> None:
        """Pick ``start`` and then ``end`` in the Date Range calendar; the same day twice selects one day."""
        self.click(self.locators.date_range_input, "Date Range field")
        self.click(self.locators.calendar_day(start), f"calendar day {start:%Y-%m-%d}")
        self.click(self.locators.calendar_day(end), f"calendar day {end:%Y-%m-%d}")

    def apply_filters(self) -> None:
        """Press Search and wait for the case list it requests."""
        with self.page.expect_response(self._is_case_list_response):
            self.click(self.locators.search_button, "Search button")

    def reset_filters(self) -> None:
        with self.page.expect_response(self._is_case_list_response):
            self.click(self.locators.reset_button, "Reset button")

    # Edit and Delete

    def open_edit_form(self, row: Locator) -> None:
        """Click the row's Edit and wait for the case the form is filled from."""
        with self.page.expect_response(lambda response: self._is_case_response(response, "GET")):
            self.click(self.locators.edit_button(row), "row 'Edit' button")

    def update_case(self, priority: str, description: str) -> None:
        self._select(self.locators.new_case_priority_select, priority, "Edit Case Priority")
        self.fill(self.locators.new_case_description_input, description, "Edit Case Description")
        with self.page.expect_response(lambda response: self._is_case_response(response, "PUT")):
            self.click(self.locators.update_case_button, "'Update' button")

    def open_delete_confirmation(self, row: Locator) -> None:
        self.click(self.locators.delete_button(row), "row 'Delete' button")

    def confirm_delete(self) -> None:
        with self.page.expect_response(lambda response: self._is_case_response(response, "DELETE")):
            self.click(self.locators.confirm_delete_button, "confirmation 'Delete' button")

    def delete_automation_case(self, description: str, case_id: str | None) -> bool:
        """Delete the automation case with ``description`` (and ``case_id``, when known); used by clean-up.

        The case is searched for, never picked by position. Returns False when no such case exists.
        Raises ValueError for a description the automation does not create, and RuntimeError when the
        search does not single out one case.
        """
        if not description.startswith(self.AUTOMATION_CASE_DESCRIPTION_PREFIX):
            raise ValueError(f"Refusing to delete a case the automation did not create: {description!r}")
        self.enter_search_text(case_id or description)
        self.apply_filters()
        rows = self.locators.case_row(description)
        if case_id:
            rows = rows.and_(self.locators.case_row_by_id(case_id))
        rows.or_(self.locators.no_cases_row).first.wait_for()
        if rows.count() == 0:
            logger.info("No automation case %r (%s) to delete", description, case_id)
            return False
        if rows.count() != 1:
            raise RuntimeError(f"{rows.count()} cases match {description!r}; none deleted")
        logger.info("Delete automation case %r (%s)", description, case_id)
        self.open_delete_confirmation(rows)
        self.confirm_delete()
        return True

    # Chat

    def open_chat(self, row: Locator) -> None:
        self.click(self.locators.chat_button(row), "row 'Chat' button")

    def send_chat_message(self, text: str) -> None:
        self.fill(self.locators.chat_reply_input, text, "chat reply field")
        self.click(self.locators.chat_send_button, "chat 'Send' button")

    def _select(self, locator: Locator, label: str, description: str) -> None:
        logger.info("Select %r in %s", label, description)
        locator.select_option(label=label)

    def _is_case_list_response(self, response: Response) -> bool:
        return self.CASE_LIST_API in response.url and response.request.method == "GET"

    def _is_case_response(self, response: Response, method: str) -> bool:
        return bool(self.CASE_API.search(response.url)) and response.request.method == method
