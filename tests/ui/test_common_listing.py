"""Listing → Common Listing: navigation, visibility and the search filters.

The page is reached through the sidebar "Listing" → "Common Listing" and comes from the
``authenticated_page`` fixture (one sign-in per browser per run). Listing data is dynamic:
filter values are taken from the visible rows or the dropdown options, and every check
holds whether the filtered table has rows or shows its empty state. Create Listing, Edit,
the row detail columns, Drafts, Product Images, sorting and pagination are out of scope.
"""

from __future__ import annotations

import re
from datetime import date

import pytest
from playwright.sync_api import Page, expect

from framework.locators.common_listing_locators import COLUMN_HEADERS, PAGE_URL
from framework.pages.common_listing_page import CommonListingPage

pytestmark = pytest.mark.regression

SEARCH_VALUE = "automation-test"
"""A harmless value typed into a text filter when no visible row offers one."""


@pytest.fixture
def common_listing(authenticated_page: Page) -> CommonListingPage:
    """The Common Listing page, opened through the signed-in sidebar."""
    page = CommonListingPage(authenticated_page)
    page.open_from_sidebar()
    return page


def _expect_valid_result(common_listing: CommonListingPage) -> None:
    """The latest table request succeeded and the table shows rows or its empty-state message."""
    locators = common_listing.locators
    response = common_listing.last_list_response
    assert response is not None and response.ok, f"Table request failed: {response and response.status}"
    expect(locators.page_heading).to_be_visible()
    expect(locators.table).to_be_visible()
    # The body always holds a row: either data or the empty-state message.
    expect(locators.body_rows.first).to_be_visible()
    if locators.data_rows.count() == 0:
        expect(locators.no_products_message).to_be_visible()
    else:
        expect(locators.no_products_message).to_have_count(0)


def _expect_every_row(common_listing: CommonListingPage, header: str, value: str, *, exact: bool) -> None:
    for text in common_listing.locators.column_cells(header).all_inner_texts():
        matches = text.strip().lower() == value.lower() if exact else value.lower() in text.lower()
        assert matches, f"{header} {text!r} does not match the filter {value!r}"


# Navigation


@pytest.mark.smoke
def test_common_listing_opens_from_listing_menu(common_listing: CommonListingPage) -> None:
    locators = common_listing.locators
    expect(locators.sidebar_submenu).to_be_visible()
    expect(common_listing.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    expect(locators.common_listing_link).to_have_attribute("aria-current", "page")


# Visibility


@pytest.mark.smoke
def test_page_header_elements_are_visible(common_listing: CommonListingPage) -> None:
    locators = common_listing.locators
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.help_button).to_be_visible()
    expect(locators.create_listing_button).to_be_visible()


@pytest.mark.smoke
def test_filters_and_controls_are_visible(common_listing: CommonListingPage) -> None:
    locators = common_listing.locators
    expect(locators.upc_number_input).to_be_visible()
    expect(locators.sku_input).to_be_visible()
    expect(locators.product_id_input).to_be_visible()
    expect(locators.title_input).to_be_visible()
    expect(locators.channel_select).to_be_visible()
    expect(locators.status_select).to_be_visible()
    expect(locators.published_date_input).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()
    expect(locators.show_entries_select).to_be_visible()


@pytest.mark.smoke
def test_table_is_visible(common_listing: CommonListingPage) -> None:
    expect(common_listing.locators.table).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(common_listing: CommonListingPage, header: str) -> None:
    expect(common_listing.locators.column_header(header)).to_be_visible()


# Filters


@pytest.mark.functional
@pytest.mark.parametrize(
    ("field", "header"),
    [
        ("upc_number_input", "UPC"),
        ("sku_input", "SKU"),
        ("product_id_input", "Product Id"),
        ("title_input", "Title"),
    ],
    ids=["UPC Number", "SKU", "Product Id", "Title"],
)
def test_text_filter(common_listing: CommonListingPage, field: str, header: str) -> None:
    value = common_listing.first_value(header) or SEARCH_VALUE
    common_listing.fill(getattr(common_listing.locators, field), value, f"{header} filter")
    common_listing.apply_filters()

    _expect_valid_result(common_listing)
    if value != SEARCH_VALUE:
        expect(common_listing.locators.data_rows.first).to_be_visible()
    _expect_every_row(common_listing, header, value, exact=False)


