"""Page object of the SHP Upgrade Plan page."""

from __future__ import annotations

import logging
import time

from playwright.sync_api import Page

from framework.locators.upgrade_plan_locators import (
    CURRENT_PLAN_ACTION,
    PLAN_COMPARISON_TITLE,
    SUBSCRIPTION_LABELS,
    USAGE_LABELS,
    UpgradePlanLocators,
)
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)

CHECKOUT_TIMEOUT_MS = 60_000
"""The upgrade checkout charges the saved card through Stripe, which can take longer than the default timeout."""


class UpgradePlanPage(BasePage):
    # PATH is not set: the page is only reached through the sidebar, and its route is not asserted.

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = UpgradePlanLocators(page)

    def open_from_sidebar(self) -> None:
        """Open the page the way a user does: the "Upgrade Plan" sidebar entry."""
        self.click(self.locators.sidebar_menu_entry, "'Upgrade Plan' sidebar menu")

    def wait_for_plans(self) -> None:
        self.locators.plan_cards.first.wait_for()

    def reload(self) -> None:
        logger.info("Reload the Upgrade Plan page")
        self.page.reload()
        self.wait_for_plans()

    def current_plan_name(self) -> str:
        """Name of the card whose button is the disabled "Current Plan"."""
        card = self.locators.plan_cards_with_action(CURRENT_PLAN_ACTION)
        return self.locators.plan_name(card).inner_text().strip()

    def is_current_plan(self, name: str) -> bool:
        return self.locators.plan_card(name).filter(
            has=self.page.get_by_role("button", name=CURRENT_PLAN_ACTION, exact=True)
        ).count() == 1

    def plan_names_with_action(self, action: str) -> list[str]:
        """Names of the cards whose button is ``action``, in the order the page renders them."""
        cards = self.locators.plan_cards_with_action(action)
        return [name.strip() for name in self.locators.plan_name(cards).all_inner_texts()]

    def plan_features(self, name: str) -> dict[str, str]:
        """The card's feature list as {feature: value}, e.g. {"Staff": "2", "Setups": "∞"}."""
        items = self.locators.plan_feature_items(self.locators.plan_card(name)).all_inner_texts()
        return {key.strip(): value.strip() for key, _, value in (item.partition(":") for item in items)}

    def auto_pay_state(self) -> str:
        """Value of the "Auto-Pay:" summary item, e.g. "Off"."""
        label = SUBSCRIPTION_LABELS[1]
        return self.locators.subscription_item(label).inner_text().strip().removeprefix(label).strip()

    def usage_texts(self) -> dict[str, str]:
        """Text of every Current Usage tile, whitespace collapsed: {"No of Staff": "No of Staff 10% 1 / 10 9 left", ...}."""
        return {label: " ".join(self.locators.usage_tile(label).inner_text().split()) for label in USAGE_LABELS}

    def change_plan(self, name: str, *, auto_pay_on: bool) -> bool:
        """Change to plan ``name`` through its card button and the dialogs the application shows.

        A downgrade first shows Plan Comparison: when any module check there fails, the dialog
        is closed and False is returned (nothing is changed). The checkout's Auto-Pay choice is
        set to ``auto_pay_on`` before confirming. Returns True once the checkout dialog has closed.
        """
        locators = self.locators
        action = locators.plan_action(locators.plan_card(name))
        self.click(action, f"'{action.inner_text().strip()}' on the '{name}' plan card")
        locators.modal_title.wait_for()
        if locators.modal_title.inner_text().strip() == PLAN_COMPARISON_TITLE:
            locators.comparison_rows.first.wait_for()
            if locators.comparison_failed_rows.count():
                logger.info("Plan Comparison for '%s' has failed checks; close it", name)
                self.click(locators.comparison_close_button, "'Close' in Plan Comparison")
                locators.open_modal.wait_for(state="hidden")
                return False
            self.click(locators.comparison_proceed_button, "'Proceed' in Plan Comparison")
        locators.checkout_confirm_button.wait_for()
        logger.info("Set the checkout Auto-Pay choice to %s", "on" if auto_pay_on else "off")
        locators.checkout_auto_pay_checkbox.set_checked(auto_pay_on)
        self.click(locators.checkout_confirm_button, f"'{locators.checkout_confirm_button.inner_text().strip()}'")
        locators.open_modal.wait_for(state="hidden", timeout=CHECKOUT_TIMEOUT_MS)
        return True

    def wait_until_current_plan(self, name: str, timeout_s: float = 90) -> bool:
        """Reload until ``name`` is the current plan; False when it is not within ``timeout_s``."""
        deadline = time.monotonic() + timeout_s
        while True:
            self.reload()
            if self.is_current_plan(name):
                return True
            if time.monotonic() > deadline:
                return False
            self.page.wait_for_timeout(3_000)
