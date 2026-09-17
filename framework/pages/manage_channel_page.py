"""Page object of the SHP Manage Channel page."""

from __future__ import annotations

import logging
import re

from playwright.sync_api import Page

from framework.locators.manage_channel_locators import (
    ManageChannelLocators,
    SandboxAuthorizationLocators,
)
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)

AUTOMATION_CHANNEL_PREFIX = "AUTOMATION TEST CHANNEL"
"""Every channel this framework creates starts with this; only such a channel may be deleted."""


class ManageChannelPage(BasePage):
    PATH = "/channels"

    FULL_TABLE_VIEWPORT = {"width": 1600, "height": 900}
    """Smallest viewport that renders every column.

    Below 1600 px the page folds its last columns ("Config Date", "Cron Config
    Time Slot") into expandable "+" rows, so they are not in the DOM at the
    default 1280 px viewport.
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = ManageChannelLocators(page)

    def use_full_table_viewport(self) -> None:
        """Widen the browser window so the table renders all of its columns."""
        logger.info("Set the viewport to %(width)sx%(height)s", self.FULL_TABLE_VIEWPORT)
        self.page.set_viewport_size(self.FULL_TABLE_VIEWPORT)

    def open_from_sidebar(self) -> None:
        """Open the page the way a user does: the 'Manage Channel' sidebar menu; nothing else is clicked."""
        self.click(self.locators.sidebar_menu_entry, "'Manage Channel' sidebar menu")

    def expand_sidebar_menu(self, menu: str) -> None:
        """Expand the ``menu`` sidebar entry so its sub-menu is shown; nothing inside it is clicked.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        if not self.locators.sidebar_submenu(menu).is_visible():
            self.click(self.locators.sidebar_submenu_button(menu), f"'{menu}' sidebar menu")

    # "Add a new connection" popup. Platform and channel name are filled in one step:
    # choosing a platform reveals the Channel Name field in the same popup.

    def open_add_connection_popup(self) -> None:
        self.click(self.locators.add_new_button, "'+ Add New' button")

    def select_platform(self, platform: str) -> None:
        """Choose ``platform`` in the connection popup, the way a user clicks its card."""
        self.click(self.locators.platform_option(platform), f"'{platform}' platform option")

    def enter_channel_name(self, channel_name: str) -> None:
        self.fill(self.locators.popup_channel_name_input, channel_name, "'Channel Name' field of the popup")

    def continue_connection(self) -> None:
        """Press Next. With a valid channel name this leaves SHP for the platform's sign-in page."""
        self.click(self.locators.popup_next_button, "'Next' button of the popup")

    def cancel_connection_popup(self) -> None:
        self.click(self.locators.popup_cancel_button, "'Cancel' button of the popup")

    def authorize_in_sandbox(self) -> ManageChannelPage:
        """Press Next and finish the connection in SHP's local dev sandbox.

        Next opens the sandbox sign-in **in a new tab**, and that tab is redirected
        back to the Channel Connection page once the connection is authorised. The
        tab this page object was built on keeps showing the table from before, so the
        returned page object is bound to the new tab and every check runs on it.

        Nothing is typed: the sandbox is SHP's own fake sign-in and accepts the empty
        form, so no marketplace credentials are needed or stored anywhere.
        """
        with self.page.expect_popup() as sandbox_tab:
            self.continue_connection()
        sandbox = sandbox_tab.value
        sandbox.wait_for_load_state()
        logger.info("Authorise the connection in the local dev sandbox (nothing is typed)")
        SandboxAuthorizationLocators(sandbox).sign_in_button.click()
        # The tab returns to /channels?connected=... and then drops the query.
        sandbox.wait_for_url(re.compile(rf"{re.escape(self.PATH)}(\?|$)"))
        return ManageChannelPage(sandbox)

    # Delete. One modal walks through three stages: confirm, a countdown, confirm again.

    def open_delete_confirmation(self, channel_name: str) -> None:
        self.click(
            self.locators.row_delete_button(channel_name),
            f"'Delete' button of the '{channel_name}' channel",
        )

    def confirm_delete(self) -> None:
        self.click(self.locators.delete_confirm_button, "'Yes, delete' button")

    def confirm_delete_permanently(self) -> None:
        """Press the final confirmation.

        The button is disabled and named "Please wait <n>s" while it counts down, so
        this locator only matches once the countdown has finished; the click waits.
        """
        self.click(self.locators.permanent_delete_button, "'Delete permanently' button")

    def delete_channel(self, channel_name: str) -> None:
        """Delete ``channel_name`` through all three confirmation stages.

        Refuses any channel this framework did not create, so neither a test nor a
        clean-up can ever remove one of the account's real channels.
        """
        if not channel_name.startswith(AUTOMATION_CHANNEL_PREFIX):
            raise ValueError(
                f"Refusing to delete {channel_name!r}: only channels named "
                f"{AUTOMATION_CHANNEL_PREFIX!r}... are created by the automation."
            )
        self.open_delete_confirmation(channel_name)
        self.confirm_delete()
        self.confirm_delete_permanently()
