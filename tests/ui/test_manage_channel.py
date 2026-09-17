"""Manage Channel: page visibility and the "Add a new connection" popup.

The page is reached by clicking the "Manage Channel" sidebar menu only; no other
menu entry is used.

**Visibility tests** check presence only: the existing channel rows and their
values (channel name, token expiry, status, config date, cron slot) are data and
are not verified, and nothing on the page is clicked.

**Popup tests** click "+ Add New" and work inside the popup only: they choose a
platform, type a channel name and leave through Cancel. They never press Next
with a valid channel name, so no channel is created by them. The existing EBAY
channel is only read.

**Connect and delete tests** run the whole journey against SHP's local dev
sandbox: they create one channel under a unique automation name, verify it, then
delete it again through all three confirmation stages. Only that channel is ever
deleted – ``ManageChannelPage.delete_channel`` refuses any other name – and every
test checks that the account's real channel is still there afterwards.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from playwright.sync_api import Page, expect

from framework.locators.manage_channel_locators import (
    COLUMN_HEADERS,
    COMING_SOON_PLATFORMS,
    CONNECTABLE_PLATFORM,
    PLATFORMS,
    SIDEBAR_CHANNEL_MENUS,
)
from framework.pages.manage_channel_page import AUTOMATION_CHANNEL_PREFIX, ManageChannelPage

pytestmark = [pytest.mark.regression]

EXISTING_CHANNEL_NAME = "EBAY"
"""The account's real channel. Tests only read it; it is never edited or deleted."""

TEST_CHANNEL_NAME = AUTOMATION_CHANNEL_PREFIX
"""Name typed into the popup. Nothing is submitted, so no channel of this name is created."""

COUNTDOWN_TIMEOUT_MS = 20_000
"""The delete flow's second stage counts down for a few seconds before it can be confirmed."""


def unique_channel_name() -> str:
    """A channel name no other run, browser or test shares, so its row is addressable."""
    return f"{AUTOMATION_CHANNEL_PREFIX} {uuid.uuid4().hex[:8].upper()}"


@pytest.fixture
def manage_channel(authenticated_page: Page) -> ManageChannelPage:
    """The Manage Channel page, opened from the sidebar of the signed-in dashboard."""
    page = ManageChannelPage(authenticated_page)
    # Widen first: below 1600 px the page folds its last two columns out of the DOM.
    page.use_full_table_viewport()
    page.open_from_sidebar()
    return page


@pytest.mark.smoke
def test_manage_channel_page_opens_successfully(manage_channel: ManageChannelPage, base_url: str) -> None:
    expect(manage_channel.page).to_have_url(f"{base_url}{ManageChannelPage.PATH}")
    expect(manage_channel.locators.page_heading).to_be_visible()


@pytest.mark.smoke
def test_page_header_elements_are_visible(manage_channel: ManageChannelPage) -> None:
    locators = manage_channel.locators
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.help_button).to_be_visible()
    expect(locators.add_new_button).to_be_visible()


@pytest.mark.smoke
def test_filter_bar_is_visible(manage_channel: ManageChannelPage) -> None:
    locators = manage_channel.locators
    expect(locators.channel_name_label).to_be_visible()
    expect(locators.channel_name_input).to_be_visible()
    expect(locators.connection_label).to_be_visible()
    expect(locators.connection_select).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()


@pytest.mark.smoke
def test_table_and_its_controls_are_visible(manage_channel: ManageChannelPage) -> None:
    locators = manage_channel.locators
    expect(locators.show_entries_select).to_be_visible()
    expect(locators.table).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(manage_channel: ManageChannelPage, header: str) -> None:
    expect(manage_channel.locators.column_header(header)).to_be_visible()


@pytest.mark.smoke
def test_pagination_area_is_visible(manage_channel: ManageChannelPage) -> None:
    locators = manage_channel.locators
    expect(locators.entry_count).to_be_visible()
    expect(locators.pagination).to_be_visible()
    # Previous / Next are disabled while one page of channels exists; visibility only.
    expect(locators.previous_button).to_be_visible()
    expect(locators.current_page).to_be_visible()
    expect(locators.next_button).to_be_visible()


