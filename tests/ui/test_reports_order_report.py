"""Reports → Order Report: navigation, visibility and the search filters.

The page is reached through the sidebar "Reports" link and comes from the
``authenticated_page`` fixture (one sign-in per browser per run). Report data is dynamic:
filter values are taken from the visible rows or the dropdown options, and every check
holds whether the filtered table has rows or shows its empty state. Request Report,
Download, Help, the other report tabs, sorting and pagination are out of scope.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.reports_locators import COLUMN_HEADERS, PAGE_URL, REPORT_TABS
from framework.pages.reports_page import ACTIVE_TAB, ReportsPage

pytestmark = pytest.mark.regression

SEARCH_VALUE = "automation-test"
"""A harmless value typed into a text filter when no visible row offers one."""


@pytest.fixture
def order_report(authenticated_page: Page) -> ReportsPage:
    """The Reports page on its Order Report tab, opened through the signed-in sidebar."""
    page = ReportsPage(authenticated_page)
    page.open_from_sidebar()
    page.open_order_report_tab()
    return page


def _expect_valid_result(order_report: ReportsPage) -> None:
    """The latest table request succeeded and the table shows rows or its empty-state message."""
    locators = order_report.locators
    response = order_report.last_list_response
    assert response is not None and response.ok, f"Table request failed: {response and response.status}"
    expect(locators.table).to_be_visible()
    # The body always holds a row: either data or the empty-state message.
    expect(locators.body_rows.first).to_be_visible()
    if locators.data_rows.count() == 0:
        expect(locators.no_results_message).to_be_visible()
    else:
        expect(locators.no_results_message).to_have_count(0)


def _expect_every_row(order_report: ReportsPage, header: str, value: str, *, exact: bool) -> None:
    for text in order_report.locators.column_cells(header).all_inner_texts():
        matches = text.strip() == value if exact else value.lower() in text.lower()
        assert matches, f"{header} {text!r} does not match the filter {value!r}"


# Navigation


@pytest.mark.smoke
def test_order_report_opens_from_reports_menu(order_report: ReportsPage) -> None:
    locators = order_report.locators
    expect(order_report.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    expect(locators.report_tab("Order Report")).to_be_visible()
    expect(locators.report_tab("Order Report")).to_have_class(ACTIVE_TAB)


# Visibility


@pytest.mark.smoke
def test_page_header_elements_are_visible(order_report: ReportsPage) -> None:
    locators = order_report.locators
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.help_button).to_be_visible()
    expect(locators.request_report_button).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("tab", REPORT_TABS)
def test_report_tab_is_visible(order_report: ReportsPage, tab: str) -> None:
    expect(order_report.locators.report_tab(tab)).to_be_visible()


@pytest.mark.smoke
def test_filters_and_controls_are_visible(order_report: ReportsPage) -> None:
    locators = order_report.locators
    expect(locators.channel_select).to_be_visible()
    expect(locators.order_status_select).to_be_visible()
    expect(locators.buyer_name_input).to_be_visible()
    expect(locators.part_number_input).to_be_visible()
    expect(locators.order_id_input).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()
    expect(locators.show_entries_select).to_be_visible()


@pytest.mark.smoke
def test_table_is_visible(order_report: ReportsPage) -> None:
    expect(order_report.locators.table).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(order_report: ReportsPage, header: str) -> None:
    expect(order_report.locators.column_header(header)).to_be_visible()


@pytest.mark.smoke
def test_footer_and_pagination_are_visible(order_report: ReportsPage) -> None:
    locators = order_report.locators
    expect(locators.showing_entries_text).to_be_visible()
    expect(locators.previous_button).to_be_visible()
    expect(locators.page_number_button).to_be_visible()
    expect(locators.next_button).to_be_visible()


# Filters


@pytest.mark.functional
@pytest.mark.parametrize(
    ("field", "header"),
    [("channel_select", "Channel"), ("order_status_select", "Order Status")],
    ids=["Channel", "Order Status"],
)
def test_dropdown_filter(order_report: ReportsPage, field: str, header: str) -> None:
    select = getattr(order_report.locators, field)
    options = order_report.option_labels(select)
    if not options:
        pytest.skip(f"{header} offers no option besides its default")
    # A value some visible row holds, so the result is not empty whenever possible.
    value = order_report.first_value(header)
    value = value if value in options else options[0]
    order_report.select_option(select, value, f"{header} filter")
    order_report.apply_filters()

    _expect_valid_result(order_report)
    _expect_every_row(order_report, header, value, exact=True)


@pytest.mark.functional
@pytest.mark.parametrize(
    ("field", "header"),
    [("buyer_name_input", "Buyer Name"), ("part_number_input", "Part Number"), ("order_id_input", "Order Id")],
    ids=["Buyer Name", "Part#", "Order ID"],
)
def test_text_filter(order_report: ReportsPage, field: str, header: str) -> None:
    value = order_report.first_value(header) or SEARCH_VALUE
    order_report.fill(getattr(order_report.locators, field), value, f"{header} filter")
    order_report.apply_filters()

    _expect_valid_result(order_report)
    if value != SEARCH_VALUE:
        expect(order_report.locators.data_rows.first).to_be_visible()
    _expect_every_row(order_report, header, value, exact=False)


@pytest.mark.functional
def test_combined_filters(order_report: ReportsPage) -> None:
    locators = order_report.locators
    channels = order_report.option_labels(locators.channel_select)
    statuses = order_report.option_labels(locators.order_status_select)
    if not channels or not statuses:
        pytest.skip("Channel or Order Status offers no option besides its default")
    # Prefer the Channel + Order Status pair of one visible row, so both filters can match together.
    channel, status = channels[0], statuses[0]
    rows = zip(
        locators.column_cells("Channel").all_inner_texts(),
        locators.column_cells("Order Status").all_inner_texts(),
    )
    for row_channel, row_status in rows:
        if row_channel.strip() in channels and row_status.strip() in statuses:
            channel, status = row_channel.strip(), row_status.strip()
            break
    order_report.select_option(locators.channel_select, channel, "Channel filter")
    order_report.select_option(locators.order_status_select, status, "Order Status filter")
    order_report.apply_filters()

    _expect_valid_result(order_report)
    _expect_every_row(order_report, "Channel", channel, exact=True)
    _expect_every_row(order_report, "Order Status", status, exact=True)


@pytest.mark.functional
def test_reset_clears_filters(order_report: ReportsPage) -> None:
    locators = order_report.locators
    expect(locators.body_rows.first).to_be_visible()
    initial_rows = locators.data_rows.count()
    statuses = order_report.option_labels(locators.order_status_select)
    if statuses:
        order_report.select_option(locators.order_status_select, statuses[0], "Order Status filter")
    order_report.fill(locators.buyer_name_input, SEARCH_VALUE, "Buyer Name filter")
    order_report.fill(locators.part_number_input, SEARCH_VALUE, "Part# filter")
    order_report.fill(locators.order_id_input, SEARCH_VALUE, "Order ID filter")
    order_report.apply_filters()
    expect(locators.no_results_message).to_be_visible()

    order_report.reset_filters()

    expect(locators.channel_select).to_have_value("")  # "All Channels"
    expect(locators.order_status_select).to_have_value("")  # "All"
    expect(locators.buyer_name_input).to_have_value("")
    expect(locators.part_number_input).to_have_value("")
    expect(locators.order_id_input).to_have_value("")
    _expect_valid_result(order_report)
    expect(locators.data_rows).to_have_count(initial_rows)
