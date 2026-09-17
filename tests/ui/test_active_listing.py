"""Active Listing: visibility of a channel's product page – header, filter bar, table controls and column headers.

Visibility only. No product data is verified and nothing on the page is clicked
(no Search, Reset, Show entries, Show all columns, sorting, Edit or row actions). The
channel is the first one the "Active Listing" sidebar sub-menu lists, never a hard-coded
name. The page comes from the ``authenticated_page`` fixture (one sign-in per browser per run).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.active_listing_locators import COLUMN_HEADERS, PAGE_URL
from framework.pages.active_listing_page import ActiveListingPage

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


@pytest.fixture
def active_listing(authenticated_page: Page) -> ActiveListingPage:
    """The Active Listing page of the first listed channel, opened through the signed-in sidebar."""
    page = ActiveListingPage(authenticated_page)
    page.show_full_table()
    page.open_first_channel_from_sidebar()
    return page


def test_active_listing_page_opens_successfully(active_listing: ActiveListingPage) -> None:
    expect(active_listing.page).to_have_url(PAGE_URL)
    expect(active_listing.locators.page_heading).to_be_visible()


def test_page_header_elements_are_visible(active_listing: ActiveListingPage) -> None:
    expect(active_listing.locators.breadcrumb).to_be_visible()
    expect(active_listing.locators.help_button).to_be_visible()


def test_filter_bar_is_visible(active_listing: ActiveListingPage) -> None:
    locators = active_listing.locators
    expect(locators.upc_number_label).to_be_visible()
    expect(locators.upc_number_input).to_be_visible()
    expect(locators.sku_label).to_be_visible()
    expect(locators.sku_input).to_be_visible()
    expect(locators.title_label).to_be_visible()
    expect(locators.title_input).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()


def test_table_and_its_controls_are_visible(active_listing: ActiveListingPage) -> None:
    locators = active_listing.locators
    expect(locators.show_entries_select).to_be_visible()
    expect(locators.show_all_columns_button).to_be_visible()
    expect(locators.table).to_be_visible()


@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(active_listing: ActiveListingPage, header: str) -> None:
    expect(active_listing.locators.column_header(header)).to_be_visible()


def test_empty_state_message_is_visible_when_no_products(active_listing: ActiveListingPage) -> None:
    locators = active_listing.locators
    expect(locators.table_rows.first).to_be_visible()
    # The rows are only counted once the table has finished loading.
    expect(locators.loading_row).to_have_count(0)
    # A single cell spanning the table is the message row; its dynamic text is not checked.
    expect(locators.first_row_cells.first).to_be_visible()
    if locators.first_row_cells.count() > 1:
        pytest.skip("The product table holds data, so there is no empty-state message")
    expect(locators.first_row_cells).to_have_count(1)
