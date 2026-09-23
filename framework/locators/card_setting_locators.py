"""Locators of the SHP My Account → Card Setting page (``/card-setting``).

Verified against the live page on 2026-09-23. The page has no ``data-testid`` and no
table: every saved card is a Bootstrap card tile inside ``main``. The default tile
carries a "Default" badge and has **no** action buttons; every other tile has a
"Set default" button and an icon-only delete button.

The Add Card modal mounts a **Stripe** card element in a cross-origin iframe
(``iframe[title="Secure card payment input frame"]``); the application runs Stripe in
test mode. No card number, expiry or CVC is part of any locator - card data comes from
configuration only (see ``framework.config.get_sandbox_cards``). A card is addressed the
way the page shows it: masked last four digits plus the brand / expiry line.
"""

from __future__ import annotations

import re

from playwright.sync_api import FrameLocator, Locator, Page

PAGE_URL = re.compile(r"/card-setting$")
LIST_API_PATH = "/api/v1/card-setting"
"""The request the page sends for the card list, and re-sends after every change."""

PAGE_HEADING = "Card Setting"
ADD_CARD_TITLE = "Add Card"
REMOVE_CARD_TITLE = "Remove card?"
DEFAULT_BADGE = "Default"
SET_DEFAULT_LABEL = "Set default"
SET_AS_DEFAULT_CHECKBOX_LABEL = "Set as default card"
CARD_DETAILS_LABEL = "Card details"
STRIPE_NOTICE = re.compile(r"Card data is sent directly to Stripe")
STRIPE_CARD_FRAME = "iframe[title='Secure card payment input frame']"

MASKED_NUMBER = re.compile(r"^[•\s]+(\d{4})$")
"""A card's number line: bullets (U+2022) and nothing but the last four digits."""


def masked_number_pattern(last_four: str) -> re.Pattern[str]:
    """The masked number inside a tile's concatenated text content.

    ``has_text`` matches the element's whole text content, in which the number line runs
    straight into the brand line ("... 5556Visa - Exp ..."), so the digits are anchored to
    the masking bullets in front of them rather than to a word boundary behind them.
    """
    return re.compile(rf"•\s*{re.escape(last_four)}")


class CardSettingLocators:
    """Every element the Card Setting tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self.main: Locator = page.get_by_role("main")

        # Sidebar: "My Account" is an accordion button whose nested list holds "Card Setting".
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_my_account_menu: Locator = sidebar_menu.get_by_role("button", name="My Account")
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(has=page.get_by_role("button", name="My Account"))
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.card_setting_link: Locator = self.sidebar_submenu.get_by_role("link", name=PAGE_HEADING, exact=True)

        # Page header.
        self.page_heading: Locator = self.main.get_by_role("heading", name=PAGE_HEADING, exact=True)
        self.breadcrumb: Locator = self.main.get_by_role("navigation", name="breadcrumb")
        # The Add Card modal renders inside ``main`` and repeats the name on its submit
        # button, so the page's own button is the first of the two in the DOM.
        self.add_card_button: Locator = self.main.get_by_role("button", name=ADD_CARD_TITLE).first

        # One tile per saved card.
        self.cards: Locator = self.main.locator(".card")
        self.default_cards: Locator = self.cards.filter(has=page.get_by_text(DEFAULT_BADGE, exact=True))
        """Every tile carrying the "Default" badge; the page must have exactly one."""

        # Add Card modal. Both modals share the ``.modal`` class, so each is found by its own title.
        self.add_card_modal: Locator = self._modal(ADD_CARD_TITLE)
        self.add_card_modal_title: Locator = self.add_card_modal.get_by_role(
            "heading", name=ADD_CARD_TITLE, exact=True
        )
        self.card_details_label: Locator = self.add_card_modal.get_by_text(CARD_DETAILS_LABEL, exact=True)
        # Stripe's own container class; it is the element Stripe mounts its iframe into.
        self.card_element: Locator = self.add_card_modal.locator(".StripeElement")
        self.set_as_default_checkbox: Locator = self.add_card_modal.get_by_role(
            "checkbox", name=SET_AS_DEFAULT_CHECKBOX_LABEL, exact=True
        )
        self.stripe_notice: Locator = self.add_card_modal.get_by_text(STRIPE_NOTICE)
        self.cancel_button: Locator = self.add_card_modal.get_by_role("button", name="Cancel", exact=True)
        self.submit_add_card_button: Locator = self.add_card_modal.get_by_role(
            "button", name=ADD_CARD_TITLE, exact=True
        )
        # The close (×) icon has no accessible name; Bootstrap's own class identifies it.
        self.close_icon: Locator = self.add_card_modal.locator("button.btn-close")

        # The Stripe card element, in its cross-origin iframe. The input names are Stripe's.
        self.card_frame: FrameLocator = self.add_card_modal.frame_locator(STRIPE_CARD_FRAME)
        self.card_number_input: Locator = self.card_frame.locator("input[name='cardnumber']")
        self.card_expiry_input: Locator = self.card_frame.locator("input[name='exp-date']")
        self.card_cvc_input: Locator = self.card_frame.locator("input[name='cvc']")

        # "Remove card?" confirmation modal.
        self.remove_card_modal: Locator = self._modal(REMOVE_CARD_TITLE)
        self.remove_card_modal_title: Locator = self.remove_card_modal.get_by_role(
            "heading", name=REMOVE_CARD_TITLE, exact=True
        )
        self.remove_confirm_button: Locator = self.remove_card_modal.get_by_role(
            "button", name="Remove", exact=True
        )
        self.remove_cancel_button: Locator = self.remove_card_modal.get_by_role(
            "button", name="Cancel", exact=True
        )

    def _modal(self, title: str) -> Locator:
        return self.main.locator(".modal").filter(
            has=self._page.get_by_role("heading", name=title, exact=True)
        )

    def card_tile(self, last_four: str, details: str | re.Pattern[str]) -> Locator:
        """The tile of one saved card: its masked last four digits and its brand / expiry line.

        Both are needed - the account may hold two cards of the same number with
        different expiry dates.
        """
        return self.cards.filter(has_text=masked_number_pattern(last_four)).filter(has_text=details)

    @staticmethod
    def masked_number(card: Locator, last_four: str) -> Locator:
        """The card's number line, matched only when it is masked down to the last four digits."""
        return card.get_by_text(re.compile(rf"^[•\s]+{re.escape(last_four)}$"))

    @staticmethod
    def default_badge(card: Locator) -> Locator:
        return card.get_by_text(DEFAULT_BADGE, exact=True)

    @staticmethod
    def set_default_button(card: Locator) -> Locator:
        return card.get_by_role("button", name=SET_DEFAULT_LABEL, exact=True)

    @staticmethod
    def delete_button(card: Locator) -> Locator:
        # Icon-only button with no accessible name; its danger style is the only thing identifying it.
        return card.locator("button.btn-outline-danger")

    def remove_message(self, brand: str, last_four: str) -> Locator:
        """The confirmation text, which names the brand and the masked number of the card."""
        return self.remove_card_modal.get_by_text(
            re.compile(rf"Remove\s+{re.escape(brand)}.*{re.escape(last_four)}")
        )
