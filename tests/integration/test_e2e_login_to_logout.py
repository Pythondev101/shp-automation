"""End-to-end happy path: one user journey from the login page to sign-out, in one browser session.

The test signs in through the login form itself (not ``authenticated_page``), walks through every
automated module via the sidebar, and signs out through the header profile menu. Each module gets
only the checks that show it opened; the module tests in ``tests/ui`` cover the details.

Data: the journey connects one ``AUTOMATION TEST CHANNEL <hex>`` sandbox channel and raises one
``AUTOMATION TEST CASE <hex>`` Help Center case, and deletes both again before signing out. The
``automation_records`` fixture deletes whatever the test did not, pass or fail. Profile, password,
plan and Auto-Pay are only viewed, never changed.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from framework.config import Credentials
from framework.locators.active_listing_locators import PAGE_URL as ACTIVE_LISTING_URL
from framework.locators.manage_channel_locators import CONNECTABLE_PLATFORM, SIDEBAR_CHANNEL_MENUS
from framework.locators.manage_order_locators import PAGE_URL as MANAGE_ORDER_URL
from framework.pages.active_listing_page import ActiveListingPage
from framework.pages.billing_page import BillingPage
from framework.pages.customer_page import CustomerPage
from framework.pages.dashboard_page import DashboardPage
from framework.pages.help_center_page import HelpCenterPage
from framework.pages.login_page import LoginPage
from framework.pages.manage_channel_page import AUTOMATION_CHANNEL_PREFIX, ManageChannelPage
from framework.pages.manage_order_page import ManageOrderPage
from framework.pages.my_profile_page import MyProfilePage
from framework.pages.training_videos_page import TrainingVideosPage
from framework.pages.upgrade_plan_page import UpgradePlanPage

logger = logging.getLogger(__name__)

CASE_SUBJECT_PREFIX = "AUTOMATION TEST CASE"
CASE_PRIORITY = "High"
LEFTOVER_LOOKUP_TIMEOUT_MS = 10_000


@dataclass
class AutomationRecords:
    """What the journey created and has not yet deleted; the fixture removes anything left."""

    channel_name: str | None = None
    case_description: str | None = None
    case_id: str | None = None
    leftovers: list[str] = field(default_factory=list)


@pytest.fixture
def automation_records(page: Page) -> Iterator[AutomationRecords]:
    """Delete the channel and case the journey created but did not delete, in the same signed-in context.

    A record is registered before it is submitted and cleared once the journey has verified its
    deletion, so this teardown only acts after a failure. A record that cannot be deleted is
    reported as a teardown ERROR next to the test's own failure.
    """
    records = AutomationRecords()
    context = page.context
    yield records
    if records.channel_name is None and records.case_description is None:
        return

    cleanup = context.new_page()
    cleanup.goto(LoginPage.DASHBOARD_PATH)
    if records.channel_name:
        try:
            channels = ManageChannelPage(cleanup)
            channels.use_full_table_viewport()
            channels.open()
            row = channels.locators.channel_row(records.channel_name)
            try:
                row.wait_for(timeout=LEFTOVER_LOOKUP_TIMEOUT_MS)
            except PlaywrightTimeoutError:
                logger.info("Channel %r is not listed; nothing to delete", records.channel_name)
            else:
                channels.delete_channel(records.channel_name)
                expect(row).to_have_count(0)
        except Exception as error:  # noqa: BLE001 - the case is still attempted, failures are reported below
            records.leftovers.append(f"channel {records.channel_name!r}: {error}")
    if records.case_description:
        try:
            cleanup.goto(LoginPage.DASHBOARD_PATH)
            help_center = HelpCenterPage(cleanup)
            help_center.show_full_table()
            help_center.open_from_sidebar()
            if help_center.delete_automation_case(records.case_description, records.case_id):
                expect(help_center.locators.case_row(records.case_description)).to_have_count(0)
        except Exception as error:  # noqa: BLE001 - reported below
            records.leftovers.append(f"case {records.case_id or 'Case Id unknown'} {records.case_description!r}: {error}")

    if records.leftovers:
        logger.error("E2E clean-up failed; left in the account: %s", records.leftovers)
        pytest.fail("E2E clean-up failed; left in the account:\n" + "\n".join(records.leftovers), pytrace=False)
    logger.info("E2E clean-up deleted the records the journey left behind")


@pytest.mark.e2e
@pytest.mark.regression
@pytest.mark.destructive
def test_user_journey_from_login_to_logout(
    page: Page, credentials: Credentials, base_url: str, automation_records: AutomationRecords
) -> None:
    # 1. Login, in the fresh browser context pytest-playwright gives this test.
    logger.info("E2E: sign in")
    login = LoginPage(page)
    login.open()
    expect(login.locators.heading).to_be_visible()
    login.login(credentials)
    expect(page).to_have_url(f"{base_url}{LoginPage.DASHBOARD_PATH}")
    expect(login.locators.signed_in_indicator).to_be_visible()
    expect(login.locators.password_input).to_have_count(0)

    # 2. Dashboard.
    logger.info("E2E: dashboard")
    dashboard = DashboardPage(page).locators
    expect(dashboard.welcome_heading).to_be_visible()
    expect(dashboard.profile_button).to_be_visible()
    expect(dashboard.orders_chart_heading).to_be_visible()

    # 3. Manage Channel: connect a sandbox channel. The authorisation returns in a new tab (D34),
    # which carries the rest of the journey; the stale starting tab is closed.
    logger.info("E2E: Manage Channel - connect an automation channel")
    channels = ManageChannelPage(page)
    channels.use_full_table_viewport()
    channels.open_from_sidebar()
    expect(channels.locators.page_heading).to_be_visible()
    channel_name = f"{AUTOMATION_CHANNEL_PREFIX} {uuid.uuid4().hex[:8].upper()}"
    automation_records.channel_name = channel_name
    channels.open_add_connection_popup()
    channels.select_platform(CONNECTABLE_PLATFORM)
    channels.enter_channel_name(channel_name)
    channels = channels.authorize_in_sandbox()
    page.close()
    app = channels.page
    channels.use_full_table_viewport()
    expect(channels.locators.connected_message).to_be_visible()
    expect(channels.locators.channel_row(channel_name)).to_be_visible()

    # 4. Active Listing: the new channel is listed in the sub-menu; the first channel's listing opens.
    logger.info("E2E: Active Listing")
    channels.expand_sidebar_menu(SIDEBAR_CHANNEL_MENUS[0])
    expect(channels.locators.sidebar_submenu_channel(SIDEBAR_CHANNEL_MENUS[0], channel_name)).to_be_visible()
    active_listing = ActiveListingPage(app)
    active_listing.open_first_channel_from_sidebar()
    expect(app).to_have_url(ACTIVE_LISTING_URL)
    expect(active_listing.locators.page_heading).to_be_visible()
    expect(active_listing.locators.table).to_be_visible()

    # 5. My Account -> My Profile (viewed only). The sidebar is an accordion: expanding one menu collapses
    # the others, so My Account's two entries are opened with another menu expanded in between.
    logger.info("E2E: My Profile")
    my_profile = MyProfilePage(app)
    my_profile.open_from_sidebar()
    expect(app).to_have_url(f"{base_url}{MyProfilePage.PATH}")
    expect(my_profile.locators.page_heading).to_be_visible()

    # 6. Manage Order: the new channel is listed in the sub-menu; All Orders opens.
    logger.info("E2E: Manage Order")
    channels.expand_sidebar_menu(SIDEBAR_CHANNEL_MENUS[1])
    expect(channels.locators.sidebar_submenu_channel(SIDEBAR_CHANNEL_MENUS[1], channel_name)).to_be_visible()
    manage_order = ManageOrderPage(app)
    manage_order.open_all_orders_from_sidebar()
    expect(app).to_have_url(MANAGE_ORDER_URL)
    expect(manage_order.locators.page_heading).to_be_visible()
    expect(manage_order.locators.table).to_be_visible()

    # 7. My Account -> Billing (viewed only).
    logger.info("E2E: Billing")
    billing = BillingPage(app)
    billing.open_from_sidebar()
    expect(billing.locators.page_heading).to_be_visible()
    expect(billing.locators.table).to_be_visible()

    # 8. Help Center: raise an automation case, find it, delete it.
    logger.info("E2E: Help Center - raise and delete an automation case")
    help_center = HelpCenterPage(app)
    help_center.open_from_sidebar()
    expect(help_center.locators.page_heading).to_be_visible()
    tag = secrets.token_hex(4)
    description = f"{HelpCenterPage.AUTOMATION_CASE_DESCRIPTION_PREFIX}{tag}"
    automation_records.case_description = description
    help_center.raise_case(CASE_PRIORITY, f"{CASE_SUBJECT_PREFIX} {tag}", description)
    expect(help_center.locators.case_raised_toast).to_be_visible()
    case_row = help_center.locators.case_row(description)
    expect(case_row).to_have_count(1)
    case_id = help_center.case_id_of(case_row)
    automation_records.case_id = case_id
    assert help_center.delete_automation_case(description, case_id), f"Case {case_id} was not listed for deletion"
    expect(help_center.locators.case_deleted_toast).to_be_visible()
    expect(help_center.locators.case_row_by_id(case_id)).to_have_count(0)
    automation_records.case_description = automation_records.case_id = None

    # 9. Training Videos (viewed only; no video is played).
    logger.info("E2E: Training Videos")
    training_videos = TrainingVideosPage(app)
    training_videos.open_from_sidebar()
    expect(app).to_have_url(f"{base_url}{TrainingVideosPage.PATH}")
    expect(training_videos.locators.page_heading).to_be_visible()
    expect(training_videos.locators.video_cards.first).to_be_visible()

    # 10. Upgrade Plan (viewed only; the plan is never changed).
    logger.info("E2E: Upgrade Plan")
    upgrade_plan = UpgradePlanPage(app)
    upgrade_plan.open_from_sidebar()
    expect(upgrade_plan.locators.page_heading).to_be_visible()
    upgrade_plan.wait_for_plans()
    assert upgrade_plan.current_plan_name(), "No plan card is marked as the current plan"

    # 11. Customer (viewed only).
    logger.info("E2E: Customer")
    customer = CustomerPage(app)
    customer.open_from_sidebar()
    expect(customer.locators.page_heading).to_be_visible()
    expect(customer.locators.table).to_be_visible()

    # 12. Manage Channel: delete the automation channel again.
    logger.info("E2E: Manage Channel - delete the automation channel")
    channels.open_from_sidebar()
    expect(channels.locators.page_heading).to_be_visible()
    channels.delete_channel(channel_name)
    expect(channels.locators.delete_popup).to_be_hidden()
    expect(channels.locators.channel_row(channel_name)).to_have_count(0)
    automation_records.channel_name = None

    # 13. Sign out, and the signed-out session cannot reach a signed-in page.
    logger.info("E2E: sign out")
    DashboardPage(app).sign_out()
    signed_out = LoginPage(app)
    expect(app).to_have_url(f"{base_url}{LoginPage.PATH}")
    expect(signed_out.locators.heading).to_be_visible()
    expect(signed_out.locators.signed_in_indicator).to_have_count(0)
    app.goto(LoginPage.DASHBOARD_PATH)
    expect(app).to_have_url(f"{base_url}{LoginPage.PATH}")
    expect(signed_out.locators.heading).to_be_visible()
