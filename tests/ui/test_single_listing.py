"""Listing → Common Listing → Create Listing → Single Listing → Manual ("Add New Listing").

The page is reached through the sidebar "Listing" → "Common Listing" → "Create Listing" →
"Single Listing" → "Manual" on the ``authenticated_page`` fixture ("Single Listing" only expands
a sub-menu). No field is ever filled: the validation tests submit the empty form, and every API
request that is not a GET is aborted (and fails the test), so no listing can be saved or sent
live even if validation stopped working. Multi Listing, "Generate Listing By AI", image upload,
category and policy logic are out of scope.
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from framework.locators.single_listing_locators import (
    CHECKBOXES,
    FIELDS,
    PAGE_URL,
    SECTIONS,
    Field,
    Section,
)
from framework.pages.common_listing_page import CommonListingPage
from framework.pages.single_listing_page import SingleListingPage

pytestmark = pytest.mark.regression

INVALID_CLASS = re.compile(r"(^|\s)is-invalid(\s|$)")
REQUIRED_FIELDS = [field for field in FIELDS if field.required]
OPTIONAL_FIELDS = [field for field in FIELDS if not field.required]


def _field_id(field: Field) -> str:
    return f"{field.section_id.removeprefix('sec-')}-{field.label}"


@pytest.fixture
def common_listing(authenticated_page: Page) -> CommonListingPage:
    page = CommonListingPage(authenticated_page)
    page.open_from_sidebar()
    return page


@pytest.fixture
def single_listing(common_listing: CommonListingPage) -> SingleListingPage:
    """The Add New Listing page, opened through Create Listing → Single Listing → Manual, writes blocked."""
    page = SingleListingPage(common_listing.page)
    page.block_write_requests()
    common_listing.open_create_listing_menu()
    page.open_from_common_listing(common_listing)
    return page


# Navigation


@pytest.mark.smoke
def test_create_listing_menu_offers_single_and_multi_listing(common_listing: CommonListingPage) -> None:
    locators = common_listing.locators
    common_listing.open_create_listing_menu()
    expect(locators.create_listing_menu).to_be_visible()
    expect(locators.single_listing_option).to_be_visible()
    expect(locators.multi_listing_option).to_be_visible()


@pytest.mark.smoke
def test_single_listing_offers_manual_and_ai_options(common_listing: CommonListingPage) -> None:
    locators = common_listing.locators
    common_listing.open_create_listing_menu()
    expect(locators.single_listing_option).to_be_visible()
    common_listing.expand_single_listing()
    expect(locators.single_listing_submenu).to_be_visible()
    expect(locators.manual_option).to_be_visible()
    expect(locators.generate_by_ai_option).to_be_visible()


@pytest.mark.smoke
def test_single_listing_opens_add_new_listing_page(single_listing: SingleListingPage) -> None:
    expect(single_listing.page).to_have_url(PAGE_URL)
    expect(single_listing.locators.page_heading).to_be_visible()
    expect(single_listing.locators.breadcrumb).to_be_visible()


# Visibility


@pytest.mark.smoke
def test_section_buttons_and_actions_are_visible(single_listing: SingleListingPage) -> None:
    locators = single_listing.locators
    for section in SECTIONS:
        expect(locators.section_button(section.button)).to_be_visible()
    expect(locators.save_as_draft_button).to_be_visible()
    expect(locators.send_to_live_button).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("section", SECTIONS, ids=[s.button for s in SECTIONS])
def test_section_is_visible(single_listing: SingleListingPage, section: Section) -> None:
    expect(single_listing.locators.section(section.element_id)).to_be_visible()
    expect(single_listing.locators.section_heading(section)).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("field", FIELDS, ids=[_field_id(f) for f in FIELDS])
def test_field_is_visible(single_listing: SingleListingPage, field: Field) -> None:
    locators = single_listing.locators
    expect(locators.field_label(field)).to_be_visible()
    expect(locators.field_control(field)).to_be_visible()
    if field.required:
        expect(locators.required_marker(field)).to_be_visible()
    else:
        expect(locators.required_marker(field)).to_have_count(0)


@pytest.mark.smoke
def test_checkboxes_description_and_image_controls_are_visible(single_listing: SingleListingPage) -> None:
    locators = single_listing.locators
    for label in CHECKBOXES:
        expect(locators.checkbox(label)).to_be_visible()
    expect(locators.add_specification_button).to_be_visible()
    expect(locators.description_format_select).to_be_visible()
    expect(locators.description_editor).to_be_visible()
    expect(locators.images_label).to_be_visible()
    expect(locators.images_label.get_by_text("*", exact=True)).to_be_visible()
    expect(locators.select_from_library_button).to_be_visible()
    expect(locators.upload_from_storage_button).to_be_visible()


# Section buttons


@pytest.mark.functional
@pytest.mark.parametrize("section", SECTIONS, ids=[s.button for s in SECTIONS])
def test_section_button_scrolls_to_its_section(single_listing: SingleListingPage, section: Section) -> None:
    heading = single_listing.locators.section_heading(section)
    single_listing.scroll_away_from(section)
    expect(heading).not_to_be_in_viewport()
    single_listing.go_to_section(section)
    expect(heading).to_be_in_viewport(ratio=1)
    expect(single_listing.locators.section(section.element_id)).to_be_in_viewport()
    expect(single_listing.page).to_have_url(PAGE_URL)


# Required-field validation


@pytest.mark.functional
@pytest.mark.parametrize("action", ["save_as_draft", "send_to_live"], ids=["Save as Draft", "Send to Live"])
def test_empty_form_is_rejected(single_listing: SingleListingPage, action: str) -> None:
    locators = single_listing.locators
    getattr(single_listing, action)()

    for field in REQUIRED_FIELDS:
        expect(locators.required_message(field), f"{field.label}: no message").to_be_visible()
        expect(locators.field_control(field), f"{field.label}: not invalid").to_have_class(INVALID_CLASS)
    expect(locators.images_required_message).to_be_visible()
    for field in OPTIONAL_FIELDS:
        expect(locators.required_message(field)).to_have_count(0)
        expect(locators.field_control(field), f"{field.label}: marked invalid").not_to_have_class(INVALID_CLASS)

    # Still on the empty form, and nothing was sent to be saved or published.
    expect(single_listing.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    assert single_listing.blocked_write_requests == [], (
        f"The empty form tried to save: {single_listing.blocked_write_requests}"
    )
