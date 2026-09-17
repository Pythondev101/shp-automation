"""Login page: page load, form elements, links, client-side validation and valid sign-in.

Lockout safety: SHP may deactivate an account after 3 wrong passwords, so these
tests never submit wrong or invalid credentials. Validation tests abort every API
request in the browser, so nothing reaches the server; sign-in tests use only the
.env account, and a sign-in the server does not confirm stops the whole run.
Every test gets a new browser context from pytest-playwright, so tests are independent.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, Route, expect

from framework.config import Credentials
from framework.pages.login_page import LoginPage

pytestmark = [pytest.mark.authentication, pytest.mark.regression]

# Typed into the form only; never submitted to the server.
DUMMY_PASSWORD_TEXT = "Visibility-Check-123"
DUMMY_EMAIL = "validation.check@example.com"


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """The login page, opened in a fresh browser context."""
    login_page = LoginPage(page)
    login_page.open()
    return login_page


@pytest.fixture
def blocked_api_requests(page: Page) -> list[str]:
    """Aborts every API request before it leaves the browser and records it.

    Lets validation tests prove that no sign-in attempt was sent.
    """
    attempted: list[str] = []

    def abort(route: Route) -> None:
        attempted.append(f"{route.request.method} {route.request.url}")
        route.abort()

    page.route(LoginPage.API_URL_PATTERN, abort)
    return attempted


# --- Page and form elements -------------------------------------------------


@pytest.mark.smoke
def test_login_url_opens_successfully(page: Page, base_url: str) -> None:
    response = LoginPage(page).open()

    assert response is not None, "Navigation to the login page returned no response"
    assert response.ok, f"Login URL returned HTTP {response.status}"
    expect(page).to_have_url(f"{base_url}{LoginPage.PATH}")


@pytest.mark.smoke
def test_login_page_is_displayed(login_page: LoginPage) -> None:
    expect(login_page.locators.heading).to_be_visible()


@pytest.mark.smoke
def test_email_field_is_visible_and_enabled(login_page: LoginPage) -> None:
    expect(login_page.locators.email_input).to_be_visible()
    expect(login_page.locators.email_input).to_be_enabled()
    expect(login_page.locators.email_input).to_be_editable()


@pytest.mark.smoke
def test_password_field_is_visible_and_enabled(login_page: LoginPage) -> None:
    expect(login_page.locators.password_input).to_be_visible()
    expect(login_page.locators.password_input).to_be_enabled()
    expect(login_page.locators.password_input).to_be_editable()


@pytest.mark.smoke
def test_sign_in_button_is_visible_and_enabled(login_page: LoginPage) -> None:
    expect(login_page.locators.sign_in_button).to_be_visible()
    expect(login_page.locators.sign_in_button).to_be_enabled()


@pytest.mark.functional
def test_forgot_password_link_opens_forgot_password_page(login_page: LoginPage, base_url: str) -> None:
    expect(login_page.locators.forgot_password_link).to_be_visible()

    login_page.go_to_forgot_password()

    expect(login_page.page).to_have_url(f"{base_url}{LoginPage.FORGOT_PASSWORD_PATH}")
    expect(login_page.locators.forgot_password_page_heading).to_be_visible()


@pytest.mark.functional
def test_register_link_opens_register_page(login_page: LoginPage, base_url: str) -> None:
    expect(login_page.locators.register_link).to_be_visible()

    login_page.go_to_register()

    expect(login_page.page).to_have_url(f"{base_url}{LoginPage.REGISTER_PATH}")
    expect(login_page.locators.register_page_heading).to_be_visible()


# --- Password field behaviour -----------------------------------------------


def test_password_is_masked_by_default(login_page: LoginPage) -> None:
    login_page.enter_password(DUMMY_PASSWORD_TEXT)

    expect(login_page.locators.password_input).to_have_attribute("type", "password")


@pytest.mark.functional
def test_password_visibility_toggle_shows_and_hides_password(login_page: LoginPage) -> None:
    password_input = login_page.locators.password_input
    toggle = login_page.locators.password_visibility_toggle
    expect(toggle).to_be_visible()
    expect(toggle).to_have_accessible_name("Show password")
    login_page.enter_password(DUMMY_PASSWORD_TEXT)

    login_page.toggle_password_visibility()
    expect(password_input).to_have_attribute("type", "text")
    expect(password_input).to_have_value(DUMMY_PASSWORD_TEXT)
    expect(toggle).to_have_accessible_name("Hide password")

    login_page.toggle_password_visibility()
    expect(password_input).to_have_attribute("type", "password")
    expect(password_input).to_have_value(DUMMY_PASSWORD_TEXT)
    expect(toggle).to_have_accessible_name("Show password")


# --- Input and client-side validation (nothing is sent to the server) -------


@pytest.mark.functional
def test_fields_accept_valid_input(login_page: LoginPage) -> None:
    login_page.enter_email(DUMMY_EMAIL)
    login_page.enter_password(DUMMY_PASSWORD_TEXT)

    expect(login_page.locators.email_input).to_have_value(DUMMY_EMAIL)
    expect(login_page.locators.password_input).to_have_value(DUMMY_PASSWORD_TEXT)


@pytest.mark.functional
def test_empty_email_shows_required_message_without_sign_in_request(
    blocked_api_requests: list[str], login_page: LoginPage, base_url: str
) -> None:
    login_page.enter_password(DUMMY_PASSWORD_TEXT)

    login_page.click_sign_in()

    expect(login_page.locators.email_required_message).to_be_visible()
    expect(login_page.locators.password_required_message).to_be_hidden()
    expect(login_page.page).to_have_url(f"{base_url}{LoginPage.PATH}")
    assert blocked_api_requests == [], f"The form sent API requests: {blocked_api_requests}"


@pytest.mark.functional
def test_empty_password_shows_required_message_without_sign_in_request(
    blocked_api_requests: list[str], login_page: LoginPage, base_url: str
) -> None:
    login_page.enter_email(DUMMY_EMAIL)

    login_page.click_sign_in()

    expect(login_page.locators.password_required_message).to_be_visible()
    expect(login_page.locators.email_required_message).to_be_hidden()
    expect(login_page.page).to_have_url(f"{base_url}{LoginPage.PATH}")
    assert blocked_api_requests == [], f"The form sent API requests: {blocked_api_requests}"


# --- Valid sign-in (the .env account only) ----------------------------------


@pytest.mark.smoke
@pytest.mark.functional
def test_valid_credentials_sign_in_and_open_dashboard(
    login_page: LoginPage, credentials: Credentials, base_url: str
) -> None:
    login_page.login(credentials)

    expect(login_page.page).to_have_url(f"{base_url}{LoginPage.DASHBOARD_PATH}")
    expect(login_page.locators.signed_in_indicator).to_be_visible()
    expect(login_page.locators.sign_in_button).to_be_hidden()


@pytest.mark.functional
def test_enter_key_submits_login_form(login_page: LoginPage, credentials: Credentials, base_url: str) -> None:
    login_page.login(credentials, press_enter=True)

    expect(login_page.page).to_have_url(f"{base_url}{LoginPage.DASHBOARD_PATH}")
    expect(login_page.locators.signed_in_indicator).to_be_visible()


@pytest.mark.functional
def test_session_persists_after_page_refresh(authenticated_page: Page, base_url: str) -> None:
    signed_in_indicator = LoginPage(authenticated_page).locators.signed_in_indicator
    expect(signed_in_indicator).to_be_visible()

    authenticated_page.reload()

    expect(authenticated_page).to_have_url(f"{base_url}{LoginPage.DASHBOARD_PATH}")
    expect(signed_in_indicator).to_be_visible()


def test_password_is_not_written_to_logs(
    authenticated_page: Page, credentials: Credentials, caplog: pytest.LogCaptureFixture, pytestconfig: pytest.Config
) -> None:
    # authenticated_page guarantees a sign-in happened in this run, in this test or an earlier one.
    log_file = Path(pytestconfig.getoption("log_file") or pytestconfig.getini("log_file")).resolve()
    log_text = log_file.read_text(encoding="utf-8")
    captured = "\n".join(record.getMessage() for when in ("setup", "call") for record in caplog.get_records(when))

    # Booleans only, so a failure message can never print the password or the log itself.
    password_in_log_file = credentials.password in log_text
    password_in_captured_logs = credentials.password in captured
    password_in_credentials_repr = credentials.password in repr(credentials)
    sign_in_was_logged = "Fill password field (value hidden)" in log_text
    assert not password_in_log_file, f"Password found in {log_file}"
    assert not password_in_captured_logs, "Password found in the captured log records"
    assert not password_in_credentials_repr, "Password found in the text form of Credentials"
    assert sign_in_was_logged, f"No sign-in found in {log_file}, so the check above proves nothing"