# --- "Add a new connection" popup -------------------------------------------------
# Nothing is submitted: Next is pressed only with an empty channel name, which the
# popup rejects on the client side. Every popup test leaves through Cancel or ends
# with the popup still open, so no channel is created.


@pytest.fixture
def connection_popup(manage_channel: ManageChannelPage) -> ManageChannelPage:
    """The Manage Channel page with the "Add a new connection" popup open."""
    manage_channel.open_add_connection_popup()
    return manage_channel


@pytest.mark.functional
def test_add_new_opens_the_connection_popup(connection_popup: ManageChannelPage) -> None:
    locators = connection_popup.locators
    expect(locators.add_connection_popup).to_be_visible()
    expect(locators.popup_heading).to_be_visible()
    expect(locators.popup_next_button).to_be_visible()
    expect(locators.popup_cancel_button).to_be_visible()


@pytest.mark.functional
@pytest.mark.parametrize("platform", PLATFORMS)
def test_platform_option_is_visible(connection_popup: ManageChannelPage, platform: str) -> None:
    expect(connection_popup.locators.platform_option(platform)).to_be_visible()


@pytest.mark.functional
@pytest.mark.parametrize("platform", COMING_SOON_PLATFORMS)
def test_platform_that_is_not_released_cannot_be_selected(
    connection_popup: ManageChannelPage, platform: str
) -> None:
    """Shopify, Temu, Amazon and Walmart are offered but disabled ("Coming soon")."""
    expect(connection_popup.locators.platform_option(platform)).to_be_disabled()


@pytest.mark.functional
def test_ebay_platform_can_be_selected(connection_popup: ManageChannelPage) -> None:
    connection_popup.select_platform(CONNECTABLE_PLATFORM)
    locators = connection_popup.locators
    expect(locators.platform_option(CONNECTABLE_PLATFORM)).to_be_checked()
    # Choosing a platform reveals the Channel Name field in the same popup.
    expect(locators.popup_channel_name_input).to_be_visible()
    expect(locators.popup_channel_name_input).to_be_editable()


@pytest.mark.functional
def test_channel_name_field_accepts_the_test_value(connection_popup: ManageChannelPage) -> None:
    connection_popup.select_platform(CONNECTABLE_PLATFORM)
    connection_popup.enter_channel_name(TEST_CHANNEL_NAME)
    expect(connection_popup.locators.popup_channel_name_input).to_have_value(TEST_CHANNEL_NAME)


@pytest.mark.functional
def test_channel_name_is_required_to_continue(
    connection_popup: ManageChannelPage, base_url: str
) -> None:
    """Next without a channel name is rejected in the browser: the popup stays open."""
    connection_popup.select_platform(CONNECTABLE_PLATFORM)
    connection_popup.continue_connection()
    locators = connection_popup.locators
    expect(locators.popup_channel_name_error).to_be_visible()
    expect(locators.add_connection_popup).to_be_visible()
    expect(connection_popup.page).to_have_url(f"{base_url}{ManageChannelPage.PATH}")


@pytest.mark.functional
def test_cancel_closes_the_popup_without_creating_a_channel(
    connection_popup: ManageChannelPage,
) -> None:
    connection_popup.select_platform(CONNECTABLE_PLATFORM)
    connection_popup.enter_channel_name(TEST_CHANNEL_NAME)
    connection_popup.cancel_connection_popup()
    locators = connection_popup.locators
    expect(locators.add_connection_popup).to_be_hidden()
    expect(locators.channel_row(TEST_CHANNEL_NAME)).to_have_count(0)
    # The account's real channel is untouched.
    expect(locators.channel_row(EXISTING_CHANNEL_NAME)).to_be_visible()


