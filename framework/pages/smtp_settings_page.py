"""Page object of the SHP My Account → SMTP Settings page."""

from __future__ import annotations

import logging

from playwright.sync_api import Locator, Page, Request, Response

from framework.config import SandboxSmtp
from framework.locators.smtp_settings_locators import (
    CREATE_API_PATH,
    LIST_API_PATH,
    PAGE_URL,
    RECORD_API_PATH,
    SmtpSettingsLocators,
)
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class SmtpSettingsPage(BasePage):
    PATH = "/smtp-settings"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = SmtpSettingsLocators(page)
        self.last_list_response: Response | None = None
        """The table request the page answered on load."""
        self.create_requests: list[str] = []
        """Every create request the page has sent, so a test can prove none was sent."""
        page.on("request", self._record_create_request)

    def _record_create_request(self, request: Request) -> None:
        if request.method == "POST" and request.url.split("?")[0].rstrip("/").endswith(CREATE_API_PATH):
            self.create_requests.append(request.url)

    def open_from_sidebar(self) -> None:
        """Expand "My Account" and open its "SMTP Settings" link.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'My Account' sidebar menu")
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.smtp_settings_link, "'SMTP Settings' My Account sub-menu link")
        self.last_list_response = response.value
        self.page.wait_for_url(PAGE_URL)

    @staticmethod
    def _is_list_response(response: Response) -> bool:
        return LIST_API_PATH in response.url and response.request.method == "GET"

    # Add / Edit modal

    def open_add_modal(self) -> Locator:
        """Click "+ Add New" and return the Add SMTP Settings modal."""
        self.click(self.locators.add_new_button, "'+ Add New'")
        self.locators.add_modal.wait_for()
        return self.locators.add_modal

    def open_edit_modal(self, username: str) -> Locator:
        """Open the Edit modal of the row with this exact SMTP username."""
        row = self.locators.row_for(username)
        self.click(self.locators.row_edit_button(row), f"the Edit action of the '{username}' row")
        self.locators.edit_modal.wait_for()
        return self.locators.edit_modal

    def fill_form(
        self,
        modal: Locator,
        *,
        host: str | None = None,
        port: str | None = None,
        username: str | None = None,
        password: str | None = None,
        encryption: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
    ) -> None:
        """Fill the fields that are given; the ones left out keep whatever they hold.

        The password is filled through ``fill_secret``, so neither the log nor a Playwright
        error message can carry it.
        """
        __tracebackhide__ = True
        plain = (
            (self.locators.modal_host_input(modal), host, "SMTP host"),
            (self.locators.modal_port_input(modal), port, "Port"),
            (self.locators.modal_username_input(modal), username, "Username"),
            (self.locators.modal_from_email_input(modal), from_email, "From email"),
            (self.locators.modal_from_name_input(modal), from_name, "From name"),
        )
        for locator, value, description in plain:
            if value is not None:
                self.fill(locator, value, f"the SMTP {description} field")
        if password is not None:
            self.fill_secret(self.locators.modal_password_input(modal), password, "the SMTP Password field")
        if encryption is not None:
            logger.info("Select the '%s' Encryption option", encryption)
            self.locators.modal_encryption_select(modal).select_option(encryption)

    def fill_form_from(self, modal: Locator, smtp: SandboxSmtp, *, username: str) -> None:
        """Fill every required field from the sandbox configuration, with a unique username."""
        __tracebackhide__ = True
        self.fill_form(
            modal,
            host=smtp.host,
            port=smtp.port,
            username=username,
            password=smtp.password,
            encryption=smtp.encryption,
            from_email=smtp.from_email,
            from_name=smtp.from_name,
        )

    def save_expecting_no_write(self, modal: Locator) -> None:
        """Click Save with a required field missing and let the page settle.

        The application sends no request at all in this case, so there is nothing to wait for;
        waiting for the network to go idle keeps the wait bound to the application rather than
        to a fixed sleep.
        """
        self.click(self.locators.modal_save_button(modal), "'Save' (expecting no SMTP setting to be saved)")
        self.page.wait_for_load_state("networkidle")

    def save_expecting_create(self, modal: Locator) -> Response:
        """Click Save in the Add modal and return the create response."""
        with self.page.expect_response(self._is_create_response) as response:
            self.click(self.locators.modal_save_button(modal), "'Save' in the Add SMTP Settings modal")
        modal.wait_for(state="hidden")
        return response.value

    def save_expecting_update(self, modal: Locator) -> Response:
        """Click Save in the Edit modal and return the update response."""
        with self.page.expect_response(self._is_update_response) as response:
            self.click(self.locators.modal_save_button(modal), "'Save' in the Edit SMTP Settings modal")
        modal.wait_for(state="hidden")
        return response.value

    def cancel_modal(self, modal: Locator) -> None:
        self.click(self.locators.modal_cancel_button(modal), "'Cancel' in the SMTP Settings modal")
        modal.wait_for(state="hidden")

    # Delete

    def open_delete_dialog(self, username: str) -> Locator:
        """Click the Delete action of the row with this exact username and return the confirmation."""
        row = self.locators.row_for(username)
        self.click(self.locators.row_delete_button(row), f"the Delete action of the '{username}' row")
        self.locators.delete_dialog.wait_for()
        return self.locators.delete_dialog

    def confirm_delete(self) -> Response:
        """Confirm the open delete dialog and return the delete response."""
        with self.page.expect_response(self._is_delete_response) as response:
            self.click(self.locators.delete_dialog_confirm_button, "'Delete' in the confirmation")
        self.locators.delete_dialog.wait_for(state="hidden")
        return response.value

    def delete_setting(self, username: str) -> Response:
        """Delete the setting with this exact username through its row action and the confirmation."""
        self.open_delete_dialog(username)
        return self.confirm_delete()

    def reload_list(self) -> Response:
        """Reopen the page and wait for the table request, so the rows are the server's current ones."""
        with self.page.expect_response(self._is_list_response) as response:
            self.open()
        self.page.wait_for_url(PAGE_URL)
        self.locators.table.wait_for()
        return response.value

    @staticmethod
    def _is_create_response(response: Response) -> bool:
        return (
            response.request.method == "POST"
            and response.url.split("?")[0].rstrip("/").endswith(CREATE_API_PATH)
        )

    @staticmethod
    def _is_update_response(response: Response) -> bool:
        return response.request.method == "PUT" and RECORD_API_PATH.search(response.url) is not None

    @staticmethod
    def _is_delete_response(response: Response) -> bool:
        return response.request.method == "DELETE" and RECORD_API_PATH.search(response.url) is not None