@pytest.mark.functional
@pytest.mark.parametrize(
    ("field", "header"),
    [("channel_select", "Channel Name"), ("status_select", "Status")],
    ids=["Channel Filter", "Status"],
)
def test_dropdown_filter(common_listing: CommonListingPage, field: str, header: str) -> None:
    select = getattr(common_listing.locators, field)
    options = common_listing.option_labels(select)
    if not options:
        pytest.skip(f"{header} offers no option besides its default")
    # A value some visible row holds, so the result is not empty whenever possible.
    value = common_listing.first_value(header)
    value = next((option for option in options if value and option.lower() == value.lower()), options[0])
    common_listing.select_option(select, value, f"{header} filter")
    common_listing.apply_filters()

    _expect_valid_result(common_listing)
    _expect_every_row(common_listing, header, value, exact=True)


@pytest.mark.functional
def test_published_date_filter(common_listing: CommonListingPage) -> None:
    today = date.today()
    common_listing.choose_published_date_range(today.replace(day=1), today)
    # The field shows the range as dd-mm-yyyy; only its end is checked so a one-day range also passes.
    expect(common_listing.locators.published_date_input).to_have_value(re.compile(rf"{today:%d-%m-%Y}$"))
    common_listing.apply_filters()

    _expect_valid_result(common_listing)


@pytest.mark.functional
def test_combined_filters(common_listing: CommonListingPage) -> None:
    locators = common_listing.locators
    channels = common_listing.option_labels(locators.channel_select)
    statuses = common_listing.option_labels(locators.status_select)
    if not channels or not statuses:
        pytest.skip("Channel Filter or Status offers no option besides its default")
    # Prefer the Channel Name + Status pair of one visible row, so both filters can match together.
    channel, status = channels[0], statuses[0]
    rows = zip(
        locators.column_cells("Channel Name").all_inner_texts(),
        locators.column_cells("Status").all_inner_texts(),
    )
    lower_channels = {option.lower(): option for option in channels}
    lower_statuses = {option.lower(): option for option in statuses}
    for row_channel, row_status in rows:
        if row_channel.strip().lower() in lower_channels and row_status.strip().lower() in lower_statuses:
            channel, status = lower_channels[row_channel.strip().lower()], lower_statuses[row_status.strip().lower()]
            break
    common_listing.select_option(locators.channel_select, channel, "Channel Filter")
    common_listing.select_option(locators.status_select, status, "Status filter")
    common_listing.apply_filters()

    _expect_valid_result(common_listing)
    _expect_every_row(common_listing, "Channel Name", channel, exact=True)
    _expect_every_row(common_listing, "Status", status, exact=True)


@pytest.mark.functional
def test_reset_clears_filters(common_listing: CommonListingPage) -> None:
    locators = common_listing.locators
    expect(locators.body_rows.first).to_be_visible()
    initial_rows = locators.data_rows.count()
    for select, description in ((locators.channel_select, "Channel Filter"), (locators.status_select, "Status filter")):
        options = common_listing.option_labels(select)
        if options:
            common_listing.select_option(select, options[0], description)
    common_listing.fill(locators.upc_number_input, SEARCH_VALUE, "UPC Number filter")
    common_listing.fill(locators.sku_input, SEARCH_VALUE, "SKU filter")
    common_listing.fill(locators.product_id_input, SEARCH_VALUE, "Product Id filter")
    common_listing.fill(locators.title_input, SEARCH_VALUE, "Title filter")
    today = date.today()
    common_listing.choose_published_date_range(today, today)
    common_listing.apply_filters()
    expect(locators.no_products_message).to_be_visible()

    common_listing.reset_filters()

    expect(locators.upc_number_input).to_have_value("")
    expect(locators.sku_input).to_have_value("")
    expect(locators.product_id_input).to_have_value("")
    expect(locators.title_input).to_have_value("")
    expect(locators.channel_select).to_have_value("")  # "All Channels"
    expect(locators.status_select).to_have_value("")  # "All"
    expect(locators.published_date_input).to_have_value("")
    _expect_valid_result(common_listing)
    expect(locators.data_rows).to_have_count(initial_rows)
