"""Locators of the SHP Manage Channel page (``/channels``).

Verified against the live DOM on 2026-09-12. The page has no ``data-testid``
attributes; elements are located by accessible role and name inside the ``main``
landmark. "Channel Connection" is both the page title (``h3``) and the card title
(``h4``), so the page heading is pinned to level 3.

Channel rows and their values (channel name, token expiry, status, dates, cron
slot) are data and are deliberately not part of any locator, except
``channel_row()``, which finds one row by its channel name so a test can prove a
channel exists or does not.

The "Add a new connection" popup and the delete confirmation (verified 2026-09-12)
are Bootstrap modals without ``role="dialog"``, so they are the second documented
exception to the "no CSS classes" rule: they are scoped by ``.modal.show``. Only
one modal is open at a time, so both use the same container.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

COLUMN_HEADERS = (
    "S.No",
    "Channel Name",
    "Token Expiry",
    "Action",
    "Manage Products",
    "Manage Orders",
    "Config Date",
    "Cron Config Time Slot",
)
"""Every column header of the channel table, in the order the page renders them."""

ENTRY_COUNT_TEXT = re.compile(r"^Showing .+ entries$")
"""The entry count line; the numbers in it are data and are not matched."""

CONNECTABLE_PLATFORM = "eBay"
"""The only platform the application can connect today."""

COMING_SOON_PLATFORMS = ("Shopify", "Temu", "Amazon", "Walmart")
"""Platforms the popup offers but disables with a "Coming soon" badge."""

PLATFORMS = (CONNECTABLE_PLATFORM, *COMING_SOON_PLATFORMS)
"""Every platform of the "Add a new connection" popup, in the order it renders them."""

SIDEBAR_CHANNEL_MENUS = ("Active Listing", "Manage Order")
"""Sidebar entries whose sub-menu lists every connected channel by name."""

OPEN_MODAL = ".modal.show"
"""A popup is a Bootstrap modal without a dialog role; ``.show`` is only on the open one."""

ADD_CONNECTION_POPUP = OPEN_MODAL
"""The "Add a new connection" popup, under the name used since Step 7."""

CHANNEL_NAME_REQUIRED_MESSAGE = "Channel name is required"
"""Client-side validation shown when Next is pressed without a channel name."""

CHANNEL_CONNECTED_MESSAGE = "eBay channel connected successfully."
"""Banner shown on the page the authorisation returns to."""

DELETE_CONFIRMATION_HEADING = "Delete this channel?"
"""First stage of the delete flow, opened by a row's Delete button."""

DELETE_CHECKING_HEADING = "Checking before we continue…"
"""Second stage: the permanent-delete button counts down before it can be pressed."""

DELETE_COUNTDOWN_TEXT = re.compile(r"^Please wait \d+s$")
"""Name of the permanent-delete button while it counts down (and is disabled)."""

DELETE_FINAL_HEADING = "Confirm once more"
"""Third stage: the countdown has finished and the permanent delete can be pressed."""


