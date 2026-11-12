"""Listing → Common Listing → Create Listing → Multi Listing ("Add Draft").

The page is reached through the sidebar "Listing" → "Common Listing" → "Create Listing" →
"Multi Listing" on the ``authenticated_page`` fixture. The page creates a blank draft row the
moment it opens (``POST …/multiple-listing/create-blank``), so every API request that is not a
GET is aborted before it is opened: no draft is created, saved or sent live by these tests.

Not covered, because the application cannot show it at present (2026-11-12): the draft row's
fields, their required-field validation and any file input. The server answers
``GET …/multiple-listing/row/<id>`` with HTTP 500, so the page never renders a row.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.locators.multi_listing_locators import CREATE_BLANK_API_PATH, PAGE_URL
from framework.pages.common_listing_page import CommonListingPage
from framework.pages.multi_listing_page import MultiListingPage

pytestmark = pytest.mark.regression


@pytest.fixture
def multi_listing(authenticated_page: Page) -> MultiListingPage:
    """The Add Draft page, opened through Create Listing → Multi Listing, with every write blocked."""
    common_listing = CommonListingPage(authenticated_page)
    common_listing.open_from_sidebar()
    page = MultiListingPage(authenticated_page)
    page.block_write_requests()
    page.open_from_common_listing(common_listing)
    return page


@pytest.mark.smoke
def test_multi_listing_opens_add_draft_page(multi_listing: MultiListingPage) -> None:
    locators = multi_listing.locators
    expect(multi_listing.page).to_have_url(PAGE_URL)
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.breadcrumb_draft_link).to_have_attribute("href", "/drafts")


@pytest.mark.smoke
def test_page_controls_are_visible(multi_listing: MultiListingPage) -> None:
    locators = multi_listing.locators
    expect(locators.add_draft_button).to_be_visible()
    expect(locators.add_draft_button).to_be_enabled()
    expect(locators.send_to_draft_button).to_be_visible()
    expect(locators.send_to_live_button).to_be_visible()


@pytest.mark.functional
def test_nothing_can_be_sent_without_a_draft_row(multi_listing: MultiListingPage) -> None:
    """Without a draft row the page shows its empty state and offers no way to save or publish."""
    locators = multi_listing.locators
    expect(locators.no_drafts_message).to_be_visible()
    expect(locators.send_to_draft_button).to_be_disabled()
    expect(locators.send_to_live_button).to_be_disabled()
    expect(multi_listing.page).to_have_url(PAGE_URL)
    # The only write the page may attempt on its own is the blank row it creates on load.
    unexpected = [r for r in multi_listing.blocked_write_requests if r != f"POST {CREATE_BLANK_API_PATH}"]
    assert not unexpected, f"The page attempted to write: {unexpected}"
