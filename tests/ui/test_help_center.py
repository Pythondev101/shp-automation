"""Help Center: page visibility, and raising, finding, chatting on, editing and deleting a case.

Visibility tests (``smoke``) click nothing on the page. Functional tests raise one shared
automation case per browser per module run (``AUTOMATION TEST CASE <hex>``) and use only that
case for search, filters and chat; the one message sent goes to that case. The edit and
delete tests each raise a fresh automation case of their own. The closed-case test only
opens a Closed case's chat and never types or sends. Every raised case is tracked by
``created_cases`` and deleted after the module, pass or fail; no other case is edited or
deleted. The page comes from the ``authenticated_page`` fixture (one sign-in per browser
per run).
"""

from __future__ import annotations

import logging
import re
import secrets
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

import pytest
from playwright.sync_api import Browser, Page, StorageState, expect

from framework.locators.help_center_locators import COLUMN_HEADERS
from framework.pages.help_center_page import HelpCenterPage
from framework.pages.login_page import LoginPage

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.regression

CASE_SUBJECT_PREFIX = "AUTOMATION TEST CASE"
NEW_CASE_PRIORITY = "High"
EDITED_PRIORITY = "Medium"
ACTIVE_STATUS = "Active"
INACTIVE_STATUS = "Inactive"
CLOSED_STATUS = "Closed"
CHAT_TEST_MESSAGE = "Automation test message"


@dataclass(frozen=True)
class AutomationCase:
    subject: str
    description: str
    case_id: str


@pytest.fixture
def help_center(authenticated_page: Page) -> HelpCenterPage:
    """The Help Center page, opened through the sidebar of the signed-in dashboard."""
    page = HelpCenterPage(authenticated_page)
    page.show_full_table()
    page.open_from_sidebar()
    return page


@pytest.fixture(scope="module")
def created_cases(
    browser: Browser,
    browser_name: str,
    browser_context_args: dict,
    _signed_in_storage: dict[str, StorageState],
) -> Iterator[dict[str, str | None]]:
    """Every case this module raises in this browser: description -> Case Id (``None`` until it is read).

    A case is registered before it is submitted. After the module's last test, every case still
    registered is deleted in a fresh signed-in context, whether the tests passed or not. A case
    that cannot be deleted is reported by Case Id and description as a teardown error, which is
    reported in addition to, never instead of, a test's own failure.
    """
    cases: dict[str, str | None] = {}
    yield cases
    if not cases:
        return
    failures: list[str] = []
    storage = _signed_in_storage.get(browser_name)
    if storage is None:
        failures = [f"{case_id or 'Case Id unknown'} {description!r}: no signed-in session" for description, case_id in cases.items()]
    else:
        context = browser.new_context(**{**browser_context_args, "storage_state": storage})
        try:
            page = context.new_page()
            page.goto(LoginPage.DASHBOARD_PATH)
            help_center = HelpCenterPage(page)
            help_center.show_full_table()
            help_center.open_from_sidebar()
            for description, case_id in cases.items():
                try:
                    # Proven by the row disappearing; toasts of earlier deletions may still be on screen.
                    if help_center.delete_automation_case(description, case_id):
                        expect(help_center.locators.case_row(description)).to_have_count(0)
                except Exception as error:  # noqa: BLE001 - every case is attempted, failures are reported below
                    failures.append(f"{case_id or 'Case Id unknown'} {description!r}: {error}")
                    page.reload()
        finally:
            context.close()
    if failures:
        logger.error("Automation cases left in the account: %s", failures)
        pytest.fail("Clean-up failed; automation cases left in the account:\n" + "\n".join(failures), pytrace=False)
    logger.info("Clean-up deleted every automation case of this run (%d)", len(cases))


