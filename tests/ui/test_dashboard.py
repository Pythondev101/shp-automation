"""Dashboard: visibility of the page's UI elements for the signed-in automation account.

Presence only: counts, earnings, chart data and percentages are dynamic and not
verified. Nothing is clicked, so no navigation happens and no application data changes.
The page comes from the ``authenticated_page`` fixture (one sign-in per browser per run).
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from framework.pages.dashboard_page import DashboardPage

pytestmark = [pytest.mark.smoke, pytest.mark.regression]

PLAN_EXPIRED_NOTICE = re.compile(r"^Your plan expired")
"""Start of the notice the Upgrade Plan page shows while the account's plan has run out."""


@pytest.fixture
def dashboard(authenticated_page: Page) -> DashboardPage:
    """The dashboard, signed in with the .env account (authenticated_page opens it)."""
    return DashboardPage(authenticated_page)


def test_sidebar_branding_and_menu_are_visible(dashboard: DashboardPage) -> None:
    locators = dashboard.locators
    expect(locators.brand_logo).to_be_visible()
    expect(locators.brand_name).to_be_visible()
    expect(locators.dashboard_menu).to_be_visible()
    expect(locators.active_listing_menu).to_be_visible()
    expect(locators.manage_order_menu).to_be_visible()
    expect(locators.manage_channel_menu).to_be_visible()
    expect(locators.my_account_menu).to_be_visible()
    expect(locators.help_center_menu).to_be_visible()
    expect(locators.training_videos_menu).to_be_visible()
    expect(locators.upgrade_plan_menu).to_be_visible()
    expect(locators.customer_menu).to_be_visible()


def test_header_elements_are_visible(dashboard: DashboardPage) -> None:
    locators = dashboard.locators
    expect(locators.search_input).to_be_visible()
    expect(locators.notifications_button).to_be_visible()
    expect(locators.profile_button).to_be_visible()


def test_dashboard_sections_are_visible(dashboard: DashboardPage, base_url: str) -> None:
    locators = dashboard.locators
    expect(dashboard.page).to_have_url(f"{base_url}{DashboardPage.PATH}")
    # While the account's plan has expired, the application sends /dashboard on to /upgrade-plan
    # and never renders the dashboard (seen 2026-10-28). That is an account state, not a page
    # defect, so the test skips and names the cause instead of reporting a missing heading.
    plan_expired_notice = dashboard.page.get_by_role("main").get_by_text(PLAN_EXPIRED_NOTICE)
    expect(locators.welcome_heading.or_(plan_expired_notice)).to_be_visible()
    if plan_expired_notice.is_visible():
        pytest.skip(
            f"The dashboard is unavailable: /dashboard redirects to {dashboard.page.url} "
            f"({plan_expired_notice.inner_text()}). Renew the automation account's plan."
        )
    expect(locators.welcome_heading).to_be_visible()
    expect(locators.active_orders_card).to_be_visible()
    expect(locators.today_order_card).to_be_visible()
    expect(locators.this_month_earnings_label).to_be_visible()
    expect(locators.orders_chart_heading).to_be_visible()
    expect(locators.orders_chart).to_be_visible()
    expect(locators.channels_heading).to_be_visible()
    expect(locators.channels_date_range_input).to_be_visible()
    expect(locators.top_performing_products_heading).to_be_visible()
    expect(locators.recent_orders_heading).to_be_visible()
    expect(locators.common_order_status_heading).to_be_visible()
    expect(locators.warehouse_order_status_heading).to_be_visible()
