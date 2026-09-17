"""Page actions shared by every page object.

Page objects inherit from BasePage and combine these actions with their own
locators from ``framework/locators/``. Assertions stay in the tests.
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

from playwright.sync_api import BrowserContext, Error, Locator, Page, Response

logger = logging.getLogger(__name__)


class BasePage:
    PATH: ClassVar[str]
    """Route of the page relative to the base URL, e.g. ``/login``; set by each page object."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> Response | None:
        """Navigate to this page. The browser context resolves PATH against the base URL."""
        logger.info("Open %s", self.PATH)
        return self.page.goto(self.PATH)

    def click(self, locator: Locator, description: str) -> None:
        logger.info("Click %s", description)
        locator.click()

    def fill(self, locator: Locator, value: str, description: str) -> None:
        # The value is never logged: fields may hold personal data.
        logger.info("Fill %s", description)
        locator.fill(value)

    def fill_secret(self, locator: Locator, value: str, description: str) -> None:
        """Fill a field holding a secret (e.g. a password) without it reaching logs or reports."""
        # Keeps this frame, and the secret in its locals, out of pytest tracebacks.
        __tracebackhide__ = True
        logger.info("Fill %s (value hidden)", description)
        try:
            locator.fill(value)
        except Error as exc:
            # Playwright error messages quote the typed text in their call log.
            raise type(exc)(exc.message.replace(value, "********")) from None

    def press(self, locator: Locator, key: str, description: str) -> None:
        logger.info("Press %s in %s", key, description)
        locator.press(key)

    @contextmanager
    def _untraced(self) -> Iterator[None]:
        """Keep the actions and network traffic inside the block out of the Playwright trace.

        Used for steps that handle secrets, such as typing a password and sending it:
        a running trace records typed text and request bodies. Tracing is stopped
        completely (pausing a chunk still records network traffic) and restarted after
        the block, so the trace recorded before the block is lost. Trace snapshots taken
        later still record input values, so the block must not leave a secret on the page.
        """
        was_tracing = _stop_tracing(self.page.context)
        try:
            yield
        finally:
            if was_tracing:
                # The options pytest-playwright starts tracing with.
                self.page.context.tracing.start(screenshots=True, snapshots=True, sources=True)


def _stop_tracing(context: BrowserContext) -> bool:
    """Stop the context's tracing completely and return whether it was running."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        try:
            # Playwright has no public "is tracing" flag; this call fails when tracing is off.
            context.tracing.stop_chunk(path=Path(scratch) / "discarded.zip")
        except Error as exc:
            if "Must start tracing" in exc.message:
                return False
            raise
    context.tracing.stop()
    return True