@pytest.fixture(scope="module")
def _automation_cases(created_cases: dict[str, str | None]) -> dict[str, AutomationCase | None]:
    """The automation case raised per browser; ``None`` once raising it has failed.

    Depends on ``created_cases`` so both are set up and torn down together. pytest groups items
    by parameter, so a test of another browser can run between this module's tests (e.g. a
    ``[firefox-subject]`` test between webkit tests); that switch tears down ``created_cases``,
    whose clean-up deletes the case. The next test must then raise a new case, not reuse the
    deleted one.
    """
    return {}


@pytest.fixture
def automation_case(
    help_center: HelpCenterPage,
    browser_name: str,
    _automation_cases: dict[str, AutomationCase | None],
    created_cases: dict[str, str | None],
) -> AutomationCase:
    """This browser's automation case: the one already raised in this run, otherwise raised now.

    Once raising it has failed, dependent tests stop with an error instead of using other cases.
    """
    if browser_name in _automation_cases:
        case = _automation_cases[browser_name]
        if case is None:
            pytest.fail("Blocked: raising the automation case failed earlier in this run.", pytrace=False)
        return case
    _automation_cases[browser_name] = None
    case = _raise_automation_case(help_center, created_cases)
    _automation_cases[browser_name] = case
    return case


def _unique_case_text() -> tuple[str, str]:
    """Subject and description sharing one random tag, so the case is identifiable from the list."""
    tag = secrets.token_hex(4)
    return f"{CASE_SUBJECT_PREFIX} {tag}", f"{HelpCenterPage.AUTOMATION_CASE_DESCRIPTION_PREFIX}{tag}"


def _raise_automation_case(help_center: HelpCenterPage, created_cases: dict[str, str | None]) -> AutomationCase:
    """Raise a new automation case, registered for clean-up before it is submitted."""
    subject, description = _unique_case_text()
    created_cases[description] = None
    help_center.raise_case(NEW_CASE_PRIORITY, subject, description)
    return _confirm_listed_case(help_center, subject, description, created_cases)


def _confirm_listed_case(
    help_center: HelpCenterPage, subject: str, description: str, created_cases: dict[str, str | None]
) -> AutomationCase:
    """Assert the raise succeeded and the case is listed; return it with the Case Id the application gave it."""
    locators = help_center.locators
    expect(locators.case_raised_toast).to_be_visible()
    expect(locators.modal).to_have_count(0)
    row = locators.case_row(description)
    expect(row).to_have_count(1)
    expect(locators.cell(row, "Priority")).to_have_text(NEW_CASE_PRIORITY)
    expect(locators.cell(row, "Status")).to_have_text(ACTIVE_STATUS)
    expect(locators.cell(row, "Case Id")).to_have_text(re.compile(r"^\S+$"))
    case = AutomationCase(subject, description, help_center.case_id_of(row))
    created_cases[description] = case.case_id
    return case


def _exactly(text: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(text)}$")


def _expect_every_listed(help_center: HelpCenterPage, header: str, pattern: re.Pattern[str]) -> None:
    """Every listed case's ``header`` cell matches ``pattern``; retries until the filtered list is shown."""
    expect(help_center.locators.column_cells(header).filter(has_not_text=pattern)).to_have_count(0)


# Visibility


@pytest.mark.smoke
def test_help_center_page_opens_successfully(help_center: HelpCenterPage) -> None:
    expect(help_center.locators.page_heading).to_be_visible()


@pytest.mark.smoke
def test_page_header_elements_are_visible(help_center: HelpCenterPage) -> None:
    expect(help_center.locators.breadcrumb).to_be_visible()
    expect(help_center.locators.raise_new_case_button).to_be_visible()


@pytest.mark.smoke
def test_filter_bar_is_visible(help_center: HelpCenterPage) -> None:
    locators = help_center.locators
    expect(locators.search_label).to_be_visible()
    expect(locators.search_input).to_be_visible()
    expect(locators.priority_select).to_be_visible()
    expect(locators.status_select).to_be_visible()
    expect(locators.date_range_input).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()


