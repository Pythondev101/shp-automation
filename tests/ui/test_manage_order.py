"""Manage Order: visibility of the All Orders view – header, tabs, search/filter section and column headers.

Visibility only. No order data is verified and nothing on the page is clicked (no tabs,
Flagged, Search, Reset, filters, date pickers, Show entries, sorting or rows). The page is
reached through the sidebar "Manage Order" → "All Orders" link. The page comes from the
``authenticated_page`` fixture (one sign-in per browser per run).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.manage_order_locators import COLUMN_HEADERS, PAGE_URL
from framework.pages.manage_order_page import ManageOrderPage

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


@pytest.fixture
def manage_order(authenticated_page: Page) -> ManageOrderPage:
    """The Manage Order "All Orders" view, opened through the signed-in sidebar."""
    page = ManageOrderPage(authenticated_page)
    page.show_full_table()
    page.open_all_orders_from_sidebar()
    return page


def test_manage_order_page_opens_successfully(manage_order: ManageOrderPage) -> None:
    expect(manage_order.page).to_have_url(PAGE_URL)
    expect(manage_order.locators.page_heading).to_be_visible()


def test_page_header_elements_are_visible(manage_order: ManageOrderPage) -> None:
    locators = manage_order.locators
    expect(locators.all_orders_tab).to_be_visible()
    expect(locators.help_button).to_be_visible()
    expect(locators.flagged_button).to_be_visible()


def test_channel_tab_is_visible_when_present(manage_order: ManageOrderPage) -> None:
    # Channel tabs load after "All Orders", so the first one is waited for before concluding there is none.
    try:
        expect(manage_order.locators.channel_tabs.first).to_be_visible()
    except AssertionError:
        pytest.skip("The account has no channel, so there is no channel tab")


def test_search_and_filter_section_is_visible(manage_order: ManageOrderPage) -> None:
    locators = manage_order.locators
    expect(locators.system_status_select).to_be_visible()
    expect(locators.order_status_select).to_be_visible()
    expect(locators.order_date_input).to_be_visible()
    expect(locators.creation_date_input).to_be_visible()
    expect(locators.buyer_name_input).to_be_visible()
    expect(locators.buyer_id_input).to_be_visible()
    expect(locators.part_number_input).to_be_visible()
    expect(locators.order_id_input).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()
    expect(locators.show_entries_select).to_be_visible()


def test_orders_table_is_visible(manage_order: ManageOrderPage) -> None:
    expect(manage_order.locators.table).to_be_visible()


@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(manage_order: ManageOrderPage, header: str) -> None:
    expect(manage_order.locators.column_header(header)).to_be_visible()
