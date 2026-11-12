"""Listing → Drafts: navigation, visibility, Show entries, sorting and row selection.

The page is reached through the sidebar "Listing" → "Drafts" on the ``authenticated_page``
fixture. The page has no search or filter fields and no Reset; that is asserted, so the test
fails (and this file needs the filter tests) once the application adds them. Draft data is
dynamic: no row count, title, SKU or date is hardcoded, and every check holds whether the table
has rows or shows its empty state.

These tests are read-only. Rows are only ticked and un-ticked; "Resume draft", "Resume Drafts"
and "Delete Drafts" are never clicked, so no existing draft is opened, edited or deleted.
Editing and deleting an automation-owned draft is not covered: the application cannot create
one at present (see ``test_multi_listing.py``).
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, expect

from framework.locators.drafts_locators import (
    COLUMN_HEADERS,
    PAGE_URL,
    SORTABLE_HEADERS,
    SORTED_INDICATORS,
    UNSORTED_INDICATOR,
)
from framework.pages.drafts_page import DraftsPage

pytestmark = pytest.mark.regression

ALL_INDICATORS = (UNSORTED_INDICATOR, *SORTED_INDICATORS)


@pytest.fixture
def drafts(authenticated_page: Page) -> DraftsPage:
    """The Drafts page, opened through the signed-in sidebar."""
    page = DraftsPage(authenticated_page)
    page.open_from_sidebar()
    return page


def _expect_valid_result(drafts: DraftsPage) -> None:
    """The latest table request succeeded and the table shows rows or its empty-state message."""
    locators = drafts.locators
    response = drafts.last_list_response
    assert response is not None and response.ok, f"Table request failed: {response and response.status}"
    expect(locators.page_heading).to_be_visible()
    expect(locators.table).to_be_visible()
    expect(locators.body_rows.first).to_be_visible()
    if locators.data_rows.count() == 0:
        expect(locators.no_drafts_message).to_be_visible()
    else:
        expect(locators.no_drafts_message).to_have_count(0)


def _require_rows(drafts: DraftsPage) -> int:
    count = drafts.locators.data_rows.count()
    if count == 0:
        pytest.skip("The Drafts table is empty")
    return count


# Navigation


@pytest.mark.smoke
def test_drafts_opens_from_listing_menu(drafts: DraftsPage) -> None:
    locators = drafts.locators
    expect(locators.sidebar_submenu).to_be_visible()
    expect(drafts.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    expect(locators.drafts_link).to_have_attribute("aria-current", "page")


# Visibility


@pytest.mark.smoke
def test_page_header_elements_are_visible(drafts: DraftsPage) -> None:
    locators = drafts.locators
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.help_button).to_be_visible()
    expect(locators.expiry_note).to_be_visible()


@pytest.mark.smoke
def test_table_and_controls_are_visible(drafts: DraftsPage) -> None:
    locators = drafts.locators
    expect(locators.show_entries_select).to_be_visible()
    expect(locators.table).to_be_visible()
    expect(locators.select_all_checkbox).to_be_visible()
    # The entries summary and the pagination are rendered only while the table has rows.
    if locators.data_rows.count() > 0:
        expect(locators.entries_info).to_be_visible()
        expect(locators.previous_page_button).to_be_visible()
        expect(locators.next_page_button).to_be_visible()


@pytest.mark.smoke
def test_page_has_no_search_or_filter_fields(drafts: DraftsPage) -> None:
    """The current Drafts page offers no search / filter section; update the tests when it gets one."""
    locators = drafts.locators
    expect(locators.text_inputs).to_have_count(0)
    expect(locators.search_button).to_have_count(0)
    expect(locators.reset_button).to_have_count(0)


@pytest.mark.smoke
@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(drafts: DraftsPage, header: str) -> None:
    expect(drafts.locators.column_header(header)).to_be_visible()


@pytest.mark.smoke
def test_table_shows_rows_or_empty_state(drafts: DraftsPage) -> None:
    _expect_valid_result(drafts)


@pytest.mark.functional
def test_help_opens_the_drafts_guide(drafts: DraftsPage) -> None:
    drafts.open_help()
    expect(drafts.locators.help_dialog_heading).to_be_visible()


# Show entries, sorting and selection


@pytest.mark.functional
def test_show_entries_reloads_the_table(drafts: DraftsPage) -> None:
    locators = drafts.locators
    options = drafts.entries_options()
    assert options, "Show entries offers no option"
    # The default option is chosen last, so every choice is a change and the page is left as it was found.
    for count in [*options[1:], options[0]]:
        drafts.show_entries(count)

        assert drafts.last_list_response is not None
        query = parse_qs(urlparse(drafts.last_list_response.url).query)
        assert query.get("no_of_rows") == [count], f"Show {count} entries requested {query}"
        expect(locators.show_entries_select).to_have_value(count)
        _expect_valid_result(drafts)
        assert locators.data_rows.count() <= int(count)


@pytest.mark.functional
@pytest.mark.parametrize("header", SORTABLE_HEADERS)
def test_sortable_column_sorts(drafts: DraftsPage, header: str) -> None:
    _require_rows(drafts)
    values = drafts.column_values(header)

    initial = drafts.sort_indicator(header)

    # Each click moves the header one step through unsorted → ascending → descending → unsorted.
    # The page opens sorted by one column, so the cycle may start at any of the three states.
    seen = []
    for _ in ALL_INDICATORS:
        drafts.sort_by(header)
        seen.append(drafts.sort_indicator(header))
        # Sorting only reorders the loaded rows; it must neither drop nor add one.
        assert sorted(drafts.column_values(header)) == sorted(values)
        if seen[-1] in SORTED_INDICATORS:
            for other in SORTABLE_HEADERS:
                if other != header:
                    assert drafts.sort_indicator(other) == UNSORTED_INDICATOR, f"{other} is also marked as sorted"
    assert sorted(seen) == sorted(ALL_INDICATORS), f"{header} went through {seen} from {initial!r}"
    assert seen[-1] == initial, f"{header} ended on {seen[-1]!r}, started on {initial!r}"


@pytest.mark.functional
def test_selecting_a_row_shows_the_bulk_actions(drafts: DraftsPage) -> None:
    _require_rows(drafts)
    locators = drafts.locators
    expect(locators.delete_drafts_button).to_have_count(0)

    drafts.select_first_row()
    expect(locators.selected_count).to_have_text("1 selected")
    expect(locators.resume_drafts_button).to_be_visible()
    expect(locators.delete_drafts_button).to_be_visible()

    drafts.clear_selection()
    expect(locators.row_checkboxes.first).not_to_be_checked()
    expect(locators.selected_count).to_have_count(0)
    expect(locators.resume_drafts_button).to_have_count(0)
    expect(locators.delete_drafts_button).to_have_count(0)


@pytest.mark.functional
def test_select_all_ticks_every_row(drafts: DraftsPage) -> None:
    rows = _require_rows(drafts)
    locators = drafts.locators

    drafts.select_all_rows()
    for index in range(rows):
        expect(locators.row_checkboxes.nth(index)).to_be_checked()
    expect(locators.selected_count).to_have_text(f"{rows} selected")

    drafts.clear_selection()
    expect(locators.select_all_checkbox).not_to_be_checked()
    for index in range(rows):
        expect(locators.row_checkboxes.nth(index)).not_to_be_checked()