@pytest.mark.smoke
def test_table_and_its_controls_are_visible(help_center: HelpCenterPage) -> None:
    expect(help_center.locators.show_entries_select).to_be_visible()
    expect(help_center.locators.table).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(help_center: HelpCenterPage, header: str) -> None:
    expect(help_center.locators.column_header(header)).to_be_visible()


@pytest.mark.smoke
def test_pagination_area_is_visible(help_center: HelpCenterPage) -> None:
    locators = help_center.locators
    expect(locators.entry_count).to_be_visible()
    expect(locators.pagination).to_be_visible()
    expect(locators.previous_button).to_be_visible()
    expect(locators.current_page).to_be_visible()
    expect(locators.next_button).to_be_visible()


# Raise New Case


@pytest.mark.functional
@pytest.mark.destructive
def test_raise_new_case_creates_a_listed_case(
    help_center: HelpCenterPage,
    browser_name: str,
    _automation_cases: dict[str, AutomationCase | None],
    created_cases: dict[str, str | None],
) -> None:
    locators = help_center.locators
    help_center.open_new_case_form()
    expect(locators.new_case_heading).to_be_visible()
    for control in (
        locators.new_case_priority_select,
        locators.new_case_subject_input,
        locators.new_case_description_input,
        locators.raise_case_button,
        locators.cancel_new_case_button,
    ):
        expect(control).to_be_visible()
        expect(control).to_be_enabled()

    subject, description = _unique_case_text()
    _automation_cases[browser_name] = None
    created_cases[description] = None
    help_center.fill_new_case(NEW_CASE_PRIORITY, subject, description)
    help_center.submit_new_case()

    # Later tests of this run reuse the case instead of raising another one.
    _automation_cases[browser_name] = _confirm_listed_case(help_center, subject, description, created_cases)


# Search and filters


@pytest.mark.functional
@pytest.mark.destructive
def test_search_by_case_id_returns_the_case(help_center: HelpCenterPage, automation_case: AutomationCase) -> None:
    help_center.enter_search_text(automation_case.case_id)
    help_center.apply_filters()

    _expect_every_listed(help_center, "Case Id", _exactly(automation_case.case_id))
    expect(help_center.locators.case_row(automation_case.description)).to_be_visible()


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.parametrize("field", ["subject", "description"])
def test_search_by_text_returns_the_case(
    help_center: HelpCenterPage, automation_case: AutomationCase, field: str
) -> None:
    help_center.enter_search_text(getattr(automation_case, field))
    help_center.apply_filters()

    # Subject and description carry the case's unique tag, so no other case can match.
    _expect_every_listed(help_center, "Description", _exactly(automation_case.description))
    expect(help_center.locators.case_row(automation_case.description)).to_be_visible()


@pytest.mark.functional
@pytest.mark.destructive
def test_priority_filter_shows_only_the_selected_priority(
    help_center: HelpCenterPage, automation_case: AutomationCase
) -> None:
    help_center.select_priority(NEW_CASE_PRIORITY)
    help_center.apply_filters()

    _expect_every_listed(help_center, "Priority", _exactly(NEW_CASE_PRIORITY))
    expect(help_center.locators.case_row(automation_case.description)).to_be_visible()


@pytest.mark.functional
@pytest.mark.destructive
def test_status_filter_shows_the_selected_status(help_center: HelpCenterPage, automation_case: AutomationCase) -> None:
    locators = help_center.locators
    help_center.select_status(INACTIVE_STATUS)
    help_center.apply_filters()
    # The automation case is Active, so the Inactive filter must hide it.
    expect(locators.case_row(automation_case.description)).to_have_count(0)
    _expect_every_listed(help_center, "Status", _exactly(INACTIVE_STATUS))

    help_center.select_status(ACTIVE_STATUS)
    help_center.apply_filters()
    row = locators.case_row(automation_case.description)
    expect(row).to_be_visible()
    expect(locators.cell(row, "Status")).to_have_text(ACTIVE_STATUS)
    # The application also lists Closed cases under "Active" (see README, Help Center), so only
    # Inactive cases are asserted to be excluded.
    expect(locators.rows_with_status(INACTIVE_STATUS)).to_have_count(0)