# --- Connect a channel and delete it again ----------------------------------------
# These tests do create application data: one channel per test, named
# "AUTOMATION TEST CHANNEL <random>", which the same test deletes again. The
# fixture's clean-up removes it if the test did not get that far, and
# ManageChannelPage.delete_channel refuses every name that is not an automation one,
# so the account's real channel can never be removed.


@pytest.fixture
def connected_channel(
    manage_channel: ManageChannelPage,
) -> Iterator[tuple[ManageChannelPage, str]]:
    """A channel connected through the sandbox, with the page object that shows it.

    The sandbox sign-in opens in a new tab that is redirected back to the Channel
    Connection page, so the yielded page object is bound to that tab, not to the one
    the connection was started from.
    """
    channel_name = unique_channel_name()
    manage_channel.open_add_connection_popup()
    manage_channel.select_platform(CONNECTABLE_PLATFORM)
    manage_channel.enter_channel_name(channel_name)
    connected = manage_channel.authorize_in_sandbox()
    connected.use_full_table_viewport()

    yield connected, channel_name

    if connected.locators.channel_row(channel_name).count():
        connected.delete_channel(channel_name)


@pytest.mark.functional
@pytest.mark.destructive
def test_sandbox_authorization_connects_the_new_channel(
    connected_channel: tuple[ManageChannelPage, str], base_url: str
) -> None:
    """The authorisation completes and returns to Manage Channel with the new channel."""
    connected, channel_name = connected_channel
    locators = connected.locators
    expect(locators.connected_message).to_be_visible()
    expect(connected.page).to_have_url(f"{base_url}{ManageChannelPage.PATH}")
    expect(locators.page_heading).to_be_visible()
    expect(locators.channel_row(channel_name)).to_be_visible()
    # Connecting a channel left the account's real channel alone.
    expect(locators.channel_row(EXISTING_CHANNEL_NAME)).to_be_visible()


@pytest.mark.functional
@pytest.mark.destructive
def test_delete_removes_only_the_channel_the_test_created(
    connected_channel: tuple[ManageChannelPage, str],
) -> None:
    """All three delete stages, then the row is gone and the real channel is not."""
    connected, channel_name = connected_channel
    locators = connected.locators

    connected.open_delete_confirmation(channel_name)
    expect(locators.delete_popup).to_be_visible()
    expect(locators.delete_confirmation_heading).to_be_visible()
    expect(locators.delete_confirm_button).to_be_visible()

    connected.confirm_delete()
    expect(locators.delete_checking_heading).to_be_visible()
    expect(locators.delete_countdown_button).to_be_disabled()

    # The same modal becomes the last confirmation once the countdown has run out.
    expect(locators.delete_final_heading).to_be_visible(timeout=COUNTDOWN_TIMEOUT_MS)
    connected.confirm_delete_permanently()

    expect(locators.delete_popup).to_be_hidden()
    expect(locators.channel_row(channel_name)).to_have_count(0)
    expect(locators.channel_row(EXISTING_CHANNEL_NAME)).to_be_visible()


@pytest.mark.functional
@pytest.mark.destructive
def test_new_channel_appears_in_sidebar_submenus_until_deleted(
    connected_channel: tuple[ManageChannelPage, str],
) -> None:
    """The new channel is listed under Active Listing and Manage Order; then it is deleted.

    Only the sub-menu entries' presence is checked; neither sub-menu page is opened.
    """
    connected, channel_name = connected_channel
    locators = connected.locators
    expect(locators.channel_row(channel_name)).to_be_visible()

    # One menu at a time: the sidebar is an accordion.
    for menu in SIDEBAR_CHANNEL_MENUS:
        connected.expand_sidebar_menu(menu)
        expect(locators.sidebar_submenu_channel(menu, channel_name)).to_be_visible()

    connected.open_from_sidebar()
    expect(locators.page_heading).to_be_visible()
    connected.delete_channel(channel_name)

    expect(locators.delete_popup).to_be_hidden()
    expect(locators.channel_row(channel_name)).to_have_count(0)
    expect(locators.channel_row(EXISTING_CHANNEL_NAME)).to_be_visible()
