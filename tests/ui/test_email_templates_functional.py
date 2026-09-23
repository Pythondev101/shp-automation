"""My Account → Email Templates: required-field validation, creation, filters and delete.

Functional counterpart of ``test_email_templates.py`` (which stays visibility-only). These
tests write application data, so every item carries ``destructive``: exactly **one** template
is created per run, it is named ``AUTO_EMAIL_TEMPLATE_<unique id>`` and the ``template_cleanup``
fixture deletes it again even when an assertion failed. No pre-existing template is ever
touched: every action is addressed through the unique automation name.

Out of scope on purpose: editing a template, sending mail, SMTP settings, the placeholder
buttons, Preview, Channel behaviour, sorting, pagination and every other My Account page.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect

from framework.pages.email_templates_page import EmailTemplatesPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.regression, pytest.mark.functional, pytest.mark.destructive]

NAME_PREFIX = "AUTO_EMAIL_TEMPLATE_"
TEMPLATE_SUBJECT = "Automation test subject"
TEMPLATE_BODY = "<p>Automation test email template</p>"
"""Harmless static HTML; no placeholder and no recipient, so nothing can be sent from it."""


def unique_template_name() -> str:
    """A name no manual template can collide with; 28 characters, under the 30 the field allows."""
    return f"{NAME_PREFIX}{uuid4().hex[:8]}"


@pytest.fixture
def email_templates(authenticated_page: Page) -> EmailTemplatesPage:
    """The Email Templates page, opened through the signed-in sidebar."""
    page = EmailTemplatesPage(authenticated_page)
    page.open_from_sidebar()
    return page


@pytest.fixture
def template_cleanup(email_templates: EmailTemplatesPage) -> Iterator[list[str]]:
    """Names this test creates; each one is deleted afterwards, whatever the test did.

    Append a name **before** clicking Save, so a template created by a step that then failed is
    still cleaned up. Only these names are ever deleted. A name that survives the clean-up is
    reported by failing the teardown, which is added to - never replaces - the test failure.
    """
    created: list[str] = []
    yield created

    leftovers: list[str] = []
    for name in created:
        try:
            email_templates.open()
            email_templates.locators.search_button.wait_for()
            email_templates.search(name=name)
            if email_templates.locators.row_for(name).count() == 0:
                continue
            logger.info("Clean-up: delete the automation template %s", name)
            email_templates.delete_template(name)
            email_templates.search(name=name)
            if email_templates.locators.row_for(name).count() != 0:
                leftovers.append(name)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            leftovers.append(f"{name} ({exc.__class__.__name__}: {exc})")
    assert not leftovers, (
        f"{len(leftovers)} automation template(s) left behind and must be deleted by hand: "
        + ", ".join(leftovers)
    )


# Flow 1 - Add Template modal and required-field validation


def test_add_template_modal_opens_with_its_fields(email_templates: EmailTemplatesPage) -> None:
    locators = email_templates.locators
    email_templates.open_add_template_modal()

    expect(locators.add_template_modal).to_be_visible()
    expect(locators.add_template_modal_title).to_be_visible()
    expect(locators.modal_name_input).to_be_visible()
    expect(locators.modal_subject_input).to_be_visible()
    expect(locators.modal_body_input).to_be_visible()
    expect(locators.modal_channel_store_id_input).to_be_visible()
    expect(locators.modal_save_button).to_be_visible()
    expect(locators.modal_cancel_button).to_be_visible()

    email_templates.cancel_add_template_modal()
    expect(locators.add_template_modal).to_have_count(0)


@pytest.mark.parametrize(
    ("fill_name", "fill_subject"),
    [
        pytest.param(False, False, id="nothing-filled"),
        pytest.param(True, False, id="name-only"),
        pytest.param(True, True, id="name-and-subject"),
    ],
)
def test_save_creates_nothing_until_every_required_field_is_filled(
    email_templates: EmailTemplatesPage,
    template_cleanup: list[str],
    fill_name: bool,
    fill_subject: bool,
) -> None:
    """Name, Subject and Body (HTML) are all required: Save with any of them empty creates nothing.

    The Body is never filled here, so none of the combinations below is complete. The name is
    registered for clean-up first, so a template the application creates in spite of the missing
    Body (which would fail this test) is still removed afterwards.
    """
    locators = email_templates.locators
    name = unique_template_name()
    template_cleanup.append(name)

    email_templates.open_add_template_modal()
    email_templates.fill_add_template_form(
        name=name if fill_name else None,
        subject=TEMPLATE_SUBJECT if fill_subject else None,
    )

    email_templates.save_expecting_no_create()

    # The application sends no create request at all, so nothing can have been created.
    assert email_templates.create_requests == [], (
        "Save sent a create request although a required field was empty: "
        f"{email_templates.create_requests}"
    )
    # The modal stays open with what was typed still in it, and the page is still alive.
    expect(locators.add_template_modal).to_be_visible()
    expect(locators.modal_save_button).to_be_enabled()
    expect(locators.modal_name_input).to_have_value(name if fill_name else "")
    expect(locators.modal_subject_input).to_have_value(TEMPLATE_SUBJECT if fill_subject else "")
    expect(locators.modal_body_input).to_have_value("")

    # And the table holds no such template.
    email_templates.cancel_add_template_modal()
    email_templates.search(name=name)
    expect(locators.row_for(name)).to_have_count(0)
    expect(locators.data_rows).to_have_count(0)
    expect(locators.no_results_message).to_be_visible()


# Flows 2-4 - create one template, filter for it, delete it again
# One test, because all three flows work on the same single template: creating one per test
# would leave more data in the shared account than the extra isolation is worth.


def test_create_filter_and_delete_an_email_template(
    email_templates: EmailTemplatesPage, template_cleanup: list[str]
) -> None:
    locators = email_templates.locators
    name = unique_template_name()

    # Flow 2 - create
    email_templates.open_add_template_modal()
    email_templates.fill_add_template_form(name=name, subject=TEMPLATE_SUBJECT, body=TEMPLATE_BODY)
    template_cleanup.append(name)  # registered before Save, so a later failure still cleans up
    create_response = email_templates.save_expecting_create()

    assert create_response.ok, f"Creating the template failed: HTTP {create_response.status}"
    # The application shows no success toast; the modal closing and the new row are the indication.
    expect(locators.add_template_modal).to_have_count(0)
    row = locators.row_for(name)
    expect(row).to_have_count(1)
    expect(row).to_contain_text(TEMPLATE_SUBJECT)

    # The status the application gave the new template, read from the row rather than assumed.
    status = locators.row_status_badge(row).inner_text().strip()
    other_status = "Inactive" if status == "Active" else "Active"
    logger.info("The created template is %s", status)

    # Flow 3.1 - search by name
    email_templates.search(name=name)
    expect(locators.data_rows).to_have_count(1)
    expect(locators.row_for(name)).to_be_visible()

    # Flow 3.2 - status filter alone: every returned row must carry the selected status
    email_templates.reset()
    email_templates.search(status_label=status)
    expect(locators.row_for(name)).to_have_count(1)
    returned = locators.data_rows.count()
    assert returned > 0, f"The {status} filter returned no row although the created one is {status}"
    for index in range(returned):
        expect(locators.row_status_badge(locators.data_rows.nth(index))).to_have_text(status)

    # Flow 3.3 - combined filter: the unique name with its own status, then with the other one
    email_templates.search(name=name, status_label=status)
    expect(locators.data_rows).to_have_count(1)
    expect(locators.row_for(name)).to_be_visible()
    expect(locators.row_status_badge(locators.row_for(name))).to_have_text(status)

    email_templates.search(status_label=other_status)
    expect(locators.row_for(name)).to_have_count(0)
    expect(locators.data_rows).to_have_count(0)
    expect(locators.no_results_message).to_be_visible()

    # Flow 3.4 - Reset clears both filters and restores the unfiltered list
    email_templates.reset()
    expect(locators.name_input).to_have_value("")
    expect(locators.status_select).to_have_value("")
    expect(locators.row_for(name)).to_be_visible()
    assert locators.data_rows.count() > 0, "Reset left the table without any row"

    # Flow 4 - delete only this template, through its own row
    delete_response = email_templates.delete_template(name)
    assert delete_response.ok, f"Deleting the template failed: HTTP {delete_response.status}"
    expect(locators.delete_dialog).to_have_count(0)

    email_templates.search(name=name)
    expect(locators.row_for(name)).to_have_count(0)
    expect(locators.data_rows).to_have_count(0)
    expect(locators.no_results_message).to_be_visible()
