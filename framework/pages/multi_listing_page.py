"""Page object of the SHP Listing → Common Listing → Create Listing → Multi Listing page ("Add Draft")."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from playwright.sync_api import Page, Response, Route

from framework.locators.multi_listing_locators import (
    API_URL_PATTERN,
    COLUMNS_API_PATH,
    PAGE_URL,
    MultiListingLocators,
)
from framework.pages.base_page import BasePage
from framework.pages.common_listing_page import CommonListingPage

logger = logging.getLogger(__name__)


class MultiListingPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = MultiListingLocators(page)
        self.blocked_write_requests: list[str] = []
        """``"<METHOD> <path>"`` of every non-GET API request the page tried to send after ``block_write_requests()``."""

    def block_write_requests(self) -> None:
        """Abort (and record) every API request that could create, save or publish a draft.

        The page creates a blank draft row as soon as it opens, so this must be called before it is opened.
        """
        self.page.route(API_URL_PATTERN, self._guard_write_request)

    def open_from_common_listing(self, common_listing: CommonListingPage) -> None:
        """Choose Create Listing → Multi Listing and wait until the page asked for its columns."""
        common_listing.open_create_listing_menu()
        with self.page.expect_response(self._is_columns_response):
            common_listing.choose_multi_listing()
        self.page.wait_for_url(PAGE_URL)

    def _guard_write_request(self, route: Route) -> None:
        request = route.request
        if request.method == "GET":
            route.continue_()
            return
        logger.info("Blocked %s %s", request.method, request.url)
        self.blocked_write_requests.append(f"{request.method} {urlparse(request.url).path}")
        route.abort()

    @staticmethod
    def _is_columns_response(response: Response) -> bool:
        return urlparse(response.url).path == COLUMNS_API_PATH and response.request.method == "GET"
