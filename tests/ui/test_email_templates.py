"""My Account → Email Templates: navigation and visibility only.

The page is reached through the sidebar "My Account" → "Email Templates" link and comes
from the ``authenticated_page`` fixture (one sign-in per browser per run). Visibility only:
no filter, button or table behaviour is exercised, and nothing is created, edited or
deleted. The empty-state checks are dynamic - they hold whether the table is empty (as it
is today) or holds email templates.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.email_templates_locators import COLUMN_HEADERS, PAGE_URL
from framework.pages.email_templates_page import EmailTemplatesPage

pytestmark = [pytest.mark.regression, pytest.mark.smoke]


@pytest.fixture
def email_templates(authenticated_page: Page) -> EmailTemplatesPage:
    """The Email Templates page, opened through the signed-in sidebar."""
    page = EmailTemplatesPage(authenticated_page)
    page.open_from_sidebar()
    return page


# Navigation


def test_email_templates_opens_from_my_account_menu(email_templates: EmailTemplatesPage) -> None:
    locators = email_templates.locators
    expect(locators.sidebar_submenu).to_be_visible()
    expect(email_templates.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    expect(locators.email_templates_link).to_have_attribute("aria-current", "page")


# Page visibility


def test_page_header_elements_are_visible(email_templates: EmailTemplatesPage) -> None:
    locators = email_templates.locators
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.add_template_button).to_be_visible()


def test_filters_and_controls_are_visible(email_templates: EmailTemplatesPage) -> None:
    locators = email_templates.locators
    expect(locators.name_label).to_be_visible()
    expect(locators.name_input).to_be_visible()
    expect(locators.status_select).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()
    expect(locators.show_entries_select).to_be_visible()


def test_table_is_visible(email_templates: EmailTemplatesPage) -> None:
    expect(email_templates.locators.table).to_be_visible()


@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(email_templates: EmailTemplatesPage, header: str) -> None:
    expect(email_templates.locators.column_header(header)).to_be_visible()


# Empty / no-data state (dynamic: holds with and without email templates)


def test_empty_state_is_visible_while_no_template_exists(email_templates: EmailTemplatesPage) -> None:
    locators = email_templates.locators
    response = email_templates.last_list_response
    assert response is not None and response.ok, f"Table request failed: {response and response.status}"
    # The table structure stays visible in both states.
    expect(locators.table).to_be_visible()
    expect(locators.body_rows.first).to_be_visible()

    if locators.data_rows.count() == 0:
        expect(locators.empty_state_cell).to_be_visible()
        expect(locators.no_templates_message).to_be_visible()
    else:
        # Templates exist, so the empty state is gone; the page controls must still be there.
        expect(locators.empty_state_cell).to_have_count(0)
        expect(locators.page_heading).to_be_visible()
        expect(locators.add_template_button).to_be_visible()
        expect(locators.search_button).to_be_visible()
        expect(locators.reset_button).to_be_visible()