@pytest.mark.functional
@pytest.mark.destructive
def test_date_range_filter_shows_cases_in_the_range(
    help_center: HelpCenterPage, automation_case: AutomationCase
) -> None:
    today = date.today()
    help_center.choose_date_range(today, today)
    expect(help_center.locators.date_range_input).to_have_value(f"{today:%d-%m-%Y}")
    help_center.apply_filters()

    _expect_every_listed(help_center, "Date & Time", re.compile(rf"^{today:%d-%m-%Y} "))
    expect(help_center.locators.case_row(automation_case.description)).to_be_visible()


@pytest.mark.functional
@pytest.mark.destructive
def test_combined_filters_return_only_matching_cases(
    help_center: HelpCenterPage, automation_case: AutomationCase
) -> None:
    today = date.today()
    help_center.enter_search_text(automation_case.subject)
    help_center.select_priority(NEW_CASE_PRIORITY)
    help_center.select_status(ACTIVE_STATUS)
    help_center.choose_date_range(today, today)
    help_center.apply_filters()

    _expect_every_listed(help_center, "Description", _exactly(automation_case.description))
    _expect_every_listed(help_center, "Priority", _exactly(NEW_CASE_PRIORITY))
    _expect_every_listed(help_center, "Status", _exactly(ACTIVE_STATUS))
    _expect_every_listed(help_center, "Date & Time", re.compile(rf"^{today:%d-%m-%Y} "))
    expect(help_center.locators.case_row(automation_case.description)).to_be_visible()


@pytest.mark.functional
@pytest.mark.destructive
def test_reset_restores_default_filters_and_list(help_center: HelpCenterPage, automation_case: AutomationCase) -> None:
    locators = help_center.locators
    expect(locators.case_row(automation_case.description)).to_be_visible()
    unfiltered_entry_count = locators.entry_count.inner_text()

    today = date.today()
    help_center.enter_search_text(automation_case.subject)
    help_center.select_priority(NEW_CASE_PRIORITY)
    help_center.select_status(ACTIVE_STATUS)
    help_center.choose_date_range(today, today)
    help_center.apply_filters()
    _expect_every_listed(help_center, "Description", _exactly(automation_case.description))

    help_center.reset_filters()

    expect(locators.search_input).to_have_value("")
    expect(locators.priority_select).to_have_value("")  # "All"
    expect(locators.status_select).to_have_value("")  # "All"
    expect(locators.date_range_input).to_have_value("")
    expect(locators.entry_count).to_have_text(unfiltered_entry_count)
    expect(locators.case_row(automation_case.description)).to_be_visible()


# Chat


@pytest.mark.functional
@pytest.mark.destructive
def test_chat_on_active_case_sends_a_message(help_center: HelpCenterPage, automation_case: AutomationCase) -> None:
    locators = help_center.locators
    help_center.enter_search_text(automation_case.case_id)
    help_center.apply_filters()
    row = locators.case_row(automation_case.description)
    expect(locators.cell(row, "Status")).to_have_text(ACTIVE_STATUS)
    expect(locators.chat_button(row)).to_be_enabled()

    help_center.open_chat(row)
    expect(locators.chat_heading).to_contain_text(f"Case {automation_case.case_id}")
    expect(locators.chat_reply_input).to_be_enabled()
    expect(locators.chat_send_button).to_be_enabled()

    help_center.send_chat_message(CHAT_TEST_MESSAGE)
    expect(locators.chat_message(CHAT_TEST_MESSAGE)).to_be_visible()


