"""Page object of the SHP My Account → Card Setting page."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from playwright.sync_api import Locator, Page, Response

from framework.config import SandboxCard
from framework.locators.card_setting_locators import (
    DEFAULT_BADGE,
    LIST_API_PATH,
    MASKED_NUMBER,
    PAGE_URL,
    SET_DEFAULT_LABEL,
    CardSettingLocators,
)
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)

CHANGE_TIMEOUT_MS = 45_000
"""Adding a card round-trips through Stripe before SHP answers; observed at 5-10 s."""


@dataclass(frozen=True)
class CardOnPage:
    """One saved card as the page shows it. Holds no card data beyond what is on screen."""

    last_four: str
    details: str
    """The brand / expiry line, e.g. ``MasterCard · Exp 02/2033``."""
    is_default: bool

    def __str__(self) -> str:
        return f"{self.details} ****{self.last_four}{' (Default)' if self.is_default else ''}"


class CardSettingPage(BasePage):
    PATH = "/card-setting"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = CardSettingLocators(page)

    # Navigation

    def open_from_sidebar(self) -> None:
        """Expand "My Account" and open its "Card Setting" link.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        self.locators.sidebar_my_account_menu.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_my_account_menu, "'My Account' sidebar menu")
        with self._expect_card_list():
            self.click(self.locators.card_setting_link, "'Card Setting' My Account sub-menu link")
        self.page.wait_for_url(PAGE_URL)

    def open_and_wait_for_cards(self) -> None:
        """Navigate straight to the page and wait for its card list; used by the clean-up."""
        with self._expect_card_list():
            self.open()

    # Reading the page

    def saved_cards(self) -> list[CardOnPage]:
        """Every card tile on the page, read the way it is displayed.

        Nothing is read from the application's API: a tile shows a masked number, a brand
        and an expiry, and that is the whole identity a test needs.
        """
        cards: list[CardOnPage] = []
        for text in self.locators.cards.all_inner_texts():
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            is_default = DEFAULT_BADGE in lines
            lines = [line for line in lines if line not in (DEFAULT_BADGE, SET_DEFAULT_LABEL)]
            masked = MASKED_NUMBER.match(lines[0])
            if masked is None:  # not a card tile
                continue
            cards.append(CardOnPage(masked.group(1), lines[1], is_default))
        return cards

    def default_card(self) -> CardOnPage | None:
        return next((card for card in self.saved_cards() if card.is_default), None)

    def tile_of(self, card: CardOnPage | SandboxCard) -> Locator:
        """The tile of a card, whether it was read from the page or comes from configuration."""
        if isinstance(card, CardOnPage):
            return self.locators.card_tile(card.last_four, card.details)
        # A SandboxCard: the page renders "<brand> · Exp <MM/YYYY>"; the separator is not matched.
        details = re.compile(rf"{re.escape(card.brand)}.*Exp\s*{re.escape(card.expiry_label)}")
        return self.locators.card_tile(card.last_four, details)

    # Add Card

    def open_add_card_modal(self) -> None:
        self.click(self.locators.add_card_button, "'+ Add Card'")
        self.locators.add_card_modal.wait_for()
        # Stripe mounts its card iframe asynchronously, after the modal is already on screen.
        self.locators.card_number_input.wait_for()

    def cancel_add_card_modal(self) -> None:
        self.click(self.locators.cancel_button, "'Cancel' of the Add Card modal")
        self.locators.add_card_modal.wait_for(state="hidden")

    def add_card(self, card: SandboxCard, *, set_as_default: bool = False) -> None:
        """Type a configured sandbox test card into Stripe's iframe and submit it.

        The number and the CVC never reach the log, a report or the Playwright trace:
        they are filled with ``fill_secret`` (value never logged, masked in Playwright
        error messages) and the whole block runs with tracing stopped, which only
        restarts once the modal - and with it the iframe still holding the values - is
        gone. Only the brand, the last four digits and the expiry are ever logged, and
        that is what the application itself displays.
        """
        logger.info("Add card %s (set as default: %s)", card, set_as_default)
        with self._untraced():
            self.fill_secret(self.locators.card_number_input, card.number, "card number field")
            self.fill(self.locators.card_expiry_input, card.expiry, "card expiry field")
            self.fill_secret(self.locators.card_cvc_input, card.cvc, "card CVC field")
            if set_as_default:
                logger.info("Check 'Set as default card'")
                self.locators.set_as_default_checkbox.check()
            with self._expect_card_list():
                self.click(self.locators.submit_add_card_button, "'Add Card' of the Add Card modal")
            self.locators.add_card_modal.wait_for(state="hidden", timeout=CHANGE_TIMEOUT_MS)

    # Set default / remove

    def set_default(self, card: Locator, description: str) -> None:
        """Make one card the default and wait for its badge, not for a request."""
        self.click(self.locators.set_default_button(card), f"'Set default' of {description}")
        self.locators.default_badge(card).wait_for(timeout=CHANGE_TIMEOUT_MS)

    def open_remove_confirmation(self, card: Locator, description: str) -> None:
        self.click(self.locators.delete_button(card), f"delete (trash) of {description}")
        self.locators.remove_card_modal.wait_for()

    def confirm_remove(self) -> None:
        with self._expect_card_list():
            self.click(self.locators.remove_confirm_button, "'Remove' of the 'Remove card?' modal")
        self.locators.remove_card_modal.wait_for(state="hidden", timeout=CHANGE_TIMEOUT_MS)

    def remove_card(self, card: Locator, description: str) -> None:
        self.open_remove_confirmation(card, description)
        self.confirm_remove()

    # Internals

    @contextmanager
    def _expect_card_list(self) -> Iterator[None]:
        """Wait for the card list the page (re)loads after opening and after every change."""
        with self.page.expect_response(self._is_card_list, timeout=CHANGE_TIMEOUT_MS):
            yield

    @staticmethod
    def _is_card_list(response: Response) -> bool:
        # The delete request uses the same path with the card's id appended, hence the exact match.
        return (
            response.url.endswith(LIST_API_PATH)
            and response.request.method == "GET"
            and response.ok
        )
