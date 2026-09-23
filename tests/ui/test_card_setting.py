"""My Account → Card Setting: page visibility, adding, defaulting and removing a sandbox card.

The application runs **Stripe in test mode**. Every card these tests add comes from
configuration (``SHP_TEST_CARD*``, see ``.env.example``) and must be one of Stripe's
published test cards; the tests skip when it is not configured. No card number, expiry
or CVC is ever hardcoded, logged, written to a report or recorded in a Playwright trace,
and nothing here triggers a payment, a charge or a subscription change.

The tests form one ordered flow on the shared automation account: add a card without
"Set as default", make it the default, restore the original default, remove the card,
then add a second card **with** "Set as default" and remove it again. Every card the run
adds is tracked in ``card_state`` and removed after the module - pass or fail - and the
default the account had before the run is restored. Pre-existing cards are never
removed; their default flag is only moved and put back. Because the default card is a
setting of the shared account, the five data-writing tests are marked ``shared_state``
as well as ``destructive``; the two read-only tests are marked neither.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest
from playwright.sync_api import Browser, Locator, Page, StorageState, expect

from framework.config import ConfigError, SandboxCard, get_sandbox_cards
from framework.locators.card_setting_locators import PAGE_URL
from framework.pages.card_setting_page import CardOnPage, CardSettingPage
from framework.pages.login_page import LoginPage
from tests.conftest import NAVIGATION_TIMEOUT_MS

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.regression


@dataclass
class CardState:
    """What the account looked like before the run, and what the run added."""

    original: list[CardOnPage] = field(default_factory=list)
    captured: bool = False
    created: list[SandboxCard] = field(default_factory=list)
    """Cards added by this run and not removed yet; a card is registered before it is submitted."""

    @property
    def original_default(self) -> CardOnPage:
        default = next((card for card in self.original if card.is_default), None)
        if default is None:
            pytest.fail("The account had no default card before the run; nothing to restore.", pytrace=False)
        return default


@pytest.fixture(scope="session")
def sandbox_cards() -> tuple[SandboxCard, SandboxCard]:
    """The two sandbox test cards; the module skips when they are not configured."""
    try:
        return get_sandbox_cards()
    except ConfigError as error:
        pytest.skip(str(error))


@pytest.fixture(scope="module")
def card_state(
    browser: Browser,
    browser_name: str,
    browser_context_args: dict,
    _signed_in_storage: dict[str, StorageState],
) -> Iterator[CardState]:
    """Tracks the account's original cards and this run's cards, and restores both afterwards.

    After the module's last test, in a fresh signed-in context: every card still tracked
    is removed (a tracked card that is currently the default has the original default
    restored first, because the default card has no delete button), the original default
    is put back, and the resulting card list is compared with the original one. Anything
    that could not be restored is reported as a teardown error, which is reported in
    addition to, never instead of, a test's own failure.
    """
    state = CardState()
    yield state
    if not state.captured:
        return
    failures = _restore(state, browser, browser_name, browser_context_args, _signed_in_storage)
    if failures:
        logger.error("Card Setting clean-up failed: %s", failures)
        pytest.fail(
            "Clean-up/restore failed; the account was not returned to its original state:\n"
            + "\n".join(failures),
            pytrace=False,
        )
    logger.info("Clean-up restored the original cards and the original default card")


@pytest.fixture
def card_setting(authenticated_page: Page, card_state: CardState) -> CardSettingPage:
    """The Card Setting page, opened through the sidebar; captures the original state once."""
    page = CardSettingPage(authenticated_page)
    page.open_from_sidebar()
    if not card_state.captured:
        card_state.original = page.saved_cards()
        card_state.captured = True
        logger.info("Cards before the run: %s", [str(card) for card in card_state.original])
    return page


# Page and modal


@pytest.mark.smoke
def test_card_setting_opens_from_my_account_menu(card_setting: CardSettingPage) -> None:
    locators = card_setting.locators
    expect(card_setting.page).to_have_url(PAGE_URL)
    expect(locators.sidebar_submenu).to_be_visible()
    expect(locators.card_setting_link).to_have_attribute("aria-current", "page")
    expect(locators.page_heading).to_be_visible()
    expect(locators.breadcrumb).to_be_visible()
    expect(locators.add_card_button).to_be_visible()
    expect(locators.cards.first).to_be_visible()
    # The account always has exactly one default card.
    expect(locators.default_cards).to_have_count(1)


@pytest.mark.functional
def test_add_card_modal_opens_with_its_controls(card_setting: CardSettingPage, card_state: CardState) -> None:
    locators = card_setting.locators
    card_setting.open_add_card_modal()

    expect(locators.add_card_modal_title).to_be_visible()
    expect(locators.card_details_label).to_be_visible()
    expect(locators.card_element).to_be_visible()
    expect(locators.card_number_input).to_be_visible()
    expect(locators.card_expiry_input).to_be_visible()
    expect(locators.card_cvc_input).to_be_visible()
    expect(locators.set_as_default_checkbox).to_be_visible()
    expect(locators.set_as_default_checkbox).not_to_be_checked()
    expect(locators.stripe_notice).to_be_visible()
    expect(locators.cancel_button).to_be_enabled()
    expect(locators.submit_add_card_button).to_be_enabled()
    expect(locators.close_icon).to_be_visible()

    # Nothing is typed, so Cancel leaves the account untouched.
    card_setting.cancel_add_card_modal()
    expect(locators.add_card_modal).to_be_hidden()
    expect(locators.cards).to_have_count(len(card_state.original))


# First flow: add without the checkbox, set default, remove


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_add_sandbox_card_without_the_default_checkbox(
    card_setting: CardSettingPage, card_state: CardState, sandbox_cards: tuple[SandboxCard, SandboxCard]
) -> None:
    locators = card_setting.locators
    card = sandbox_cards[0]
    if card_setting.tile_of(card).count():
        pytest.fail(f"The account already holds {card}; the test could not tell which tile it added.", pytrace=False)
    previous_default = card_setting.tile_of(card_state.original_default)

    card_setting.open_add_card_modal()
    expect(locators.set_as_default_checkbox).not_to_be_checked()
    # Registered before it is submitted, so the clean-up knows about it even if this test fails.
    card_state.created.append(card)
    card_setting.add_card(card)

    tile = card_setting.tile_of(card)
    expect(tile).to_have_count(1)
    expect(locators.masked_number(tile, card.last_four)).to_be_visible()
    _expect_no_full_card_number(card_setting, card)
    # Not default: the checkbox was left unchecked and the account already had a default card.
    expect(locators.default_badge(tile)).to_have_count(0)
    expect(locators.set_default_button(tile)).to_be_visible()
    expect(locators.delete_button(tile)).to_be_visible()
    expect(locators.default_badge(previous_default)).to_be_visible()
    expect(locators.default_cards).to_have_count(1)


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_set_default_moves_the_default_to_the_added_card(
    card_setting: CardSettingPage, card_state: CardState, sandbox_cards: tuple[SandboxCard, SandboxCard]
) -> None:
    locators = card_setting.locators
    card = sandbox_cards[0]
    tile = _tile_of_created(card_setting, card_state, card)
    previous_default = card_setting.tile_of(card_state.original_default)

    card_setting.set_default(tile, str(card))

    expect(locators.default_badge(tile)).to_be_visible()
    # The default card offers neither action.
    expect(locators.set_default_button(tile)).to_have_count(0)
    expect(locators.delete_button(tile)).to_have_count(0)
    # The card that was default before is not any more, and can be made default again.
    expect(locators.default_badge(previous_default)).to_have_count(0)
    expect(locators.set_default_button(previous_default)).to_be_visible()
    expect(locators.default_cards).to_have_count(1)


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_remove_deletes_only_the_card_this_run_added(
    card_setting: CardSettingPage, card_state: CardState, sandbox_cards: tuple[SandboxCard, SandboxCard]
) -> None:
    locators = card_setting.locators
    card = sandbox_cards[0]
    tile = _tile_of_created(card_setting, card_state, card)
    original_default = card_setting.tile_of(card_state.original_default)

    # A default card has no delete button, so the account's own default is restored first.
    if locators.default_badge(tile).count():
        card_setting.set_default(original_default, f"the original default card {card_state.original_default}")
    expect(locators.default_badge(original_default)).to_be_visible()

    card_setting.open_remove_confirmation(tile, str(card))
    expect(locators.remove_card_modal_title).to_be_visible()
    expect(locators.remove_message(card.brand, card.last_four)).to_be_visible()
    expect(locators.remove_cancel_button).to_be_enabled()
    card_setting.confirm_remove()
    card_state.created.remove(card)

    expect(locators.remove_card_modal).to_be_hidden()
    expect(tile).to_have_count(0)
    # Nothing else was removed, and the account still has exactly one default card.
    expect(locators.cards).to_have_count(len(card_state.original))
    expect(locators.default_cards).to_have_count(1)
    for saved in card_state.original:
        expect(card_setting.tile_of(saved)).to_have_count(1)
    assert card_setting.default_card() == card_state.original_default


# Second flow: add with the "Set as default" checkbox


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_add_sandbox_card_with_the_default_checkbox_makes_it_default(
    card_setting: CardSettingPage, card_state: CardState, sandbox_cards: tuple[SandboxCard, SandboxCard]
) -> None:
    locators = card_setting.locators
    card = sandbox_cards[1]
    if card_setting.tile_of(card).count():
        pytest.fail(f"The account already holds {card}; the test could not tell which tile it added.", pytrace=False)
    previous_default = card_setting.tile_of(card_state.original_default)
    expect(locators.default_badge(previous_default)).to_be_visible()

    card_setting.open_add_card_modal()
    card_state.created.append(card)
    card_setting.add_card(card, set_as_default=True)

    tile = card_setting.tile_of(card)
    expect(tile).to_have_count(1)
    expect(locators.masked_number(tile, card.last_four)).to_be_visible()
    _expect_no_full_card_number(card_setting, card)
    # Default straight away, without a second click.
    expect(locators.default_badge(tile)).to_be_visible()
    expect(locators.default_badge(previous_default)).to_have_count(0)
    expect(locators.default_cards).to_have_count(1)


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_run_leaves_the_original_cards_and_default_behind(
    card_setting: CardSettingPage, card_state: CardState, sandbox_cards: tuple[SandboxCard, SandboxCard]
) -> None:
    """The flow's own clean-up; the ``card_state`` teardown is the safety net behind it."""
    locators = card_setting.locators
    card = sandbox_cards[1]
    tile = _tile_of_created(card_setting, card_state, card)
    original_default = card_setting.tile_of(card_state.original_default)

    card_setting.set_default(original_default, f"the original default card {card_state.original_default}")
    expect(locators.default_badge(original_default)).to_be_visible()
    card_setting.remove_card(tile, str(card))
    card_state.created.remove(card)

    expect(tile).to_have_count(0)
    expect(locators.cards).to_have_count(len(card_state.original))
    assert set(card_setting.saved_cards()) == set(card_state.original)


