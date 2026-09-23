"""Page object of the SHP Listing → Common Listing → Create Listing → Single Listing page."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from playwright.sync_api import Page, Response, Route

from framework.locators.single_listing_locators import (
    API_URL_PATTERN,
    FORM_OPTIONS_API_PATH,
    PAGE_URL,
    SECTIONS,
    Section,
    SingleListingLocators,
)
from framework.pages.base_page import BasePage
from framework.pages.common_listing_page import CommonListingPage

logger = logging.getLogger(__name__)


class SingleListingPage(BasePage):
    FORM_VIEWPORT = {"width": 1280, "height": 720}
    """Short enough that no two distant sections fit on screen together."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = SingleListingLocators(page)
        self.blocked_write_requests: list[str] = []
        """Every non-GET API request the page tried to send after ``block_write_requests()``."""

    def open_from_common_listing(self, common_listing: CommonListingPage) -> None:
        """Choose Create Listing → Single Listing and wait until the form's dropdown options loaded."""
        with self.page.expect_response(self._is_form_options_response):
            common_listing.choose_single_listing()
        self.page.wait_for_url(PAGE_URL)
        logger.info("Set the viewport to %(width)sx%(height)s", self.FORM_VIEWPORT)
        self.page.set_viewport_size(self.FORM_VIEWPORT)

    def block_write_requests(self) -> None:
        """Safety net: abort (and record) every API request that could save or publish a listing."""
        self.page.route(API_URL_PATTERN, self._guard_write_request)

    def scroll_away_from(self, section: Section) -> None:
        """Scroll to the end of the form farthest from ``section``, so its button has to bring it back."""
        index = SECTIONS.index(section)
        if index < len(SECTIONS) / 2:
            logger.info("Scroll to the bottom of the form")
            # The action buttons stay on screen, so the last section's control is the scroll target.
            self.locators.upload_from_storage_button.scroll_into_view_if_needed()
        else:
            logger.info("Scroll to the top of the form")
            self.locators.page_heading.scroll_into_view_if_needed()

    def go_to_section(self, section: Section) -> None:
        self.click(self.locators.section_button(section.button), f"'{section.button}' section button")

    def save_as_draft(self) -> None:
        self.click(self.locators.save_as_draft_button, "'Save as Draft' button")

    def send_to_live(self) -> None:
        self.click(self.locators.send_to_live_button, "'Send to Live' button")

    def _guard_write_request(self, route: Route) -> None:
        request = route.request
        if request.method == "GET":
            route.continue_()
            return
        logger.error("Blocked %s %s", request.method, request.url)
        self.blocked_write_requests.append(f"{request.method} {request.url}")
        route.abort()

    @staticmethod
    def _is_form_options_response(response: Response) -> bool:
        return urlparse(response.url).path == FORM_OPTIONS_API_PATH and response.request.method == "GET"
