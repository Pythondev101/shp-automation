"""My Account → SMTP Settings: navigation and visibility only.

The page is reached through the sidebar "My Account" → "SMTP Settings" link and comes from
the ``authenticated_page`` fixture (one sign-in per browser per run). Visibility only: no
button, control or table behaviour is exercised, nothing is created, edited, deleted or
sent, and no SMTP connection is made. The empty-state checks are dynamic - they hold
whether the table is empty (as it is today) or holds SMTP settings.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.smtp_settings_locators import COLUMN_HEADERS, PAGE_URL
from framework.pages.smtp_settings_page import SmtpSettingsPage

pytestmark = [pytest.mark.regression, pytest.mark.smoke]


@pytest.fixture
def smtp_settings(authenticated_page: Page) -> SmtpSettingsPage:
    """The SMTP Settings page, opened through the signed-in sidebar."""
    page = SmtpSettingsPage(authenticated_page)
    page.open_from_sidebar()
    return page


# Navigation


def test_smtp_settings_opens_from_my_account_menu(smtp_settings: SmtpSettingsPage) -> None:
    locators = smtp_settings.locators
    expect(locators.sidebar_submenu).to_be_visible()
    expect(smtp_settings.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    # SMTP Settings stays the selected sub-menu entry.
    expect(locators.smtp_settings_link).to_have_attribute("aria-current", "page")


# Page visibility


def test_page_header_elements_are_visible(smtp_settings: SmtpSettingsPage) -> None:
    locators = smtp_settings.locators
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.add_new_button).to_be_visible()


def test_show_entries_control_is_visible(smtp_settings: SmtpSettingsPage) -> None:
    expect(smtp_settings.locators.show_entries_select).to_be_visible()


def test_table_is_visible(smtp_settings: SmtpSettingsPage) -> None:
    expect(smtp_settings.locators.table).to_be_visible()


@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(smtp_settings: SmtpSettingsPage, header: str) -> None:
    expect(smtp_settings.locators.column_header(header)).to_be_visible()


# Empty / no-data state (dynamic: holds with and without SMTP settings)


def test_empty_state_is_visible_while_no_smtp_setting_exists(smtp_settings: SmtpSettingsPage) -> None:
    locators = smtp_settings.locators
    response = smtp_settings.last_list_response
    assert response is not None and response.ok, f"Table request failed: {response and response.status}"
    # The table structure stays visible in both states.
    expect(locators.table).to_be_visible()
    expect(locators.body_rows.first).to_be_visible()

    if locators.data_rows.count() == 0:
        expect(locators.empty_state_cell).to_be_visible()
        expect(locators.no_settings_message).to_be_visible()
    else:
        # SMTP settings exist, so the empty state is gone; the page controls must still be there.
        expect(locators.empty_state_cell).to_have_count(0)
        expect(locators.page_heading).to_be_visible()
        expect(locators.add_new_button).to_be_visible()
        expect(locators.show_entries_select).to_be_visible()