class ManageChannelLocators:
    """Every element the Manage Channel tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Sidebar: "Manage Channel" is clicked; "Active Listing" and "Manage Order" are only
        # expanded to read the channel entries of their sub-menus (see sidebar_submenu_*).
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self._sidebar_menu = sidebar_menu
        self.sidebar_menu_entry: Locator = sidebar_menu.get_by_role("link", name="Manage Channel")

        # Page header area.
        self.page_heading: Locator = self._main.get_by_role(
            "heading", name="Channel Connection", exact=True, level=3
        )
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")
        # Names of these buttons start with an icon glyph, so they are matched as substrings.
        self.help_button: Locator = self._main.get_by_role("button", name="Help")
        self.add_new_button: Locator = self._main.get_by_role("button", name="Add New")

        # Filter bar. The labels are not linked to their fields, so they are located by text;
        # the fields carry their own accessible name (placeholder / aria-label).
        self.channel_name_label: Locator = self._main.get_by_text("Channel Name", exact=True)
        self.channel_name_input: Locator = self._main.get_by_role("textbox", name="Channel Name", exact=True)
        self.connection_label: Locator = self._main.get_by_text("Connection", exact=True)
        self.connection_select: Locator = self._main.get_by_role("combobox", name="Connection", exact=True)
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)

        # Table and its "Show <n> entries" control.
        self.show_entries_select: Locator = self._main.get_by_role(
            "combobox", name="Entries per page", exact=True
        )
        self.table: Locator = self._main.get_by_role("table")

        # Footer: entry count and pagination.
        self.entry_count: Locator = self._main.get_by_text(ENTRY_COUNT_TEXT)
        self.pagination: Locator = self._main.get_by_role("navigation", name="Pagination")
        self.previous_button: Locator = self.pagination.get_by_role("button", name="Previous", exact=True)
        self.next_button: Locator = self.pagination.get_by_role("button", name="Next", exact=True)
        # The page marks the current page number with a class only (no aria-current),
        # so this is the one place a CSS class is unavoidable.
        self.current_page: Locator = self.pagination.locator("li.active").get_by_role("button")

        # "Add a new connection" popup. Scoped from the page, not from main: the modal is
        # rendered outside the page's landmarks and carries no dialog role.
        self.add_connection_popup: Locator = page.locator(ADD_CONNECTION_POPUP)
        self.popup_heading: Locator = self.add_connection_popup.get_by_role(
            "heading", name="Add a new connection", exact=True
        )
        # The label is not linked to the field and the page's filter bar holds a second
        # "Channel Name" textbox, so the popup's field is pinned to its form attribute.
        self.popup_channel_name_input: Locator = self.add_connection_popup.locator(
            "input[name='channel_name']"
        )
        self.popup_channel_name_error: Locator = self.add_connection_popup.get_by_text(
            CHANNEL_NAME_REQUIRED_MESSAGE, exact=True
        )
        # "Next" also names the pagination button, so both are scoped to the popup.
        self.popup_next_button: Locator = self.add_connection_popup.get_by_role(
            "button", name="Next", exact=True
        )
        self.popup_cancel_button: Locator = self.add_connection_popup.get_by_role(
            "button", name="Cancel", exact=True
        )

        # Banner of a completed connection. It is rendered above the page's landmarks,
        # so it is scoped to the page, not to main.
        self.connected_message: Locator = page.get_by_text(CHANNEL_CONNECTED_MESSAGE, exact=True)

        # Delete confirmation. One modal that walks through three stages, each with its
        # own heading; the permanent-delete button is disabled while it counts down and
        # only then takes the name "Delete permanently".
        self.delete_popup: Locator = page.locator(OPEN_MODAL)
        self.delete_confirmation_heading: Locator = self.delete_popup.get_by_role(
            "heading", name=DELETE_CONFIRMATION_HEADING, exact=True
        )
        self.delete_confirm_button: Locator = self.delete_popup.get_by_role(
            "button", name="Yes, delete", exact=True
        )
        self.delete_checking_heading: Locator = self.delete_popup.get_by_role(
            "heading", name=DELETE_CHECKING_HEADING, exact=True
        )
        self.delete_countdown_button: Locator = self.delete_popup.get_by_role(
            "button", name=DELETE_COUNTDOWN_TEXT
        )
        self.delete_final_heading: Locator = self.delete_popup.get_by_role(
            "heading", name=DELETE_FINAL_HEADING, exact=True
        )
        self.permanent_delete_button: Locator = self.delete_popup.get_by_role(
            "button", name="Delete permanently", exact=True
        )

    def column_header(self, name: str) -> Locator:
        """Column header ``name``; matched as a substring because sortable headers append a "⇅" glyph."""
        return self._main.get_by_role("columnheader", name=name)

    def platform_option(self, platform: str) -> Locator:
        """The ``platform`` radio of the connection popup.

        Each option is a radio wrapped in a label holding the platform's name and logo,
        so the name is matched as a substring.
        """
        return self.add_connection_popup.get_by_role("radio", name=platform)

    def channel_row(self, channel_name: str) -> Locator:
        """The table row of the channel called ``channel_name`` (exact match on its name cell)."""
        return self._main.get_by_role("row").filter(
            has=self._page.get_by_role("cell", name=channel_name, exact=True)
        )

    def row_delete_button(self, channel_name: str) -> Locator:
        """The Delete button of the ``channel_name`` row; every row has one, so it must be scoped."""
        return self.channel_row(channel_name).get_by_role("button", name="Delete", exact=True)

    # Sidebar sub-menus (verified 2026-09-14). "Active Listing" and "Manage Order" are
    # buttons whose list item holds a nested list with one link per channel (plus
    # "All Orders" under Manage Order). The menus are an accordion: expanding one
    # collapses the other, and the nested list is absent while collapsed.

    def sidebar_submenu_button(self, menu: str) -> Locator:
        """The ``menu`` sidebar button; its name starts with an icon glyph, so it is a substring match."""
        return self._sidebar_menu.get_by_role("button", name=menu)

    def sidebar_submenu(self, menu: str) -> Locator:
        """The nested list of the ``menu`` sidebar entry, present only while it is expanded."""
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        item = self._sidebar_menu.get_by_role("listitem").filter(has=self._page.get_by_role("button", name=menu))
        return item.get_by_role("list")

    def sidebar_submenu_channel(self, menu: str, channel_name: str) -> Locator:
        """The ``channel_name`` link inside the ``menu`` sidebar sub-menu (exact name)."""
        return self.sidebar_submenu(menu).get_by_role("link", name=channel_name, exact=True)


class SandboxAuthorizationLocators:
    """The sign-in page the connect flow opens in a new tab (verified 2026-09-12).

    It is **SHP's own local dev sandbox** (``/api/v1/channels/ebay/dev-sandbox/authorize``),
    not eBay: the page states that it is a fake sign-in, that no real eBay account is
    used and that any credentials are accepted. It also accepts the empty form, so the
    automation only submits it – no marketplace credentials exist in this framework.

    Following D15, the page is identified by its URL and this one element instead of
    getting its own page object.
    """

    def __init__(self, page: Page) -> None:
        self.sign_in_button: Locator = page.get_by_role("button", name="Sign in", exact=True)
