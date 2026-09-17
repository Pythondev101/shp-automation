"""Page object of the SHP login page."""

from __future__ import annotations

import logging

from playwright.sync_api import Error, Page, Response

from framework.config import Credentials
from framework.locators.login_locators import LoginLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """The server did not confirm a sign-in.

    Never retry after it: SHP may deactivate an account after repeated failed
    sign-ins. The test run is stopped when it is raised (see tests/conftest.py).
    """


class LoginPage(BasePage):
    PATH = "/login"
    FORGOT_PASSWORD_PATH = "/forgot-password"
    REGISTER_PATH = "/register"
    DASHBOARD_PATH = "/dashboard"  # where a successful sign-in lands

    SIGN_IN_API_PATH = "/api/v1/auth/web_login"
    API_URL_PATTERN = "**/api/**"  # every backend call, including sign-in

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = LoginLocators(page)

    def enter_email(self, email: str) -> None:
        self.fill(self.locators.email_input, email, "email field")

    def enter_password(self, password: str) -> None:
        self.fill_secret(self.locators.password_input, password, "password field")

    def toggle_password_visibility(self) -> None:
        self.click(self.locators.password_visibility_toggle, "password visibility (eye) button")

    def click_sign_in(self) -> None:
        self.click(self.locators.sign_in_button, "'Sign in' button")

    def go_to_forgot_password(self) -> None:
        self.click(self.locators.forgot_password_link, "'Forgot password?' link")

    def go_to_register(self) -> None:
        self.click(self.locators.register_link, "'Register' link")

    def login(self, credentials: Credentials, *, press_enter: bool = False) -> None:
        """Sign in with the given account and wait until the login form is gone.

        Submits exactly once, with the Sign in button or the Enter key. Typing the
        credentials and the sign-in request are kept out of Playwright traces.

        Raises:
            AuthenticationError: the server did not confirm the sign-in.
        """
        logger.info("Sign in with the configured account (%s)", "Enter key" if press_enter else "Sign in button")
        with self._untraced():
            self.enter_email(credentials.username)
            self.enter_password(credentials.password)
            try:
                self._submit_and_confirm(press_enter)
                # Trace snapshots record input values, so tracing resumes only once the form is gone.
                self.locators.password_input.wait_for(state="detached")
            except Exception:
                if self.locators.password_input.count():
                    self.locators.password_input.fill("")  # keep the password out of failure evidence
                raise
        logger.info("Signed in; left the login page")

    def _submit_and_confirm(self, press_enter: bool) -> None:
        try:
            with self.page.expect_response(self._is_sign_in_response) as answer:
                if press_enter:
                    self.press(self.locators.password_input, "Enter", "password field")
                else:
                    self.click_sign_in()
            response = answer.value
            body = response.json()
        except (Error, ValueError) as exc:
            # The request may still have reached the server, so this counts as a failed sign-in.
            reason = exc.message if isinstance(exc, Error) else str(exc)
            raise AuthenticationError(f"No readable answer to the sign-in request: {reason.splitlines()[0]}") from exc

        if not (response.ok and isinstance(body, dict) and body.get("status") is True):
            message = body.get("message") if isinstance(body, dict) else None
            raise AuthenticationError(f"Sign-in was not confirmed (HTTP {response.status}, message: {message!r})")

    def _is_sign_in_response(self, response: Response) -> bool:
        return response.request.method == "POST" and response.url.endswith(self.SIGN_IN_API_PATH)
