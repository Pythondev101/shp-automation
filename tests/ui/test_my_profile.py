"""My Account → My Profile: visibility of the page's fields and controls, and their functionality.

Visibility tests (``smoke``) only check presence and change nothing.

Functionality tests (``functional``) type into the profile fields and choose dropdown
options without saving, except for four tests that do save and always put the
account back: the numeric-only Full Name check, Save Profile (Company Name only),
Save Profile with every required field, and the password change, which changes the
password to a temporary one and immediately back to the ``.env`` password. The profile
saves need every required field of the saved profile to hold a value: the application
refuses to save an empty required field, so an empty original could not be restored.
The required-field validation tests send no save at all. Change Email / Phone, their OTPs, Upload Photo and
Billing are not touched, and no wrong current password is ever submitted. The page
comes from the ``authenticated_page`` fixture (one sign-in per browser per run).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.config import Credentials
from framework.locators.my_profile_locators import (
    HIDE_PASSWORD,
    PASSWORD_CHANGED_MESSAGE,
    PLACEHOLDER_OPTION,
    POSTAL_EXAMPLE_PREFIX,
    PROFILE_SAVED_MESSAGE,
    REQUIRED_FIELD_MESSAGES,
    SECTION_HEADINGS,
    SHOW_PASSWORD,
)
from framework.pages.my_profile_page import MyProfilePage

pytestmark = pytest.mark.regression

VALID_TEXT = "SHP Automation Test"
NUMERIC_ONLY_NAME = "12345"
VALID_DATE_OF_BIRTH = "1990-05-15"  # yyyy-mm-dd, the value format of a native date field
SAVED_COMPANY_NAME = "SHP Automation Test Company"
SAVED_ADDRESS_1 = "101 Dummy Test Street"  # made-up address, not real data
SAVED_ADDRESS_2 = "Dummy Test Town"
PROTECTED_REQUIRED_FIELDS = ("Username", "Email")
"""Required fields that cannot be edited here (disabled, or changed only through OTP); their label may add a note."""
TEMPORARY_PASSWORD = "tester1"  # agreed temporary password (a letter and a digit); still handled as a secret
MAX_OPTIONS_TRIED = 10
"""How many countries / states are tried to find one the application has states / cities for."""


@pytest.fixture
def my_profile(authenticated_page: Page) -> MyProfilePage:
    """The My Profile page, opened through the sidebar of the signed-in dashboard."""
    page = MyProfilePage(authenticated_page)
    page.open_from_sidebar()
    return page


def _another_value(values: list[str], current: str) -> str:
    """The first dropdown value that differs from the one currently selected."""
    return next(value for value in values if value != current)


def _valid_profile_values(my_profile: MyProfilePage, original: dict[str, str]) -> dict[str, str]:
    """Valid values for every required editable field, taken from the live options and differing where possible.

    The country stays the saved one (so its postal format is known). The state is another
    one of that country with cities; choosing it loads its cities into the form.
    """
    locators = my_profile.locators
    country = original["country_select"] or my_profile.selectable_values(locators.country_select)[0]
    if country != locators.country_select.input_value():
        my_profile.select_country(country)
    cities: list[str] = []
    candidates = [v for v in my_profile.selectable_values(locators.state_select) if v != original["state_select"]]
    for state in candidates[:MAX_OPTIONS_TRIED]:
        cities = my_profile.select_state(state)
        if cities:
            break
    assert cities, f"None of the first {MAX_OPTIONS_TRIED} other states of the saved country has cities"
    # The City list is exactly the cities the application returned for the chosen state.
    expect(locators.city_options).to_have_text([PLACEHOLDER_OPTION, *cities])
    timezone = locators.timezone_select
    placeholder = locators.pincode_input.get_attribute("placeholder") or ""
    assert placeholder.startswith(POSTAL_EXAMPLE_PREFIX), "The application shows no postal code example for the country"
    return {
        "full_name_input": VALID_TEXT,
        "company_name_input": SAVED_COMPANY_NAME,
        "country_select": country,
        "state_select": state,
        "city_select": my_profile.selectable_values(locators.city_select)[0],
        "timezone_select": _another_value(my_profile.selectable_values(timezone), original["timezone_select"]),
        "pincode_input": placeholder.removeprefix(POSTAL_EXAMPLE_PREFIX),
        "address_1_input": SAVED_ADDRESS_1,
        "address_2_input": SAVED_ADDRESS_2,
    }


@pytest.mark.smoke
def test_my_profile_page_opens_successfully(my_profile: MyProfilePage, base_url: str) -> None:
    expect(my_profile.page).to_have_url(f"{base_url}{MyProfilePage.PATH}")
    expect(my_profile.locators.page_heading).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("heading", SECTION_HEADINGS)
def test_page_section_is_visible(my_profile: MyProfilePage, heading: str) -> None:
    expect(my_profile.locators.section_heading(heading)).to_be_visible()


@pytest.mark.smoke
def test_personal_and_contact_information_fields_are_visible(my_profile: MyProfilePage) -> None:
    locators = my_profile.locators
    expect(locators.avatar).to_be_visible()
    expect(locators.upload_photo_button).to_be_visible()
    expect(locators.full_name_input).to_be_visible()
    expect(locators.username_input).to_be_visible()
    expect(locators.email_input).to_be_visible()
    expect(locators.change_email_button).to_be_visible()
    expect(locators.mobile_input).to_be_visible()
    expect(locators.change_phone_button).to_be_visible()
    expect(locators.gender_select).to_be_visible()
    expect(locators.date_of_birth_input).to_be_visible()


@pytest.mark.smoke
def test_business_and_address_information_fields_are_visible(my_profile: MyProfilePage) -> None:
    locators = my_profile.locators
    expect(locators.company_name_input).to_be_visible()
    expect(locators.country_select).to_be_visible()
    expect(locators.state_select).to_be_visible()
    expect(locators.city_select).to_be_visible()
    expect(locators.timezone_select).to_be_visible()
    expect(locators.pincode_input).to_be_visible()
    expect(locators.address_1_input).to_be_visible()
    expect(locators.address_2_input).to_be_visible()
    expect(locators.description_input).to_be_visible()
    expect(locators.save_profile_button).to_be_visible()


@pytest.mark.smoke
def test_security_fields_are_visible(my_profile: MyProfilePage) -> None:
    locators = my_profile.locators
    expect(locators.current_password_input).to_be_visible()
    expect(locators.current_password_eye).to_be_visible()
    expect(locators.new_password_input).to_be_visible()
    expect(locators.new_password_eye).to_be_visible()
    expect(locators.confirm_password_input).to_be_visible()
    expect(locators.confirm_password_eye).to_be_visible()
    expect(locators.change_password_button).to_be_visible()


# --- Functionality -----------------------------------------------------------------


@pytest.mark.functional
def test_username_field_is_read_only(my_profile: MyProfilePage) -> None:
    expect(my_profile.locators.username_input).to_be_disabled()


@pytest.mark.functional
@pytest.mark.parametrize(
    ("field", "description"),
    [
        ("full_name_input", "Full Name field"),
        ("company_name_input", "Company Name field"),
        ("address_1_input", "Address 1 field"),
        ("address_2_input", "Address 2 field"),
        ("description_input", "Description field"),
    ],
)
def test_text_field_accepts_valid_text(my_profile: MyProfilePage, field: str, description: str) -> None:
    locator = getattr(my_profile.locators, field)
    my_profile.fill(locator, VALID_TEXT, description)
    expect(locator).to_have_value(VALID_TEXT)


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_full_name_rejects_numeric_only_value(my_profile: MyProfilePage) -> None:
    full_name = my_profile.locators.full_name_input
    original = full_name.input_value()
    my_profile.fill(full_name, NUMERIC_ONLY_NAME, "Full Name field")
    answer = my_profile.save_profile()
    try:
        assert answer.get("status") is not True, (
            f"A numeric-only full name was saved (server message: {answer.get('message')!r})"
        )
        my_profile.reload()
        expect(full_name).to_have_value(original)
    finally:
        my_profile.reload()
        if full_name.input_value() != original:
            restored = my_profile.restore_field(full_name, original, "Full Name field")
            assert restored.get("status") is True, "The original full name could not be restored"


@pytest.mark.functional
def test_gender_option_can_be_selected(my_profile: MyProfilePage) -> None:
    gender = my_profile.locators.gender_select
    choice = _another_value(my_profile.selectable_values(gender), gender.input_value())
    my_profile.select(gender, choice, "Gender dropdown")
    expect(gender).to_have_value(choice)


@pytest.mark.functional
def test_date_of_birth_accepts_a_valid_date(my_profile: MyProfilePage) -> None:
    date_of_birth = my_profile.locators.date_of_birth_input
    my_profile.fill(date_of_birth, VALID_DATE_OF_BIRTH, "Date of Birth field")
    expect(date_of_birth).to_have_value(VALID_DATE_OF_BIRTH)


@pytest.mark.functional
def test_country_state_city_dependency(my_profile: MyProfilePage) -> None:
    locators = my_profile.locators

    # A different country than the saved one, for which the application has states.
    states: list[str] = []
    other_countries = [v for v in my_profile.selectable_values(locators.country_select)
                       if v != locators.country_select.input_value()]
    for country_id in other_countries[:MAX_OPTIONS_TRIED]:
        states = my_profile.select_country(country_id)
        if states:
            break
    assert states, f"None of the first {MAX_OPTIONS_TRIED} other countries has states"
    expect(locators.country_select).to_have_value(country_id)
    # The State list is replaced by exactly the states of the chosen country; State and City are reset.
    expect(locators.state_select).to_have_value("")
    expect(locators.state_options).to_have_text([PLACEHOLDER_OPTION, *states])
    expect(locators.city_options).to_have_text([PLACEHOLDER_OPTION])

    cities: list[str] = []
    for state_id in my_profile.selectable_values(locators.state_select)[:MAX_OPTIONS_TRIED]:
        cities = my_profile.select_state(state_id)
        if cities:
            break
    assert cities, f"None of the first {MAX_OPTIONS_TRIED} states of the chosen country has cities"
    expect(locators.state_select).to_have_value(state_id)
    # The City list is exactly the cities of the chosen state.
    expect(locators.city_options).to_have_text([PLACEHOLDER_OPTION, *cities])

    city_id = my_profile.selectable_values(locators.city_select)[0]
    my_profile.select(locators.city_select, city_id, "City dropdown")
    expect(locators.city_select).to_have_value(city_id)


@pytest.mark.functional
def test_timezone_option_can_be_selected(my_profile: MyProfilePage) -> None:
    timezone = my_profile.locators.timezone_select
    choice = _another_value(my_profile.selectable_values(timezone), timezone.input_value())
    my_profile.select(timezone, choice, "Timezone dropdown")
    expect(timezone).to_have_value(choice)


@pytest.mark.functional
def test_pincode_accepts_a_valid_postal_code(my_profile: MyProfilePage) -> None:
    pincode = my_profile.locators.pincode_input
    placeholder = pincode.get_attribute("placeholder") or ""
    assert placeholder.startswith(POSTAL_EXAMPLE_PREFIX), (
        "The application shows no postal code example for the profile's country"
    )
    example = placeholder.removeprefix(POSTAL_EXAMPLE_PREFIX)
    my_profile.fill(pincode, example, "Pincode field")
    expect(pincode).to_have_value(example)
    expect(my_profile.locators.pincode_error).to_be_hidden()


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_save_profile_persists_the_change(my_profile: MyProfilePage) -> None:
    company_name = my_profile.locators.company_name_input
    original = company_name.input_value()
    assert original != SAVED_COMPANY_NAME, "The account already holds the test company name"
    my_profile.fill(company_name, SAVED_COMPANY_NAME, "Company Name field")
    answer = my_profile.save_profile()
    try:
        assert answer.get("status") is True, f"Save Profile failed (server message: {answer.get('message')!r})"
        expect(my_profile.locators.toast(PROFILE_SAVED_MESSAGE)).to_be_visible()
        my_profile.reload()
        expect(company_name).to_have_value(SAVED_COMPANY_NAME)
    finally:
        my_profile.reload()
        if company_name.input_value() != original:
            restored = my_profile.restore_field(company_name, original, "Company Name field")
            assert restored.get("status") is True, "The original company name could not be restored"
    my_profile.reload()
    expect(company_name).to_have_value(original)


@pytest.mark.functional
def test_required_fields_are_marked(my_profile: MyProfilePage) -> None:
    my_profile.wait_until_loaded()  # State is marked required only once the country's states are loaded
    required = my_profile.required_fields()
    editable = [name for name, control in required.items() if control.is_editable()]
    protected = {name.split(" (")[0]: control for name, control in required.items() if name not in editable}

    missing = [name for name in REQUIRED_FIELD_MESSAGES if name not in editable]
    assert not missing, f"Fields expected to be required and editable are not: {missing} (live: {list(required)})"
    unknown = [name for name in editable if name not in REQUIRED_FIELD_MESSAGES]
    assert not unknown, f"New required editable fields have no known validation message: {unknown}"
    for name in PROTECTED_REQUIRED_FIELDS:
        assert name in protected, f"{name} is not marked as a required read-only field (live: {list(required)})"
        expect(protected[name]).not_to_have_value("")


@pytest.mark.functional
@pytest.mark.parametrize("field_name", REQUIRED_FIELD_MESSAGES)
def test_save_profile_rejects_empty_required_field(my_profile: MyProfilePage, field_name: str) -> None:
    original = my_profile.profile_values()
    my_profile.fill_profile(_valid_profile_values(my_profile, original))
    field = my_profile.required_fields()[field_name]
    if field.evaluate("e => e.tagName") == "SELECT":
        my_profile.select(field, "", f"{field_name} dropdown")
    else:
        my_profile.fill(field, "", f"{field_name} field")

    sent = my_profile.press_save_expecting_validation(REQUIRED_FIELD_MESSAGES[field_name])
    expect(my_profile.locators.toast(REQUIRED_FIELD_MESSAGES[field_name])).to_be_visible()
    assert not sent, f"Save Profile sent the form with an empty {field_name}"
    my_profile.reload()
    assert my_profile.profile_values() == original, "The profile changed although Save Profile was refused"


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_save_profile_with_all_required_fields_and_restore(my_profile: MyProfilePage) -> None:
    original = my_profile.profile_values()
    values = _valid_profile_values(my_profile, original)
    my_profile.fill_profile(values)
    assert not my_profile.empty_required_fields(), "A required field is still empty before saving"
    answer = my_profile.save_profile()
    try:
        assert answer.get("status") is True, f"Save Profile failed (server message: {answer.get('message')!r})"
        expect(my_profile.locators.toast(PROFILE_SAVED_MESSAGE)).to_be_visible()
        states, cities = my_profile.reload_reading_lists(values["country_select"], values["state_select"])
        assert my_profile.profile_values() == values, "The saved values did not persist after a reload"
        # State offers only the saved country's states and City only the saved state's cities,
        # and the saved state / city are among them.
        locators = my_profile.locators
        expect(locators.state_options).to_have_text([PLACEHOLDER_OPTION, *states])
        expect(locators.city_options).to_have_text([PLACEHOLDER_OPTION, *cities])
        assert locators.state_select.locator("option:checked").text_content() in states
        assert locators.city_select.locator("option:checked").text_content() in cities
    finally:
        my_profile.reload()
        if my_profile.profile_values() != original:
            my_profile.fill_profile(original)
            restored = my_profile.save_profile()
            assert restored.get("status") is True, (
                f"PROFILE NOT RESTORED (server message: {restored.get('message')!r}); original values: {original}"
            )
    my_profile.reload()
    assert my_profile.profile_values() == original, "The profile does not match its original values"


@pytest.mark.functional
@pytest.mark.destructive
@pytest.mark.shared_state
def test_change_password_and_restore_original(my_profile: MyProfilePage, credentials: Credentials) -> None:
    locators = my_profile.locators
    eyes = (
        (locators.current_password_input, locators.current_password_eye, "Current Password"),
        (locators.new_password_input, locators.new_password_eye, "New Password"),
        (locators.confirm_password_input, locators.confirm_password_eye, "Confirm New Password"),
    )
    with my_profile.handling_passwords():
        my_profile.enter_passwords(credentials.password, TEMPORARY_PASSWORD)

        # Each eye icon reveals its own field and masks it again.
        for field, eye, name in eyes:
            my_profile.toggle_password_visibility(eye, name)
            expect(field).to_have_attribute("type", "text")
            expect(eye).to_have_attribute("aria-label", HIDE_PASSWORD)
            my_profile.toggle_password_visibility(eye, name)
            expect(field).to_have_attribute("type", "password")
            expect(eye).to_have_attribute("aria-label", SHOW_PASSWORD)

        changed = my_profile.change_password()
        try:
            assert changed.get("status") is True, (
                f"Password change was not confirmed (server message: {changed.get('message')!r})"
            )
            expect(locators.toast(PASSWORD_CHANGED_MESSAGE)).to_be_visible()
        finally:
            if changed.get("status") is True:
                # Restore immediately, before anything else can fail. A successful restore
                # also proves the temporary password was really set.
                my_profile.enter_passwords(TEMPORARY_PASSWORD, credentials.password)
                restored = my_profile.change_password()
                assert restored.get("status") is True, (
                    "PASSWORD NOT RESTORED: the account still has the temporary password "
                    f"(server message: {restored.get('message')!r})"
                )
