"""Locators of the SHP My Profile page (``/profile``).

Verified against the live DOM on 2026-09-12. The page has no ``data-testid``
attributes and, unlike the other modules, **its form fields carry no accessible
name at all**: every field is a ``<label>`` that is not linked to its control
(no ``for``/``id``), and the controls have no ``name``, ``id`` or ``aria-label``.
Only the buttons, and the three password fields (placeholders), can be located by
role and name.

Each field is therefore located through its own label, which is the only stable,
user-visible anchor the page offers:

    <div class="col-md-6">
      <label><i class="bi bi-person"></i>Full Name<span> *</span></label>
      <input class="form-control form-control-sm" value="...">
    </div>

``_field()`` finds the label by its text and takes the first control of the wanted
kind that follows it in the document. The Email and Mobile controls sit one level
deeper (next to their "Change ..." button), which the ``following`` axis covers,
so every field uses the same rule.

The profile values shown on the page (name, username, email address, mobile
number, company, address) belong to the account and are deliberately not part of
any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_HEADING = "My Profile"
"""Page title; also the last breadcrumb entry, so it is pinned to the heading role."""

PERSONAL_SECTION_HEADING = "Personal & Contact Information"
BUSINESS_SECTION_HEADING = "Business & Address Information"
SECURITY_SECTION_HEADING = "Security"

SECTION_HEADINGS = (
    PERSONAL_SECTION_HEADING,
    BUSINESS_SECTION_HEADING,
    SECURITY_SECTION_HEADING,
)
"""Every card of the page, in the order it renders them."""

AVATAR = '[aria-label*="profile photo" i]'
"""The avatar: a circle holding the account's initial, named by ``aria-label`` only."""

PROFILE_SAVED_MESSAGE = "Profile updated successfully."
PASSWORD_CHANGED_MESSAGE = "Password changed successfully."
"""Success toasts of Save Profile and Change Password (shown with role ``status``)."""

SHOW_PASSWORD = "Show password"
HIDE_PASSWORD = "Hide password"
"""``aria-label`` of an eye button while its password field is masked / revealed."""

PLACEHOLDER_OPTION = "Select"
"""Text of the empty first option of every dropdown."""

POSTAL_EXAMPLE_PREFIX = "e.g. "
"""The Pincode placeholder reads ``e.g. <example>`` when the application knows the country's postal format."""


class MyProfileLocators:
    """Every element the My Profile tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Sidebar: "My Account" opens the sub-menu that holds "My Profile".
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_my_account_menu: Locator = sidebar_menu.get_by_role("button", name="My Account")
        self.sidebar_my_profile_entry: Locator = sidebar_menu.get_by_role("link", name="My Profile")

        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING, exact=True, level=5)

        # Personal & Contact Information.
        self.personal_section_heading: Locator = self.section_heading(PERSONAL_SECTION_HEADING)
        self.avatar: Locator = self._main.locator(AVATAR)
        # "Upload Photo" is a label wrapping a hidden file input, not a button.
        self.upload_photo_button: Locator = self._main.get_by_text("Upload Photo", exact=True)
        self.full_name_input: Locator = self._field("Full Name")
        self.username_input: Locator = self._field("Username")
        self.email_input: Locator = self._field("Email")
        self.change_email_button: Locator = self._main.get_by_role("button", name="Change Email", exact=True)
        self.mobile_input: Locator = self._field("Mobile")
        self.change_phone_button: Locator = self._main.get_by_role("button", name="Change Phone", exact=True)
        self.gender_select: Locator = self._field("Gender", "select")
        # A native date picker (``type="date"``), so the field and its calendar are one control.
        self.date_of_birth_input: Locator = self._field("Date of Birth")

        # Business & Address Information.
        self.business_section_heading: Locator = self.section_heading(BUSINESS_SECTION_HEADING)
        self.company_name_input: Locator = self._field("Company Name")
        self.country_select: Locator = self._field("Country", "select")
        self.state_select: Locator = self._field("State", "select")
        self.city_select: Locator = self._field("City", "select")
        self.state_options: Locator = self.state_select.locator("option")
        self.city_options: Locator = self.city_select.locator("option")
        self.timezone_select: Locator = self._field("Timezone", "select")
        self.pincode_input: Locator = self._field("Pincode")
        # Shown under the field while the typed value does not match the country's postal format.
        self.pincode_error: Locator = self._main.get_by_text(re.compile(r"^Enter a valid postal code"))
        self.address_1_input: Locator = self._field("Address 1")
        self.address_2_input: Locator = self._field("Address 2")
        self.description_input: Locator = self._field("Description", "textarea")
        # The name of this button starts with an icon glyph, so it is matched as a substring.
        self.save_profile_button: Locator = self._main.get_by_role("button", name="Save Profile")

        # Security. These three fields are the only ones with a placeholder, and
        # "New Password" is a substring of "Confirm New Password", so they are located
        # by placeholder rather than by label text.
        self.security_section_heading: Locator = self.section_heading(SECURITY_SECTION_HEADING)
        self.current_password_input: Locator = self._main.get_by_placeholder("Enter current password")
        self.new_password_input: Locator = self._main.get_by_placeholder("Enter new password")
        self.confirm_password_input: Locator = self._main.get_by_placeholder("Confirm new password")
        # All three eye buttons are named "Show password", so each is taken from its own field.
        self.current_password_eye: Locator = _eye_icon_of(self.current_password_input)
        self.new_password_eye: Locator = _eye_icon_of(self.new_password_input)
        self.confirm_password_eye: Locator = _eye_icon_of(self.confirm_password_input)
        self.change_password_button: Locator = self._main.get_by_role("button", name="Change Password")

    def section_heading(self, name: str) -> Locator:
        """The heading of one of the page's cards."""
        return self._main.get_by_role("heading", name=name, exact=True, level=6)

    def toast(self, message: str) -> Locator:
        """A toast notification showing ``message``; toasts render outside ``main``."""
        return self._page.get_by_role("status").filter(has_text=message)

    def _field(self, label: str, control: str = "input") -> Locator:
        """The control belonging to the field labelled ``label``.

        The page links no label to its control, so the label's text is the anchor
        and the first following control of that kind is the field.
        """
        return self._main.locator("label").filter(has_text=label).locator(
            f"xpath=following::{control}[1]"
        )


def _eye_icon_of(password_input: Locator) -> Locator:
    """The show/hide button that sits inside a password field, right after its input."""
    return password_input.locator("xpath=following-sibling::button[1]")
