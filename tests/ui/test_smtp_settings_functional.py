"""My Account → SMTP Settings: required-field validation, create, edit and delete.

Functional counterpart of ``test_smtp_settings.py`` (which stays visibility-only). These
tests write application data, so every item carries ``destructive``: at most **one** SMTP
setting exists per test, its SMTP Username is ``AUTO_SMTP_<unique id>`` and the
``smtp_cleanup`` fixture deletes it again even when an assertion failed. No pre-existing
setting is ever touched: every action is addressed through that unique username.

Sensitive data: the password comes from ``SHP_TEST_SMTP_PASSWORD`` or, when that is not
set, from a random string generated per run (see ``framework.config.get_sandbox_smtp``).
It is typed through ``fill_secret`` and is never logged, asserted on, printed or written
to a report. The application itself never returns it - the Edit modal shows an empty
"Password (leave blank to keep)" field - so the stored value is never verified.

Out of scope on purpose: sending mail, SMTP delivery or connection behaviour, invalid
credentials, Email Templates and every other My Account page.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect

from framework.config import SandboxSmtp, get_sandbox_smtp
from framework.pages.smtp_settings_page import SmtpSettingsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.regression, pytest.mark.functional, pytest.mark.destructive]

HOST_COLUMN = 1
PORT_COLUMN = 2
USERNAME_COLUMN = 3
"""0-based positions of the columns this module reads (S.No is 0)."""


@pytest.fixture(scope="session")
def sandbox_smtp() -> SandboxSmtp:
    """The sandbox SMTP values to save; one password per run, never a real mail account."""
    smtp = get_sandbox_smtp()
    logger.info("Sandbox SMTP: %s", smtp)  # __str__ holds no password
    return smtp


@pytest.fixture
def smtp_settings(authenticated_page: Page) -> SmtpSettingsPage:
    """The SMTP Settings page, opened through the signed-in sidebar."""
    page = SmtpSettingsPage(authenticated_page)
    page.open_from_sidebar()
    return page


@pytest.fixture
def smtp_cleanup(
    smtp_settings: SmtpSettingsPage, sandbox_smtp: SandboxSmtp
) -> Iterator[list[str]]:
    """Usernames this test creates; each one is deleted afterwards, whatever the test did.

    Append a username **before** clicking Save, so a setting created by a step that then
    failed is still cleaned up. Only usernames carrying the automation prefix are ever
    deleted, and only the ones this test registered. A record that survives the clean-up is
    reported by failing the teardown, which is added to - never replaces - the test failure.
    """
    created: list[str] = []
    yield created

    leftovers: list[str] = []
    for username in created:
        if not username.startswith(sandbox_smtp.username_prefix):
            leftovers.append(f"{username} (refused: not an automation username)")
            continue
        try:
            smtp_settings.reload_list()
            if smtp_settings.locators.row_for(username).count() == 0:
                continue
            logger.info("Clean-up: delete the automation SMTP setting %s", username)
            smtp_settings.delete_setting(username)
            smtp_settings.reload_list()
            if smtp_settings.locators.row_for(username).count() != 0:
                leftovers.append(username)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            leftovers.append(f"{username} ({exc.__class__.__name__}: {exc})")
    assert not leftovers, (
        f"{len(leftovers)} automation SMTP setting(s) left behind and must be deleted by hand: "
        + ", ".join(leftovers)
    )


def unique_username(smtp: SandboxSmtp) -> str:
    """An SMTP username no manual setting can collide with, e.g. ``AUTO_SMTP_1a2b3c4d``."""
    return f"{smtp.username_prefix}{uuid4().hex[:8]}"


# Flow 1 - the Add SMTP Settings modal and required-field validation


def test_add_smtp_modal_opens_with_its_fields(smtp_settings: SmtpSettingsPage) -> None:
    locators = smtp_settings.locators
    modal = smtp_settings.open_add_modal()

    expect(modal).to_be_visible()
    expect(locators.add_modal_title).to_be_visible()
    expect(locators.modal_host_input(modal)).to_be_visible()
    expect(locators.modal_port_input(modal)).to_be_visible()
    expect(locators.modal_username_input(modal)).to_be_visible()
    expect(locators.modal_password_input(modal)).to_be_visible()
    # The password is typed masked and is never revealed by these tests.
    expect(locators.modal_password_input(modal)).to_have_attribute("type", "password")
    expect(locators.modal_encryption_select(modal)).to_be_visible()
    expect(locators.modal_from_email_input(modal)).to_be_visible()
    expect(locators.modal_from_name_input(modal)).to_be_visible()
    expect(locators.modal_save_button(modal)).to_be_visible()
    expect(locators.modal_cancel_button(modal)).to_be_visible()

    smtp_settings.cancel_modal(modal)
    expect(locators.add_modal).to_have_count(0)


@pytest.mark.parametrize(
    "omitted",
    [
        pytest.param(None, id="nothing-filled"),
        pytest.param("host", id="without-host"),
        pytest.param("port", id="without-port"),
        pytest.param("username", id="without-username"),
        pytest.param("from_email", id="without-from-email"),
        pytest.param("password", id="without-password"),
    ],
)
def test_save_creates_nothing_until_every_required_field_is_filled(
    smtp_settings: SmtpSettingsPage,
    sandbox_smtp: SandboxSmtp,
    smtp_cleanup: list[str],
    omitted: str | None,
) -> None:
    """SMTP host, Port, Username, Password and From email are all required.

    Each case fills every required field except one (``nothing-filled`` fills none), so no
    case is complete: Save must send nothing and create nothing. Encryption comes
    pre-selected as TLS and From name carries no asterisk, so neither can be left empty.

    Only the **Password** is given a visible error state by the application; a missing host,
    port, username or From email is rejected silently (see the SMTP Settings section of
    README.md), so those cases assert what does hold - no request, no record, the modal still
    open - and record what the application showed instead of requiring it.

    The username is registered for clean-up before Save, so a setting the application creates
    in spite of the missing field - which would fail this test - is still removed afterwards.
    """
    locators = smtp_settings.locators
    username = unique_username(sandbox_smtp)
    smtp_cleanup.append(username)
    values = {
        "host": sandbox_smtp.host,
        "port": sandbox_smtp.port,
        "username": username,
        "password": sandbox_smtp.password,
        "encryption": sandbox_smtp.encryption,
        "from_email": sandbox_smtp.from_email,
        "from_name": sandbox_smtp.from_name,
    }
    if omitted is None:
        values = {}
    else:
        del values[omitted]

    modal = smtp_settings.open_add_modal()
    smtp_settings.fill_form(modal, **values)

    smtp_settings.save_expecting_no_write(modal)

    # The application sends no create request at all, so nothing can have been created.
    assert smtp_settings.create_requests == [], (
        "Save sent a create request although a required field was empty: "
        f"{smtp_settings.create_requests}"
    )
    # The modal stays open with what was typed still in it, and the page is still alive.
    expect(modal).to_be_visible()
    expect(locators.add_modal_title).to_be_visible()
    expect(locators.modal_host_input(modal)).to_have_value(values.get("host", ""))
    expect(locators.modal_port_input(modal)).to_have_value(values.get("port", ""))
    expect(locators.modal_username_input(modal)).to_have_value(values.get("username", ""))
    expect(locators.modal_from_email_input(modal)).to_have_value(values.get("from_email", ""))
    # The password is never read back, only its presence in the field is checked.
    expect(locators.modal_password_input(modal)).to_have_value(
        re.compile(r".+") if "password" in values else ""
    )

    if omitted == "password":
        # The one field the application does flag: invalid state, a visible message, and Save
        # disabled until it is filled. The message text is read, never hardcoded.
        expect(locators.modal_password_input(modal)).to_contain_class("is-invalid")
        expect(locators.modal_validation_messages(modal).first).to_be_visible()
        message = locators.modal_validation_messages(modal).first.inner_text().strip()
        assert message, "The password was flagged invalid without any message"
        logger.info("Missing password is reported as: %s", message)
        expect(locators.modal_save_button(modal)).to_be_disabled()
    else:
        # How the application marks the other missing fields is its own choice, so it is
        # recorded rather than required; the assertions above and below are what must hold.
        logger.info(
            "Save with no %s: %d field(s) marked invalid, %d validation message(s) shown",
            omitted or "value at all",
            locators.modal_invalid_fields(modal).count(),
            locators.modal_validation_messages(modal).count(),
        )

    # And the table holds no setting with this username.
    smtp_settings.cancel_modal(modal)
    smtp_settings.reload_list()
    expect(locators.row_for(username)).to_have_count(0)


# Flows 2-4 - create one setting, edit it, delete it again
# One test, because all three flows work on the same single record: creating one per test
# would leave more data in the shared automation account than the extra isolation is worth.


def test_create_edit_and_delete_an_smtp_setting(
    smtp_settings: SmtpSettingsPage, sandbox_smtp: SandboxSmtp, smtp_cleanup: list[str]
) -> None:
    locators = smtp_settings.locators
    username = unique_username(sandbox_smtp)
    settings_before = locators.data_rows.count()

    # Flow 2 - create
    modal = smtp_settings.open_add_modal()
    smtp_settings.fill_form_from(modal, sandbox_smtp, username=username)
    smtp_cleanup.append(username)  # registered before Save, so a later failure still cleans up
    create_response = smtp_settings.save_expecting_create(modal)

    assert create_response.ok, f"Creating the SMTP setting failed: HTTP {create_response.status}"
    # The application shows no success toast; the modal closing and the new row are the indication.
    expect(locators.add_modal).to_have_count(0)
    row = locators.row_for(username)
    expect(row).to_have_count(1)
    expect(locators.row_cell(row, HOST_COLUMN)).to_have_text(sandbox_smtp.host)
    expect(locators.row_cell(row, PORT_COLUMN)).to_have_text(sandbox_smtp.port)
    expect(locators.row_cell(row, USERNAME_COLUMN)).to_have_text(username)
    expect(locators.data_rows).to_have_count(settings_before + 1)
    # The status the application gave the new setting, read from the row rather than assumed.
    status = locators.row_status_badge(row).inner_text().strip()
    logger.info("The created SMTP setting is %s", status)

    # Flow 3 - edit: the Edit modal loads what was saved
    edit_modal = smtp_settings.open_edit_modal(username)
    expect(edit_modal).to_be_visible()
    expect(locators.edit_modal_title).to_be_visible()
    expect(locators.modal_host_input(edit_modal)).to_have_value(sandbox_smtp.host)
    expect(locators.modal_port_input(edit_modal)).to_have_value(sandbox_smtp.port)
    expect(locators.modal_username_input(edit_modal)).to_have_value(username)
    expect(locators.modal_from_email_input(edit_modal)).to_have_value(sandbox_smtp.from_email)
    expect(locators.modal_from_name_input(edit_modal)).to_have_value(sandbox_smtp.from_name)
    expect(locators.modal_encryption_select(edit_modal)).to_have_value(sandbox_smtp.encryption)
    # The password is deliberately not returned by the application ("leave blank to keep"), so
    # the stored value is never verified - only that nothing was pre-filled to be re-sent.
    expect(locators.modal_password_input(edit_modal)).to_have_value("")

    # Change only the two non-sensitive fields; the username stays the clean-up key.
    edited_host = f"edited-{sandbox_smtp.host}"
    edited_from_name = f"{sandbox_smtp.from_name} edited"
    smtp_settings.fill_form(edit_modal, host=edited_host, from_name=edited_from_name)
    update_response = smtp_settings.save_expecting_update(edit_modal)

    assert update_response.ok, f"Updating the SMTP setting failed: HTTP {update_response.status}"
    expect(locators.edit_modal).to_have_count(0)
    # The list shows the changed host, and the setting is still the same single row.
    row = locators.row_for(username)
    expect(row).to_have_count(1)
    expect(locators.row_cell(row, HOST_COLUMN)).to_have_text(edited_host)
    expect(locators.data_rows).to_have_count(settings_before + 1)
    # The change survives a reload, so it was stored and not only rendered.
    smtp_settings.reload_list()
    row = locators.row_for(username)
    expect(locators.row_cell(row, HOST_COLUMN)).to_have_text(edited_host)
    # And the edited From name comes back the next time the modal is opened.
    edit_modal = smtp_settings.open_edit_modal(username)
    expect(locators.modal_from_name_input(edit_modal)).to_have_value(edited_from_name)
    smtp_settings.cancel_modal(edit_modal)

    # Flow 4 - delete only this setting, through its own row and the confirmation
    dialog = smtp_settings.open_delete_dialog(username)
    expect(dialog).to_be_visible()
    expect(locators.delete_dialog_title).to_be_visible()
    # The confirmation names the setting it is about, so it cannot be another row's dialog.
    expect(dialog).to_contain_text(edited_host)
    expect(locators.delete_dialog_cancel_button).to_be_visible()
    delete_response = smtp_settings.confirm_delete()

    assert delete_response.ok, f"Deleting the SMTP setting failed: HTTP {delete_response.status}"
    expect(locators.delete_dialog).to_have_count(0)
    expect(locators.row_for(username)).to_have_count(0)
    # Gone on the server too, and the other settings are untouched.
    smtp_settings.reload_list()
    expect(locators.row_for(username)).to_have_count(0)
    expect(locators.data_rows).to_have_count(settings_before)
