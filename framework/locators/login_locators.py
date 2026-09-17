"""Locators of the SHP login page (``/login``).

Verified against the live DOM on 2026-09-11. The page has no ``data-testid``
attributes and its <label> elements are not linked to their inputs, so the two
fields are located by their ``name`` attribute and everything else by
accessible role and name, as Playwright recommends. Validation messages have no
role or id; they are located by their exact text, which is what the tests verify.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page


class LoginLocators:
    """Every element the login tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self.heading: Locator = page.get_by_role("heading", name="Sign in to your account", exact=True)
        self.email_input: Locator = page.locator("input[name='email']")
        self.password_input: Locator = page.locator("input[name='password']")
        # The eye button's accessible name switches between "Show password" and "Hide password".
        self.password_visibility_toggle: Locator = page.get_by_role(
            "button", name=re.compile(r"^(Show|Hide) password$")
        )
        self.forgot_password_link: Locator = page.get_by_role("link", name="Forgot password?", exact=True)
        self.register_link: Locator = page.get_by_role("link", name="Register", exact=True)
        self.sign_in_button: Locator = page.get_by_role("button", name="Sign in", exact=True)

        # Client-side validation messages shown under the fields after submitting.
        self.email_required_message: Locator = page.get_by_text("Email is required", exact=True)
        self.password_required_message: Locator = page.get_by_text("Password is required", exact=True)

        # Elements that identify the pages the login page leads to. Used only to confirm
        # that navigation; those pages get their own locators when they are automated.
        self.forgot_password_page_heading: Locator = page.get_by_role(
            "heading", name="Forgot your password?", exact=True
        )
        self.register_page_heading: Locator = page.get_by_role("heading", name="Create your account", exact=True)
        # Header button present on every page of the signed-in application.
        self.signed_in_indicator: Locator = page.get_by_role("button", name="Notifications", exact=True)
