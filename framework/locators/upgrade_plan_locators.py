"""Locators of the SHP Upgrade Plan page.

Plans, the current plan, prices, limits, usage values and subscription dates are
data that change, so none of them is part of a locator. Plan cards are discovered
by their structure (a plan-name heading and a feature list), never by name or count.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_HEADING = "Upgrade Plan"
CURRENT_USAGE_HEADING = "Current Usage"

SUBSCRIPTION_LABELS = ("Subscription:", "Auto-Pay:")
"""Labels of the subscription summary that are always there; each is followed by its value."""

RENEWAL_LABELS = ("Renews on:", "Active until:")
"""The third summary item's label, which depends on the subscription itself.

The application renders ``Renews on:`` while the subscription has a renewal date and
``Active until:`` while it has none, so the label is never assumed - whichever one is
rendered is the one the tests check.
"""

USAGE_LABELS = (
    "No of Staff",
    "No of Folder Allowed",
    "Image Memory Uses",
    "No Of Images",
    "No of Draft Product",
    "No of SKU Allowed",
    "No of Warehouse",
    "No of Channel",
    "No of Setup",
    "Max Report",
)
"""Label of every Current Usage tile, in the order the page renders them."""

USAGE_PLAN_FEATURES = {
    "No of Staff": "Staff",
    "No of Draft Product": "Draft Products",
    "No of Warehouse": "Warehouses",
    "No of Channel": "Channels",
    "No of Setup": "Setups",
    "Max Report": "Reports",
}
"""Current Usage tile -> the plan-card feature ("Staff: 2") holding that tile's limit.

The other tiles (folders, image memory, images, SKU) have no matching card feature.
"""

CURRENT_PLAN_ACTION = "Current Plan"
DOWNGRADE_ACTION = "Downgrade"
PLAN_COMPARISON_TITLE = "Plan Comparison"

PRICE_FORMAT = re.compile(r"[$€£₹]\s?\d[\d.,]*\s*/\s*\S+")
"""Text shaped like a price with its billing period ("$ 5 / day"); the values are not matched."""


class UpgradePlanLocators:
    """Every element the Upgrade Plan tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Name starts with an icon glyph, so it is matched as a substring.
        self.sidebar_menu_entry: Locator = page.get_by_role("complementary").get_by_role("link", name=PAGE_HEADING)

        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING, exact=True, level=5)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")

        # "Manage Auto-Pay" is a link styled as a button; its name starts with an icon glyph.
        self.manage_auto_pay_button: Locator = self._main.get_by_role("link", name="Manage Auto-Pay")

        # Current Usage: the block holding both its heading and the tiles (the first and last tile label).
        usage_heading = page.get_by_role("heading", name=CURRENT_USAGE_HEADING, exact=True, level=6)
        self.current_usage_heading: Locator = self._main.locator(usage_heading)
        self.current_usage_section: Locator = (
            self._main.locator("div")
            .filter(has=usage_heading)
            .filter(has=page.get_by_text(USAGE_LABELS[0], exact=True))
            .filter(has=page.get_by_text(USAGE_LABELS[-1], exact=True))
            .last
        )

        # Plan cards: the innermost block holding a plan-name heading (h5), a price and a feature list.
        # The price is required because the page title (h5) and the breadcrumb (a list) share a block too.
        # A ``has`` / ``has_not`` locator is searched inside each candidate, so it is built from the page.
        card_candidate = (
            page.locator("div")
            .filter(has=page.get_by_role("heading", level=5))
            .filter(has=page.get_by_role("list"))
            .filter(has_text=PRICE_FORMAT)
        )
        self.plan_cards: Locator = self._main.locator(card_candidate).filter(has_not=card_candidate)
        # The outermost block holding the plan cards that is not also the page wrapper holding Current Usage.
        self.plans_section: Locator = (
            self._main.locator("div").filter(has=card_candidate).filter(has_not=usage_heading).first
        )

        # Plan-change dialogs are Bootstrap modals without a dialog role. A downgrade first opens
        # "Plan Comparison" (one row per module, a check icon when the account meets it, Proceed);
        # both directions then open the checkout ("Downgrade to <plan>" / "Upgrade to <plan>").
        self.open_modal: Locator = page.locator(".modal.show")
        self.modal_title: Locator = self.open_modal.locator(".modal-title")
        self.comparison_rows: Locator = self.open_modal.locator("tbody tr")
        self.comparison_failed_rows: Locator = self.comparison_rows.filter(
            has_not=page.locator(".bi-check-circle-fill")
        )
        # The header's close icon has no text, so "Close" matches only the footer button.
        self.comparison_close_button: Locator = self.open_modal.get_by_role("button", name="Close", exact=True)
        self.comparison_proceed_button: Locator = self.open_modal.get_by_role("button", name="Proceed", exact=True)
        self.checkout_auto_pay_checkbox: Locator = self.open_modal.get_by_role("checkbox", name="Turn on Auto-Pay")
        # "Confirm Downgrade"; "Pay <prorated amount> & Upgrade", or "Confirm Upgrade" when account credit covers the charge.
        self.checkout_confirm_button: Locator = self.open_modal.get_by_role(
            "button", name=re.compile(r"^(Confirm (Downgrade|Upgrade)|Pay .+ & Upgrade)$")
        )

    def subscription_item(self, label: str) -> Locator:
        """Summary item ``label`` together with its value (the element wrapping both).

        The label's own span also matches ``has``, so the item must hold text after the label.
        """
        return (
            self._main.locator("span")
            .filter(has=self._page.get_by_text(label, exact=True))
            .filter(has_text=re.compile(rf"^\s*{re.escape(label)}\s*\S"))
        )

    def renewal_item(self) -> Locator:
        """The third summary item - its date together with whichever label the plan state gives it."""
        pattern = "|".join(re.escape(label) for label in RENEWAL_LABELS)
        return (
            self._main.locator("span")
            .filter(has=self._page.get_by_text(re.compile(rf"^({pattern})$")))
            .filter(has_text=re.compile(rf"^\s*({pattern})\s*\S"))
        )

    def usage_tile_label(self, label: str) -> Locator:
        return self.current_usage_section.get_by_text(label, exact=True)

    def usage_tile(self, label: str) -> Locator:
        """The whole tile of ``label``: its label, percentage, "used / limit" and note."""
        return self.current_usage_section.locator(".usage-tile").filter(
            has=self._page.get_by_text(label, exact=True)
        )

    def plan_card(self, name: str) -> Locator:
        return self.plan_cards.filter(has=self._page.get_by_role("heading", name=name, exact=True, level=5))

    def plan_cards_with_action(self, action: str) -> Locator:
        return self.plan_cards.filter(has=self._page.get_by_role("button", name=action, exact=True))

    @staticmethod
    def plan_name(card: Locator) -> Locator:
        return card.get_by_role("heading", level=5)

    @staticmethod
    def plan_price(card: Locator) -> Locator:
        return card.get_by_text(PRICE_FORMAT).first

    @staticmethod
    def plan_features(card: Locator) -> Locator:
        return card.get_by_role("list")

    @staticmethod
    def plan_feature_items(card: Locator) -> Locator:
        return card.get_by_role("listitem")

    @staticmethod
    def plan_action(card: Locator) -> Locator:
        """The card's Upgrade / Downgrade / Current Plan button. The info icon button has no text, so it is excluded."""
        return card.get_by_role("button").filter(has_text=re.compile(r"[A-Za-z]"))
