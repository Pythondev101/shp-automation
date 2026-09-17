"""Page object of the SHP My Profile page."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from playwright.sync_api import Error, Locator, Page, Response

from framework.locators.my_profile_locators import MyProfileLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class MyProfilePage(BasePage):
    PATH = "/profile"

    PROFILE_API_PATH = "/api/v1/profile"  # POST: Save Profile
    PASSWORD_API_PATH = "/api/v1/profile/password"  # POST: Change Password
    STATES_API_PATH = "/api/v1/profile/states"  # GET ?country_id=<id>
    CITIES_API_PATH = "/api/v1/profile/cities"  # GET ?state_id=<id>

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = MyProfileLocators(page)

    def open_from_sidebar(self) -> None:
        """Open the page the way a user does: "My Account" in the sidebar, then "My Profile"."""
        self.click(self.locators.sidebar_my_account_menu, "'My Account' sidebar menu")
        self.click(self.locators.sidebar_my_profile_entry, "'My Profile' sub-menu entry")

    def reload(self) -> None:
        """Reload the page, so every field shows what the server has saved."""
        logger.info("Reload %s", self.PATH)
        self.page.reload()
        self.locators.full_name_input.wait_for()

    @staticmethod
    def selectable_values(dropdown: Locator) -> list[str]:
        """Values of a dropdown's real options, without the empty "Select" placeholder.

        The options are loaded after the field renders, so this waits until the first real one exists.
        """
        options = dropdown.locator("option")
        options.nth(1).wait_for(state="attached")
        return [value for value in options.evaluate_all("os => os.map(o => o.value)") if value]

    def select(self, dropdown: Locator, value: str, description: str) -> None:
        logger.info("Select an option in %s", description)
        dropdown.select_option(value)

    def select_country(self, country_id: str) -> list[str]:
        """Choose a country and return the names of the states the application loaded for it."""
        return self._select_and_read_names(
            self.locators.country_select, country_id, "Country dropdown", self.STATES_API_PATH, "country_id", "states"
        )

    def select_state(self, state_id: str) -> list[str]:
        """Choose a state and return the names of the cities the application loaded for it."""
        return self._select_and_read_names(
            self.locators.state_select, state_id, "State dropdown", self.CITIES_API_PATH, "state_id", "cities"
        )

    def save_profile(self) -> dict[str, Any]:
        """Press Save Profile and return the server's answer (``status``, ``message``)."""
        with self.page.expect_response(lambda r: self._is_post_to(r, self.PROFILE_API_PATH)) as answer:
            self.click(self.locators.save_profile_button, "'Save Profile' button")
        return answer.value.json()

    def restore_field(self, field: Locator, original: str, description: str) -> dict[str, Any]:
        """Reload the saved profile, put ``original`` back into ``field`` and save; returns the server's answer."""
        logger.info("Restore the original value of %s", description)
        self.reload()
        self.fill(field, original, description)
        return self.save_profile()

    @contextmanager
    def handling_passwords(self) -> Iterator[None]:
        """Keep the passwords typed inside the block out of traces and failure evidence.

        Tracing is stopped for the whole block (it records typed text and the password
        request bodies), and the three password fields are emptied when the block ends,
        so a failure screenshot or a later trace snapshot cannot show a password.
        """
        with self._untraced():
            try:
                yield
            finally:
                for field in (
                    self.locators.current_password_input,
                    self.locators.new_password_input,
                    self.locators.confirm_password_input,
                ):
                    try:
                        field.fill("")
                    except Error:
                        pass  # the page is already broken; keep the original failure

    def enter_passwords(self, current: str, new: str) -> None:
        """Fill Current Password, and the new password into both New and Confirm New Password."""
        self.fill_secret(self.locators.current_password_input, current, "Current Password field")
        self.fill_secret(self.locators.new_password_input, new, "New Password field")
        self.fill_secret(self.locators.confirm_password_input, new, "Confirm New Password field")

    def toggle_password_visibility(self, eye: Locator, description: str) -> None:
        self.click(eye, f"eye icon of the {description} field")

    def change_password(self) -> dict[str, Any]:
        """Press Change Password and return the server's answer (``status``, ``message``)."""
        with self.page.expect_response(lambda r: self._is_post_to(r, self.PASSWORD_API_PATH)) as answer:
            self.click(self.locators.change_password_button, "'Change Password' button")
        return answer.value.json()

    def _select_and_read_names(
        self, dropdown: Locator, value: str, description: str, api_path: str, param: str, key: str
    ) -> list[str]:
        def is_list_request(response: Response) -> bool:
            return api_path in response.url and f"{param}={value}" in response.url

        with self.page.expect_response(is_list_request) as answer:
            self.select(dropdown, value, description)
        return [item["name"] for item in answer.value.json()["data"][key]]

    @staticmethod
    def _is_post_to(response: Response, api_path: str) -> bool:
        return response.request.method == "POST" and response.url.endswith(api_path)
