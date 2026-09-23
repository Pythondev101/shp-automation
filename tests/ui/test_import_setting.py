"""Setup → Import Setting: navigation and visibility only.

The page is reached through the sidebar "Setup" → "Import Setting" link and comes from the
``authenticated_page`` fixture (one sign-in per browser per run). Visibility only: no filter,
button, link or table behaviour is exercised, and nothing is created, edited or deleted.
The empty-state checks are dynamic - they hold whether the table is empty (as it is today)
or holds import settings.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.import_setting_locators import COLUMN_HEADERS, PAGE_URL
from framework.pages.import_setting_page import ImportSettingPage

pytestmark = [pytest.mark.regression, pytest.mark.smoke]


@pytest.fixture
def import_setting(authenticated_page: Page) -> ImportSettingPage:
    """The Import Setting page, opened through the signed-in sidebar."""
    page = ImportSettingPage(authenticated_page)
    page.open_from_sidebar()
    return page


# Navigation


def test_import_setting_opens_from_setup_menu(import_setting: ImportSettingPage) -> None:
    locators = import_setting.locators
    expect(locators.sidebar_submenu).to_be_visible()
    expect(import_setting.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    expect(locators.import_setting_link).to_have_attribute("aria-current", "page")


# Page visibility


def test_page_header_elements_are_visible(import_setting: ImportSettingPage) -> None:
    locators = import_setting.locators
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.help_button).to_be_visible()
    expect(locators.add_setup_button).to_be_visible()


def test_filters_and_controls_are_visible(import_setting: ImportSettingPage) -> None:
    locators = import_setting.locators
    expect(locators.name_label).to_be_visible()
    expect(locators.name_input).to_be_visible()
    expect(locators.setup_type_select).to_be_visible()
    expect(locators.setup_files_select).to_be_visible()
    expect(locators.status_select).to_be_visible()
    expect(locators.search_button).to_be_visible()
    expect(locators.reset_button).to_be_visible()
    expect(locators.show_entries_select).to_be_visible()


def test_table_is_visible(import_setting: ImportSettingPage) -> None:
    expect(import_setting.locators.table).to_be_visible()


@pytest.mark.parametrize("header", COLUMN_HEADERS)
def test_table_header_is_visible(import_setting: ImportSettingPage, header: str) -> None:
    expect(import_setting.locators.column_header(header)).to_be_visible()


# Empty / no-data state (dynamic: holds with and without import settings)


def test_empty_state_is_visible_while_no_import_setting_exists(import_setting: ImportSettingPage) -> None:
    locators = import_setting.locators
    response = import_setting.last_list_response
    assert response is not None and response.ok, f"Table request failed: {response and response.status}"
    # The table structure stays visible in both states.
    expect(locators.table).to_be_visible()
    expect(locators.body_rows.first).to_be_visible()

    if locators.data_rows.count() == 0:
        expect(locators.empty_state_cell).to_be_visible()
        expect(locators.no_settings_message).to_be_visible()
        expect(locators.empty_state_add_setup_button).to_be_visible()
        expect(locators.read_guide_button).to_be_visible()
    else:
        # Import settings exist, so the empty state is gone; the page controls must still be there.
        expect(locators.empty_state_cell).to_have_count(0)
        expect(locators.page_heading).to_be_visible()
        expect(locators.add_setup_button).to_be_visible()
        expect(locators.search_button).to_be_visible()
        expect(locators.reset_button).to_be_visible()
