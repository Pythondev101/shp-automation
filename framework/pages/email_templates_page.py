"""Page object of the SHP My Account → Email Templates page."""

from __future__ import annotations

import logging

from playwright.sync_api import Page, Request, Response

from framework.locators.email_templates_locators import (
    DELETE_API_PATH,
    LIST_API_PATH,
    PAGE_URL,
    EmailTemplatesLocators,
)
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class EmailTemplatesPage(BasePage):
    PATH = "/email-templates"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = EmailTemplatesLocators(page)
        self.last_list_response: Response | None = None
        """The table request the page answered on load."""
        self.create_requests: list[str] = []
        """Every create request the page has sent, so a test can prove none was sent."""
        page.on("request", self._record_create_request)

    def _record_create_request(self, request: Request) -> None:
        if request.method == "POST" and request.url.split("?")[0].rstrip("/").endswith(LIST_API_PATH):
            self.create_requests.append(request.url)

    def open_from_sidebar(self) -> None:
        """Expand "My Account" and open its "Email Templates" link.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'My Account' sidebar menu")
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.email_templates_link, "'Email Templates' My Account sub-menu link")
        self.last_list_response = response.value
        self.page.wait_for_url(PAGE_URL)

    @staticmethod
    def _is_list_response(response: Response) -> bool:
        return LIST_API_PATH in response.url and response.request.method == "GET"

    # Add Template modal

    def open_add_template_modal(self) -> None:
        self.click(self.locators.add_template_button, "'+ Add Template'")
        self.locators.add_template_modal.wait_for()

    def fill_add_template_form(
        self,
        *,
        name: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        channel_store_id: str | None = None,
    ) -> None:
        """Fill the fields that are given; the ones left out keep whatever they hold."""
        fields = (
            (self.locators.modal_name_input, name, "Name"),
            (self.locators.modal_subject_input, subject, "Subject"),
            (self.locators.modal_body_input, body, "Body (HTML)"),
            (self.locators.modal_channel_store_id_input, channel_store_id, "Channel store id"),
        )
        for locator, value, description in fields:
            if value is not None:
                self.fill(locator, value, f"the Add Template {description} field")

    def save_expecting_no_create(self) -> None:
        """Click Save with a required field missing and let the page settle.

        The application sends no create request at all in this case, so there is no response to
        wait for; the click is followed by the table request the page would have sent on a
        successful save, which never arrives. Waiting for the network to go idle keeps the wait
        bound to the application rather than to a fixed sleep.
        """
        self.click(self.locators.modal_save_button, "'Save' (expecting no template to be created)")
        self.page.wait_for_load_state("networkidle")

    def save_expecting_create(self) -> Response:
        """Click Save with every required field filled and return the create response."""
        with self.page.expect_response(self._is_create_response) as response:
            self.click(self.locators.modal_save_button, "'Save'")
        self.locators.add_template_modal.wait_for(state="hidden")
        return response.value

    def cancel_add_template_modal(self) -> None:
        self.click(self.locators.modal_cancel_button, "'Cancel' in the Add Template modal")
        self.locators.add_template_modal.wait_for(state="hidden")

    # Search / filter

    def search(self, *, name: str | None = None, status_label: str | None = None) -> Response:
        """Set the filters that are given, click Search and return the table response."""
        if name is not None:
            self.fill(self.locators.name_input, name, "the Name filter")
        if status_label is not None:
            value = self.locators.status_option(status_label).get_attribute("value")
            logger.info("Select the '%s' Status filter", status_label)
            self.locators.status_select.select_option(value or "")
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.search_button, "'Search'")
        return response.value

    def reset(self) -> Response:
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.reset_button, "'Reset'")
        return response.value

    # Delete

    def delete_template(self, name: str) -> Response:
        """Delete the template with this exact name through its row action and the confirmation."""
        row = self.locators.row_for(name)
        self.click(self.locators.row_delete_button(row), f"the Delete action of the '{name}' row")
        self.locators.delete_dialog.wait_for()
        with self.page.expect_response(self._is_delete_response) as response:
            self.click(self.locators.delete_dialog_confirm_button, "'Delete' in the confirmation")
        self.locators.delete_dialog.wait_for(state="hidden")
        return response.value

    @staticmethod
    def _is_create_response(response: Response) -> bool:
        return (
            response.request.method == "POST"
            and response.url.split("?")[0].rstrip("/").endswith(LIST_API_PATH)
        )

    @staticmethod
    def _is_delete_response(response: Response) -> bool:
        return response.request.method == "DELETE" and DELETE_API_PATH.search(response.url) is not None
