"""Order Logs → Order Tracking: navigation, visibility, empty-state handling and the filters.

The page is reached through the sidebar "Order Logs" → "Order Tracking" link and comes
from the ``authenticated_page`` fixture (one sign-in per browser per run). No order data
is hardcoded: every check holds whether the table is empty (as it is today) or has rows.
Nothing is created, edited or deleted; Order Processing, sorting, order and tracking details are out of scope.
"""

from __future__ import annotations

import re
from datetime import date

import pytest
from playwright.sync_api import Page, expect

from framework.locators.order_tracking_locators import COLUMN_HEADERS, PAGE_URL
from framework.pages.order_tracking_page import OrderTrackingPage

pytestmark = pytest.mark.regression

SEARCH_VALUE = "automation-test"
"""A harmless value typed into the text filters."""


@pytest.fixture
def order_tracking(authenticated_page: Page) -> OrderTrackingPage:
    """The Order Tracking page, opened through the signed-in sidebar."""
    page = OrderTrackingPage(authenticated_page)
    page.open_from_sidebar()
    return page


def _expect_valid_result(order_tracking: OrderTrackingPage) -> None:
    """The latest table request succeeded and the table shows rows or its empty-state message."""
    locators = order_tracking.locators
    response = order_tracking.last_list_response
    assert response is not None and response.ok, f"Table request failed: {response and response.status}"
    expect(locators.page_heading).to_be_visible()
    expect(locators.table).to_be_visible()
    # The body always holds a row: either data or the empty-state message.
    expect(locators.body_rows.first).to_be_visible()
    if locators.data_rows.count() == 0:
        expect(locators.no_records_message).to_be_visible()
    else:
        expect(locators.no_records_message).to_have_count(0)


def _expect_every_row_contains(order_tracking: OrderTrackingPage, header: str, value: str) -> None:
    for text in order_tracking.locators.column_cells(header).all_inner_texts():
        assert value.lower() in text.lower(), f"{header} {text!r} does not match the filter {value!r}"


# Navigation


@pytest.mark.smoke
def test_order_tracking_opens_from_order_logs_menu(order_tracking: OrderTrackingPage) -> None:
    locators = order_tracking.locators
    expect(locators.sidebar_submenu).to_be_visible()
    expect(order_tracking.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    expect(locators.order_tracking_link).to_have_attribute("aria-current", "page")


# Visibility


@pytest.mark.smoke
def test_page_heading_and_breadcrumb_are_visible(order_tracking: OrderTrackingPage) -> None:
    expect(order_tracking.locators.page_heading).to_be_visible()
    expect(order_tracking.locators.breadcrumb).to_be_visible()


@pytest.mark.smoke
def test_filters_and_controls_are_visible(order_tracking: OrderTrackingPage) -> None:
    locators = order_tracking.locators
    expect(locators.order_status_select).to_be_visible()
    expect(locators.date_range_input).to_be_visible()
    expect(locators.buyer_input).to_be_visible()
    expect(locators.part_number_input).to_be_visible()
    expect(locators.order_id_input).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()
    expect(locators.show_entries_select).to_be_visible()


@pytest.mark.smoke
def test_table_is_visible(order_tracking: OrderTrackingPage) -> None:
    expect(order_tracking.locators.table).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(order_tracking: OrderTrackingPage, header: str) -> None:
    expect(order_tracking.locators.column_header(header)).to_be_visible()


# No data


@pytest.mark.functional
def test_table_loads_with_rows_or_empty_state(order_tracking: OrderTrackingPage) -> None:
    _expect_valid_result(order_tracking)


@pytest.mark.functional
def test_controls_stay_usable_when_table_is_empty(order_tracking: OrderTrackingPage) -> None:
    locators = order_tracking.locators
    expect(locators.body_rows.first).to_be_visible()
    if locators.data_rows.count() > 0:
        pytest.skip("The table has rows, so there is no empty state to check")
    for control in (
        locators.order_status_select,
        locators.date_range_input,
        locators.buyer_input,
        locators.part_number_input,
        locators.order_id_input,
        locators.search_button,
        locators.reset_button,
        locators.show_entries_select,
    ):
        expect(control).to_be_enabled()
    expect(locators.buyer_input).to_be_editable()
    expect(locators.part_number_input).to_be_editable()
    expect(locators.order_id_input).to_be_editable()

    # Search sends no request while the filters are unchanged, so one is filled first.
    order_tracking.fill(locators.buyer_input, SEARCH_VALUE, "Buyer filter")
    order_tracking.apply_filters()
    _expect_valid_result(order_tracking)


# Filters


@pytest.mark.functional
def test_order_status_filter(order_tracking: OrderTrackingPage) -> None:
    options = order_tracking.status_options()
    if not options:
        pytest.skip("Order Status offers no status besides 'All'")
    order_tracking.select_order_status(options[0])
    order_tracking.apply_filters()

    _expect_valid_result(order_tracking)
    for text in order_tracking.locators.column_cells("Order Status").all_inner_texts():
        assert text.strip() == options[0], f"Order Status {text!r} does not match the filter {options[0]!r}"


@pytest.mark.functional
def test_date_range_filter(order_tracking: OrderTrackingPage) -> None:
    today = date.today()
    start = today.replace(day=1)
    order_tracking.choose_date_range(start, today)
    expect(order_tracking.locators.date_range_input).to_have_value(re.compile(rf"{today:%d-%m-%Y}$"))
    order_tracking.apply_filters()

    _expect_valid_result(order_tracking)


@pytest.mark.functional
@pytest.mark.parametrize(
    ("field", "header"),
    [("buyer_input", "Buyer"), ("part_number_input", "Part #"), ("order_id_input", "Order ID")],
    ids=["Buyer", "Part #", "Order ID"],
)
def test_text_filter(order_tracking: OrderTrackingPage, field: str, header: str) -> None:
    order_tracking.fill(getattr(order_tracking.locators, field), SEARCH_VALUE, f"{header} filter")
    order_tracking.apply_filters()

    _expect_valid_result(order_tracking)
    _expect_every_row_contains(order_tracking, header, SEARCH_VALUE)


@pytest.mark.functional
def test_reset_clears_filters(order_tracking: OrderTrackingPage) -> None:
    locators = order_tracking.locators
    today = date.today()
    order_tracking.choose_date_range(today, today)
    order_tracking.fill(locators.buyer_input, SEARCH_VALUE, "Buyer filter")
    order_tracking.fill(locators.part_number_input, SEARCH_VALUE, "Part # filter")
    order_tracking.fill(locators.order_id_input, SEARCH_VALUE, "Order ID filter")
    order_tracking.apply_filters()

    order_tracking.reset_filters()

    expect(locators.order_status_select).to_have_value("")  # "All"
    expect(locators.date_range_input).to_have_value("")
    expect(locators.buyer_input).to_have_value("")
    expect(locators.part_number_input).to_have_value("")
    expect(locators.order_id_input).to_have_value("")
    _expect_valid_result(order_tracking)