# Helpers


def _tile_of_created(card_setting: CardSettingPage, card_state: CardState, card: SandboxCard) -> Locator:
    """The tile of a card an earlier test of this flow added; fails clearly when it is gone."""
    tile = card_setting.tile_of(card)
    if card not in card_state.created or tile.count() != 1:
        pytest.fail(f"Blocked: adding {card} earlier in this run did not succeed.", pytrace=False)
    return tile


def _expect_no_full_card_number(card_setting: CardSettingPage, card: SandboxCard) -> None:
    """The page must show the masked number only, never the number that was typed."""
    __tracebackhide__ = True  # keeps the number out of the pytest traceback
    shown = "\n".join(card_setting.locators.cards.all_inner_texts())
    assert card.number not in shown, f"The Card Setting page displays the full card number of {card}"


def _restore(
    state: CardState,
    browser: Browser,
    browser_name: str,
    browser_context_args: dict,
    signed_in_storage: dict[str, StorageState],
) -> list[str]:
    """Remove every card this run added and put the original default back. Returns the failures."""
    failures: list[str] = []
    storage = signed_in_storage.get(browser_name)
    if storage is None:
        return [f"{card}: no signed-in session to clean up with" for card in state.created]
    context = browser.new_context(**{**browser_context_args, "storage_state": storage})
    try:
        page = context.new_page()
        # The application's own JS bundle can take well over the 30 s default (see conftest).
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        page.goto(LoginPage.DASHBOARD_PATH)
        card_setting = CardSettingPage(page)
        card_setting.open_and_wait_for_cards()
        original_default = next((card for card in state.original if card.is_default), None)
        for card in list(state.created):
            try:
                tile = card_setting.tile_of(card)
                if not tile.count():
                    state.created.remove(card)
                    continue
                # The default card has no delete button, so the original default goes back first.
                if card_setting.locators.default_badge(tile).count() and original_default is not None:
                    card_setting.set_default(card_setting.tile_of(original_default), str(original_default))
                card_setting.remove_card(tile, str(card))
                tile.wait_for(state="detached")
                state.created.remove(card)
            except Exception as error:  # noqa: BLE001 - every card is attempted, failures are reported below
                failures.append(f"{card} was added by this run and is still on the account: {error}")
                page.reload()
        if original_default is not None and card_setting.default_card() != original_default:
            try:
                card_setting.set_default(card_setting.tile_of(original_default), str(original_default))
            except Exception as error:  # noqa: BLE001
                failures.append(f"the original default card {original_default} could not be restored: {error}")
        remaining = set(card_setting.saved_cards())
        if remaining != set(state.original):
            failures.append(
                "the final card list differs from the original one; "
                f"now: {sorted(str(card) for card in remaining)}, "
                f"before: {sorted(str(card) for card in state.original)}"
            )
    finally:
        context.close()
    return failures
