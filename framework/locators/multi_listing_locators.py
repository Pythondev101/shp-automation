"""Locators of the SHP Listing → Common Listing → Create Listing → Multi Listing page (``/multiple-listing/add``).

Verified against the live page on 2026-11-12. The page is titled "Add Draft". Opening it (and
its "Add Draft" button) sends ``POST /api/v1/multiple-listing/create-blank`` to create a blank
draft row, then reads that row back. Without a row the page shows only its empty-state message,
"Add Draft", and the disabled "Send to Draft" / "Send to Live" buttons.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/multiple-listing/add$")
COLUMNS_API_PATH = "/api/v1/multiple-listing/columns"
"""The request that tells the page which draft columns to render; it marks the page as loaded."""
CREATE_BLANK_API_PATH = "/api/v1/multiple-listing/create-blank"
"""The write request the page sends on load and on "Add Draft": it creates a blank draft row."""
API_URL_PATTERN = "**/api/**"

NO_DRAFTS_MESSAGE = "No drafts yet. Click Add Draft below to start."


class MultiListingLocators:
    """Every element the Multi Listing tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        main = page.get_by_role("main")

        self.page_heading: Locator = main.get_by_role("heading", name="Add Draft", exact=True)
        self.breadcrumb: Locator = main.get_by_role("navigation", name="breadcrumb")
        self.breadcrumb_draft_link: Locator = self.breadcrumb.get_by_role("link", name="Draft", exact=True)
        self.no_drafts_message: Locator = main.get_by_text(NO_DRAFTS_MESSAGE, exact=True)

        # "Add Draft" starts with an icon glyph, so only the words are matched.
        self.add_draft_button: Locator = main.get_by_role("button", name=re.compile(r"^\W*Add Draft\W*$"))
        self.send_to_draft_button: Locator = main.get_by_role("button", name="Send to Draft", exact=True)
        self.send_to_live_button: Locator = main.get_by_role("button", name="Send to Live", exact=True)
