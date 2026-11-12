"""Reusable client for the SHP login API.

Tests never call ``requests`` themselves: they call ``LoginApi.login()`` and
assert on the response it returns.
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


class LoginApi:
    LOGIN_PATH = "/api/v1/auth/web_login"
    TIMEOUT_SECONDS = 60  # the test server can be slow to answer

    def __init__(self, base_url: str, session: requests.Session) -> None:
        self.url = base_url + self.LOGIN_PATH
        self.session = session

    def login(self, payload: dict[str, str]) -> requests.Response:
        """Send one login request with exactly the given JSON payload.

        The payload is sent as it is, so a test can leave a field out or send it
        empty. Only the field names are logged - never the values, and never the
        token of the response.
        """
        logger.info("POST %s | fields sent: %s", self.LOGIN_PATH, sorted(payload))
        response = self.session.post(self.url, json=payload, timeout=self.TIMEOUT_SECONDS)
        logger.info("Answer: HTTP %s | message: %r", response.status_code, self.message_of(response))
        return response

    def login_with(self, email: str, password: str) -> requests.Response:
        """Send one login request with an email and a password."""
        return self.login({"email": email, "password": password})

    @staticmethod
    def message_of(response: requests.Response) -> str | None:
        """The ``message`` of a login answer, or ``None`` when the body is not the expected JSON."""
        try:
            body = response.json()
        except ValueError:
            return None
        return body.get("message") if isinstance(body, dict) else None

    @staticmethod
    def token_of(response: requests.Response) -> str | None:
        """The access token of a login answer, or ``None`` when the answer carries none."""
        data = response.json().get("data")
        return data.get("access_token") if isinstance(data, dict) else None