@pytest.mark.functional
def test_closed_case_chat_cannot_receive_replies(help_center: HelpCenterPage) -> None:
    locators = help_center.locators
    # Wait for the case list itself (a loading or empty-state row has no Case Id cell).
    expect(locators.column_cells("Case Id").first).to_be_visible()
    closed_rows = locators.rows_with_status(CLOSED_STATUS)
    if closed_rows.count() == 0:
        pytest.skip("No case with Status 'Closed' on the first page of the Help Center list")
    row = closed_rows.first
    case_id = help_center.case_id_of(row)

    # Chat is the application's own, enabled control; it opens the thread. Nothing is typed or sent.
    help_center.open_chat(row)
    expect(locators.chat_heading).to_contain_text(f"Case {case_id}")
    expect(locators.chat_heading).to_contain_text(CLOSED_STATUS)
    expect(locators.chat_closed_notice).to_be_visible()
    expect(locators.chat_reply_input).to_have_count(0)
    expect(locators.chat_send_button).to_have_count(0)


# Edit and Delete (each on a fresh automation case of its own)


@pytest.mark.functional
@pytest.mark.destructive
def test_edit_case_updates_priority_and_description(
    help_center: HelpCenterPage, created_cases: dict[str, str | None]
) -> None:
    locators = help_center.locators
    case = _raise_automation_case(help_center, created_cases)
    row = locators.case_row_by_id(case.case_id)

    help_center.open_edit_form(row)
    expect(locators.edit_case_heading).to_be_visible()
    expect(locators.new_case_subject_input).to_have_value(case.subject)
    expect(locators.new_case_description_input).to_have_value(case.description)
    expect(locators.selected_option(locators.new_case_priority_select)).to_have_text(NEW_CASE_PRIORITY)

    # The unique tag stays in the description, so the case remains identifiable (and cleanable).
    edited_description = f"{case.description} edited"
    help_center.update_case(EDITED_PRIORITY, edited_description)

    expect(locators.case_updated_toast).to_be_visible()
    expect(locators.modal).to_have_count(0)
    expect(locators.cell(row, "Description")).to_have_text(edited_description)
    expect(locators.cell(row, "Priority")).to_have_text(EDITED_PRIORITY)
    expect(locators.cell(row, "Status")).to_have_text(ACTIVE_STATUS)

    # Loaded from the server again: search by the Case Id.
    help_center.enter_search_text(case.case_id)
    help_center.apply_filters()
    _expect_every_listed(help_center, "Case Id", _exactly(case.case_id))
    expect(locators.cell(row, "Description")).to_have_text(edited_description)
    expect(locators.cell(row, "Priority")).to_have_text(EDITED_PRIORITY)


@pytest.mark.functional
@pytest.mark.destructive
def test_delete_case_removes_it_from_the_list(
    help_center: HelpCenterPage, created_cases: dict[str, str | None]
) -> None:
    locators = help_center.locators
    case = _raise_automation_case(help_center, created_cases)
    help_center.enter_search_text(case.case_id)
    help_center.apply_filters()
    _expect_every_listed(help_center, "Case Id", _exactly(case.case_id))
    # Identified by its Case Id and its unique description, never by position.
    row = locators.case_row_by_id(case.case_id).filter(has_text=case.description)
    expect(row).to_have_count(1)

    help_center.open_delete_confirmation(row)
    expect(locators.delete_case_heading).to_be_visible()
    expect(locators.delete_confirmation_text(case.case_id)).to_be_visible()
    help_center.confirm_delete()

    expect(locators.case_deleted_toast).to_be_visible()
    expect(locators.modal).to_have_count(0)
    expect(locators.case_row_by_id(case.case_id)).to_have_count(0)
    # Search sends no request when its text is unchanged, and the Case Id is already entered: description first.
    for text in (case.description, case.case_id):
        help_center.enter_search_text(text)
        help_center.apply_filters()
        expect(locators.no_cases_row).to_be_visible()
        expect(locators.case_row(case.description)).to_have_count(0)
    # Deleted by the test itself: nothing left for the clean-up.
    del created_cases[case.description]
