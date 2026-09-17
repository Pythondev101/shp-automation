"""Customer: visibility of the page header, filter bar, table, column headers and empty-state message.

Visibility only. No customer data is verified and nothing on the page is clicked
(no Search, Reset, Export, Date Range, Channel filter, sorting or Show entries). The
page comes from the ``authenticated_page`` fixture (one sign-in per browser per run).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.customer_locators import COLUMN_HEADERS
from framework.pages.customer_page import CustomerPage

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


@pytest.fixture
def customer(authenticated_page: Page) -> CustomerPage:
    """The Customer page, opened through the sidebar of the signed-in dashboard."""
    page = CustomerPage(authenticated_page)
    page.show_full_table()
    page.open_from_sidebar()
    return page


def test_customer_page_opens_successfully(customer: CustomerPage) -> None:
    expect(customer.locators.page_heading).to_be_visible()


def test_page_header_elements_are_visible(customer: CustomerPage) -> None:
    locators = customer.locators
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.export_button).to_be_visible()
    expect(locators.access_logging_message).to_be_visible()


def test_filter_bar_is_visible(customer: CustomerPage) -> None:
    locators = customer.locators
    expect(locators.customer_name_label).to_be_visible()
    expect(locators.customer_name_input).to_be_visible()
    expect(locators.order_id_label).to_be_visible()
    expect(locators.order_id_input).to_be_visible()
    expect(locators.date_range_input).to_be_visible()
    expect(locators.channel_select).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()
    expect(locators.export_info_text).to_be_visible()


def test_table_and_its_controls_are_visible(customer: CustomerPage) -> None:
    expect(customer.locators.show_entries_select).to_be_visible()
    expect(customer.locators.table).to_be_visible()


@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(customer: CustomerPage, header: str) -> None:
    expect(customer.locators.column_header(header)).to_be_visible()


def test_empty_state_message_is_visible_when_no_customers(customer: CustomerPage) -> None:
    locators = customer.locators
    expect(locators.table_rows.first).to_be_visible()
    # The rows are only counted once the table has finished loading.
    expect(locators.loading_row).to_have_count(0)
    if locators.first_row_cells.count() > 1:
        pytest.skip("The customer table holds data, so there is no empty-state message")
    expect(locators.empty_state_row).to_be_visible()
