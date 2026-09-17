"""Upgrade Plan: page visibility (tests 1–14) and a downgrade + upgrade-back plan change (test 15).

Visibility tests click nothing on the page. The plan-change test downgrades to a lower
plan, upgrades back to the original one and always restores the original plan and
Auto-Pay choice. Plans, prices and limits are discovered at run time, never hard-coded.
The page comes from the ``authenticated_page`` fixture (one sign-in per browser per run).
"""

from __future__ import annotations

import logging
import re
import time

import pytest
from playwright.sync_api import Page, expect

from framework.locators.upgrade_plan_locators import (
    DOWNGRADE_ACTION,
    SUBSCRIPTION_LABELS,
    USAGE_LABELS,
    USAGE_PLAN_FEATURES,
)
from framework.pages.upgrade_plan_page import UpgradePlanPage

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.regression

USAGE_UPDATE_TIMEOUT_S = 120
"""The checkout says new limits "take effect shortly after you confirm"."""


@pytest.fixture
def upgrade_plan(authenticated_page: Page) -> UpgradePlanPage:
    """The Upgrade Plan page, opened through the sidebar of the signed-in dashboard."""
    page = UpgradePlanPage(authenticated_page)
    page.open_from_sidebar()
    return page


@pytest.mark.smoke
def test_page_header_is_visible(upgrade_plan: UpgradePlanPage) -> None:
    expect(upgrade_plan.locators.page_heading).to_be_visible()
    expect(upgrade_plan.locators.breadcrumb).to_be_visible()


@pytest.mark.smoke
def test_subscription_summary_is_visible(upgrade_plan: UpgradePlanPage) -> None:
    locators = upgrade_plan.locators
    for label in SUBSCRIPTION_LABELS:
        expect(locators.subscription_item(label)).to_be_visible()
    expect(locators.manage_auto_pay_button).to_be_visible()


@pytest.mark.smoke
def test_current_usage_section_is_visible(upgrade_plan: UpgradePlanPage) -> None:
    expect(upgrade_plan.locators.current_usage_heading).to_be_visible()
    expect(upgrade_plan.locators.current_usage_section).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("label", USAGE_LABELS)
def test_usage_tile_is_visible(upgrade_plan: UpgradePlanPage, label: str) -> None:
    expect(upgrade_plan.locators.usage_tile_label(label)).to_be_visible()


@pytest.mark.smoke
def test_every_rendered_plan_card_is_visible(upgrade_plan: UpgradePlanPage) -> None:
    locators = upgrade_plan.locators
    expect(locators.plans_section).to_be_visible()
    expect(locators.plan_cards.first).to_be_visible()

    cards = locators.plan_cards.all()
    assert cards, "No plan card is rendered"
    for card in cards:
        expect(card).to_be_visible()
        expect(locators.plan_name(card)).to_be_visible()
        expect(locators.plan_price(card)).to_be_visible()
        expect(locators.plan_features(card)).to_be_visible()
        expect(locators.plan_feature_items(card).first).to_be_visible()
        # The action/status button is checked only where the card renders one.
        if locators.plan_action(card).count():
            expect(locators.plan_action(card)).to_be_visible()


def _expected_limit(value: str | None) -> str | None:
    """Pattern a usage tile must show for a card feature value; None when it is not comparable ("Not included")."""
    if value == "∞":
        return r"\bUnlimited\b"
    if value and value.isdigit():
        return rf"/\s*{value}(?!\d)"
    return None


def _usage_mismatches(features: dict[str, str], usage: dict[str, str]) -> list[str]:
    """Tiles whose limit does not match the plan's card features, and tiles showing no value at all."""
    problems = [f"{label}: tile shows no value" for label, text in usage.items() if text == label]
    for label, feature in USAGE_PLAN_FEATURES.items():
        pattern = _expected_limit(features.get(feature))
        if pattern and not re.search(pattern, usage[label]):
            problems.append(f"{label}: plan has {feature} {features[feature]!r}, tile shows {usage[label]!r}")
    return problems


def _wait_for_plan_and_usage(upgrade_plan: UpgradePlanPage, name: str, features: dict[str, str]) -> list[str]:
    """Reload until ``name`` is current and Current Usage matches its limits; the remaining problems otherwise."""
    deadline = time.monotonic() + USAGE_UPDATE_TIMEOUT_S
    while True:
        upgrade_plan.reload()
        if upgrade_plan.is_current_plan(name):
            usage = upgrade_plan.usage_texts()
            problems = _usage_mismatches(features, usage)
            if not problems:
                logger.info("Current Usage for '%s': %s", name, usage)
                return []
        else:
            problems = [f"'{name}' is not the current plan"]
        if time.monotonic() > deadline:
            return problems
        upgrade_plan.page.wait_for_timeout(5_000)


def _restore_original_plan(upgrade_plan: UpgradePlanPage, original: str, auto_pay_on: bool) -> None:
    """Make ``original`` the current plan again if the test left another one current."""
    upgrade_plan.page.keyboard.press("Escape")
    upgrade_plan.reload()
    if upgrade_plan.is_current_plan(original):
        return
    logger.warning("RESTORE: '%s' is not current; change back to it", original)
    upgrade_plan.change_plan(original, auto_pay_on=auto_pay_on)
    assert upgrade_plan.wait_until_current_plan(original), f"RESTORE FAILED: '{original}' is not the current plan"


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_downgrade_then_upgrade_back_to_the_original_plan(upgrade_plan: UpgradePlanPage) -> None:
    upgrade_plan.wait_for_plans()
    original = upgrade_plan.current_plan_name()
    original_features = upgrade_plan.plan_features(original)
    original_auto_pay = upgrade_plan.auto_pay_state()
    auto_pay_on = original_auto_pay.lower().startswith("on")
    usage_before = upgrade_plan.usage_texts()
    logger.info("Original plan '%s' %s, Auto-Pay %s, usage %s", original, original_features, original_auto_pay, usage_before)

    try:
        # Downgrade target: the nearest lower plan (cards render cheapest first) whose card lists
        # a limit for every mapped usage module (so Current Usage can be compared, and no module
        # the account uses is removed) and whose Plan Comparison checks all pass.
        target = None
        for name in reversed(upgrade_plan.plan_names_with_action(DOWNGRADE_ACTION)):
            features = upgrade_plan.plan_features(name)
            if not all(_expected_limit(features.get(feature)) for feature in USAGE_PLAN_FEATURES.values()):
                continue
            if upgrade_plan.change_plan(name, auto_pay_on=auto_pay_on):
                target = name
                break
        if target is None:
            pytest.skip("No lower plan with comparable limits whose Plan Comparison checks all pass")

        problems = _wait_for_plan_and_usage(upgrade_plan, target, features)
        assert not problems, f"After downgrading to '{target}': {problems}"
        if any(features.get(f) != original_features.get(f) for f in USAGE_PLAN_FEATURES.values()):
            assert upgrade_plan.usage_texts() != usage_before, "Current Usage did not change after the downgrade"
        assert upgrade_plan.auto_pay_state() == original_auto_pay, "Auto-Pay changed during the downgrade"

        assert upgrade_plan.change_plan(original, auto_pay_on=auto_pay_on), f"Could not start the change back to '{original}'"
        problems = _wait_for_plan_and_usage(upgrade_plan, original, original_features)
        assert not problems, f"After upgrading back to '{original}': {problems}"
        assert upgrade_plan.auto_pay_state() == original_auto_pay, "Auto-Pay changed during the upgrade back"
    finally:
        _restore_original_plan(upgrade_plan, original, auto_pay_on)
