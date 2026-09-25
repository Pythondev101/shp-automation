"""Page object of the SHP My Profile page."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from playwright.sync_api import Error, Locator, Page, Request, Response

from framework.locators.my_profile_locators import REQUIRED_MARK, MyProfileLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class MyProfilePage(BasePage):
    PATH = "/profile"

    PROFILE_API_PATH = "/api/v1/profile"  # POST: Save Profile
    PASSWORD_API_PATH = "/api/v1/profile/password"  # POST: Change Password
    STATES_API_PATH = "/api/v1/profile/states"  # GET ?country_id=<id>
    CITIES_API_PATH = "/api/v1/profile/cities"  # GET ?state_id=<id>

    PROFILE_FIELDS = (
        "full_name_input",
        "company_name_input",
        "country_select",
        "state_select",
        "city_select",
        "timezone_select",
        "pincode_input",
        "address_1_input",
        "address_2_input",
    )
    """Required editable fields Save Profile sends, in the order they are filled (Country → State → City first)."""

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

    def reload_reading_lists(self, country_id: str, state_id: str) -> tuple[list[str], list[str]]:
        """Reload the page and return the names of the states / cities the application loads for the saved country / state."""
        def is_list_request(api_path: str, param: str, value: str) -> Callable[[Response], bool]:
            return lambda response: api_path in response.url and f"{param}={value}" in response.url

        with (
            self.page.expect_response(is_list_request(self.STATES_API_PATH, "country_id", country_id)) as states,
            self.page.expect_response(is_list_request(self.CITIES_API_PATH, "state_id", state_id)) as cities,
        ):
            self.reload()
        return (
            [item["name"] for item in states.value.json()["data"]["states"]],
            [item["name"] for item in cities.value.json()["data"]["cities"]],
        )

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

    def wait_until_loaded(self) -> None:
        """Wait until the dropdowns hold their options, so their saved values can be read.

        A dropdown shows no value until its options arrive; State and City only load
        once a country / state is selected.
        """
        self.selectable_values(self.locators.country_select)
        self.selectable_values(self.locators.timezone_select)
        if self.locators.country_select.input_value():
            self.selectable_values(self.locators.state_select)
        if self.locators.state_select.input_value():
            self.selectable_values(self.locators.city_select)

    def required_fields(self) -> dict[str, Locator]:
        """The fields the live page marks as required (red ``*``), by label text; the password fields are left out."""
        fields: dict[str, Locator] = {}
        self.locators.required_labels.first.wait_for()
        for label in self.locators.required_labels.all():
            control = self.locators.control_of(label)
            if control.get_attribute("type") != "password":
                name = (label.text_content() or "").replace(REQUIRED_MARK, "").strip()
                fields[name] = control
        return fields

    def empty_required_fields(self) -> list[str]:
        """Names of the required editable fields that hold no value."""
        self.wait_until_loaded()
        return [
            name for name, control in self.required_fields().items()
            if control.is_editable() and not control.input_value()
        ]

    def profile_values(self) -> dict[str, str]:
        """Current value of every field in ``PROFILE_FIELDS``."""
        self.wait_until_loaded()
        return {field: getattr(self.locators, field).input_value() for field in self.PROFILE_FIELDS}

    def fill_profile(self, values: dict[str, str]) -> None:
        """Put ``values`` (keyed like ``PROFILE_FIELDS``) into the form, Country before State before City.

        A new country / state waits for the states / cities it loads; an unchanged one sends no request.
        """
        locators = self.locators
        if values["country_select"] != locators.country_select.input_value():
            self.select_country(values["country_select"])
        if values["state_select"] != locators.state_select.input_value():
            self.select_state(values["state_select"])
        for field in self.PROFILE_FIELDS[4:]:
            control = getattr(locators, field)
            if field.endswith("_select"):
                self.select(control, values[field], field.replace("_", " "))
            else:
                self.fill(control, values[field], field.replace("_", " "))
        self.fill(locators.full_name_input, values["full_name_input"], "Full Name field")
        self.fill(locators.company_name_input, values["company_name_input"], "Company Name field")

    def press_save_expecting_validation(self, message: str) -> list[str]:
        """Press Save Profile, wait for the validation toast ``message`` and return the save requests that were sent."""
        sent: list[str] = []

        def record(request: Request) -> None:
            if request.method == "POST" and request.url.endswith(self.PROFILE_API_PATH):
                sent.append(request.url)

        self.page.on("request", record)
        try:
            self.click(self.locators.save_profile_button, "'Save Profile' button")
            self.locators.toast(message).wait_for()
        finally:
            self.page.remove_listener("request", record)
        return sent

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
