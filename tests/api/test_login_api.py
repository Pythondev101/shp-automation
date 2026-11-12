"""Login API tests - ``POST /api/v1/auth/web_login`` (no browser).

Lockout safety: SHP may deactivate an account after 3 wrong passwords. The only
test that sends a wrong password for the real account is
``test_invalid_password_is_rejected``; it is skipped unless it is selected on
purpose with ``-m lockout_risk``. Every other negative test uses an email that
is not an SHP account, so the real account is never involved.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
import requests

from framework.api.login_api import LoginApi
from framework.config import PROJECT_ROOT, Credentials

pytestmark = [pytest.mark.api, pytest.mark.authentication, pytest.mark.regression]

# Test data lives in its own file, so values can change without touching the tests.
DATA = json.loads((PROJECT_ROOT / "test_data" / "login_api_data.json").read_text(encoding="utf-8"))
MESSAGES = DATA["messages"]


@pytest.fixture(scope="module")
def login_api(base_url: str) -> Iterator[LoginApi]:
    """The login API client, with one HTTP session shared by this module's tests."""
    with requests.Session() as session:
        yield LoginApi(base_url, session)


@pytest.fixture(scope="module")
def valid_login(login_api: LoginApi, credentials: Credentials) -> requests.Response:
    """The answer to one sign-in with the configured account, shared by the positive tests."""
    return login_api.login_with(credentials.username, credentials.password)


def assert_login_rejected(response: requests.Response, expected_message: str) -> None:
    """A rejected login: HTTP 200, ``status`` false, the expected message and no token."""
    body = response.json()
    assert response.status_code == 200
    assert body["status"] is False
    assert body["message"] == expected_message
    assert body["data"] is None, "A rejected login must not return any data"
    assert LoginApi.token_of(response) is None, "A rejected login must not return a token"


# --- Positive -----------------------------------------------------------------


@pytest.mark.smoke
def test_valid_credentials_login_succeeds(valid_login: requests.Response) -> None:
    body = valid_login.json()
    assert valid_login.status_code == 200
    assert body["status"] is True
    assert body["message"] == MESSAGES["success"]


@pytest.mark.smoke
def test_valid_login_returns_access_token(valid_login: requests.Response) -> None:
    token = LoginApi.token_of(valid_login)
    assert isinstance(token, str), "A successful login must return data.access_token"
    # The token is a JWT: three parts separated by dots. Only the count is asserted,
    # so the token itself can never appear in a failure message or report.
    part_count = token.count(".") + 1
    assert part_count == 3


# --- Negative -----------------------------------------------------------------


def test_invalid_username_is_rejected(login_api: LoginApi) -> None:
    user = DATA["unknown_user"]
    response = login_api.login_with(user["email"], user["password"])
    assert_login_rejected(response, MESSAGES["invalid_credentials"])


@pytest.mark.lockout_risk
def test_invalid_password_is_rejected(
    request: pytest.FixtureRequest, login_api: LoginApi, credentials: Credentials
) -> None:
    mark_expression = request.config.getoption("markexpr")
    if "lockout_risk" not in mark_expression or "not lockout_risk" in mark_expression:
        pytest.skip("Sends a wrong password for the real account; run on purpose with -m lockout_risk")
    response = login_api.login_with(credentials.username, DATA["wrong_password"])
    assert_login_rejected(response, MESSAGES["invalid_credentials"])


def test_empty_username_and_password_are_rejected(login_api: LoginApi) -> None:
    response = login_api.login(DATA["empty_credentials"])
    assert_login_rejected(response, MESSAGES["required_fields"])


@pytest.mark.parametrize("case", list(DATA["missing_parameters"]))
def test_missing_request_parameters_are_rejected(login_api: LoginApi, case: str) -> None:
    response = login_api.login(DATA["missing_parameters"][case])
    assert_login_rejected(response, MESSAGES["required_fields"])
