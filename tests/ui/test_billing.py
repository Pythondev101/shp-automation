"""My Account → Billing: visibility of the page's summary, table controls, column headers and pagination.

Visibility only. No billing value is verified and nothing on the page is clicked
(no Invoice, sorting, Show entries or pagination). The page comes from the
``authenticated_page`` fixture (one sign-in per browser per run).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.billing_locators import COLUMN_HEADERS
from framework.pages.billing_page import BillingPage

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


@pytest.fixture
def billing(authenticated_page: Page) -> BillingPage:
    """The Billing page, opened through the sidebar of the signed-in dashboard."""
    page = BillingPage(authenticated_page)
    page.show_full_table()
    page.open_from_sidebar()
    return page


def test_billing_page_opens_successfully(billing: BillingPage) -> None:
    expect(billing.locators.page_heading).to_be_visible()


def test_current_plan_section_is_visible(billing: BillingPage) -> None:
    locators = billing.locators
    expect(locators.current_plan_label).to_be_visible()
    expect(locators.current_plan_section).to_be_visible()
    expect(locators.current_plan_name).to_be_visible()
    expect(locators.current_plan_amount).to_be_visible()
    expect(locators.current_plan_status_date).to_be_visible()


def test_table_and_its_controls_are_visible(billing: BillingPage) -> None:
    expect(billing.locators.show_entries_select).to_be_visible()
    expect(billing.locators.table).to_be_visible()


@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(billing: BillingPage, header: str) -> None:
    expect(billing.locators.column_header(header)).to_be_visible()


def test_pagination_area_is_visible(billing: BillingPage) -> None:
    locators = billing.locators
    expect(locators.pagination).to_be_visible()
    expect(locators.previous_button).to_be_visible()
    expect(locators.current_page).to_be_visible()
    expect(locators.next_button).to_be_visible()
