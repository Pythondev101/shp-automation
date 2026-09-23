"""Setup → Import Setting: the complete Add Setup workflow, filters, edit and delete.

Functional counterpart of ``test_import_setting.py`` (which stays visibility-only). These
tests write application data, so every item carries ``destructive``: each one creates its own
import settings, named ``AUTO_IMP_<what>_<unique id>``, and the ``setup_cleanup`` fixture
deletes them again even when an assertion failed. No pre-existing import setting is ever
opened, edited or deleted: every action is addressed through the unique automation name.

Nothing here is hardcoded from the application: the Setup Type options, the File Type
choices, the mapping fields, the detected file columns, the row's status and the row counts
are all read from the live UI. The three upload files in ``test_data/`` carry the same
logical data in CSV, XLS and XLSX.

Out of scope on purpose: Help & sample files, Read the guide first, Download sample file,
the status badge toggle, pagination, sorting, Show entries and every other Setup page.
"""

from __future__ import annotations

import csv
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect

from framework.config import PROJECT_ROOT
from framework.locators.import_setting_locators import STEP_ONE_BADGE, STEP_TWO_BADGE
from framework.pages.import_setting_page import ImportSettingPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.regression, pytest.mark.functional, pytest.mark.destructive]

TEST_DATA_DIR = PROJECT_ROOT / "test_data"
UPLOAD_FILES = {
    # format key -> (File Type button as the modal labels it, the prepared upload file)
    "csv": ("CSV", TEST_DATA_DIR / "import_setting_sample.csv"),
    "xls": ("Xls", TEST_DATA_DIR / "import_setting_sample.xls"),
    "xlsx": ("XLSX", TEST_DATA_DIR / "import_setting_sample.xlsx"),
}
"""The same sample rows in the three formats the application offers."""

NAME_PREFIX = "AUTO_IMP_"
"""Automation-owned names only; the Name field allows 30 characters."""


def sample_columns() -> list[str]:
    """The header row of the sample file - what the application must detect after the upload."""
    with UPLOAD_FILES["csv"][1].open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def unique_name(what: str) -> str:
    """A name no manual import setting can collide with, within the field's 30 characters.

    Upper case throughout: the Name column is rendered with ``text-transform: capitalize``.
    """
    return f"{NAME_PREFIX}{what.upper()}_{uuid4().hex[:8].upper()}"[:30]


@pytest.fixture
def import_setting(authenticated_page: Page) -> ImportSettingPage:
    """The Import Setting page, opened through the signed-in sidebar, showing the whole list.

    The filters work on the rows the page has loaded, so the largest page size is chosen first;
    otherwise a record on a later page could not be found by its own name.
    """
    page = ImportSettingPage(authenticated_page)
    page.open_from_sidebar()
    page.show_all_entries()
    return page


@pytest.fixture
def setup_cleanup(import_setting: ImportSettingPage) -> Iterator[list[str]]:
    """Names this test creates; each one is deleted afterwards, whatever the test did.

    Append a name **before** clicking Save, so a setup created by a step that then failed is
    still cleaned up. Only these names are ever deleted. A name that survives the clean-up is
    reported by failing the teardown, which is added to - never replaces - the test failure.
    """
    created: list[str] = []
    yield created

    leftovers: list[str] = []
    for name in created:
        try:
            # A reload also closes a modal a failed test left open.
            import_setting.open()
            import_setting.locators.search_button.wait_for()
            import_setting.dismiss_guide_dialog()
            import_setting.dismiss_open_modal()
            import_setting.show_all_entries()
            import_setting.search(name=name)
            import_setting.wait_for_search_result(name)
            if import_setting.locators.row_for(name).count() == 0:
                continue
            logger.info("Clean-up: delete the automation import setting %s", name)
            import_setting.delete_setup(name)
            import_setting.search(name=name)
            # Auto-retrying, so the check cannot read the table between two renders.
            expect(import_setting.locators.row_for(name)).to_have_count(0)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            leftovers.append(f"{name} ({exc.__class__.__name__}: {exc})")
    assert not leftovers, (
        f"{len(leftovers)} automation import setting(s) left behind and must be deleted by hand: "
        + ", ".join(leftovers)
    )


# Flow 1 - the Add Setup modal


def test_add_setup_modal_opens_with_its_step_one_fields(import_setting: ImportSettingPage) -> None:
    """+ Add Setup opens "Add Import Setting" on step 1 with every field the screenshot shows."""
    locators = import_setting.locators
    import_setting.open_add_setup_modal()

    expect(locators.modal).to_be_visible()
    expect(locators.modal_title).to_have_text("Add Import Setting")
    # Both step indicators are shown; step 1 is the current one ("bg-primary").
    expect(locators.step_badge(STEP_ONE_BADGE)).to_be_visible()
    expect(locators.step_badge(STEP_TWO_BADGE)).to_be_visible()
    expect(locators.step_badge(STEP_ONE_BADGE)).to_have_class(re.compile(r"bg-primary"))

    expect(locators.file_type_label).to_be_visible()
    for label, _path in UPLOAD_FILES.values():
        expect(locators.file_type_button(label)).to_be_visible()
    expect(locators.modal_name_label).to_be_visible()
    expect(locators.modal_name_input).to_be_visible()
    expect(locators.modal_type_label).to_be_visible()
    expect(locators.modal_type_select).to_be_visible()
    expect(locators.modal_cancel_button).to_be_visible()
    expect(locators.modal_next_button).to_be_visible()
    expect(locators.modal_close_icon).to_be_visible()
    # Name and Select Type are the two the application marks as required.
    expect(locators.required_marker("Name")).to_be_visible()
    expect(locators.required_marker("Select Type")).to_be_visible()

    import_setting.close_modal_with_icon()
    expect(locators.modal).to_have_count(0)


def test_file_type_choices_match_the_prepared_upload_files(import_setting: ImportSettingPage) -> None:
    """The three formats the modal offers are the three the test data covers, and CSV is preselected."""
    import_setting.open_add_setup_modal()

    offered = import_setting.file_type_labels()
    assert offered == [label for label, _path in UPLOAD_FILES.values()], (
        f"The modal offers {offered}; the prepared upload files cover "
        f"{[label for label, _path in UPLOAD_FILES.values()]}"
    )
    assert import_setting.selected_file_type() == "CSV", "CSV is no longer the preselected File Type"

    # Each button can be chosen, and the Upload & Map step names the chosen format.
    for label, _path in UPLOAD_FILES.values():
        import_setting.select_file_type(label)
        assert import_setting.selected_file_type() == label, f"The '{label}' button did not become the selected one"

    import_setting.cancel_modal()
    expect(import_setting.locators.modal).to_have_count(0)


# Flow 2 - mandatory field validation


@pytest.mark.parametrize(
    ("fill_name", "fill_type"),
    [
        pytest.param(False, False, id="name-empty-type-empty"),
        pytest.param(True, False, id="name-filled-type-empty"),
        pytest.param(False, True, id="type-selected-name-empty"),
    ],
)
def test_next_keeps_step_one_open_until_name_and_type_are_filled(
    import_setting: ImportSettingPage,
    setup_cleanup: list[str],
    fill_name: bool,
    fill_type: bool,
) -> None:
    """Name and Select Type are both required: Next with either one empty cannot reach step 2.

    The application renders no error text for this - it marks both fields with a red asterisk
    and simply refuses to advance - so the invalid state checked here is the application's own:
    the step indicator stays on step 1, step 2's upload field never appears, the empty required
    field is still empty, and no import setting is created.
    """
    locators = import_setting.locators
    name = unique_name("VAL")
    setup_cleanup.append(name)  # registered first, so a setup created in spite of this still goes

    import_setting.open_add_setup_modal()
    first_type = import_setting.setup_type_options()[0]
    import_setting.fill_step_one(
        name=name if fill_name else None,
        setup_type_label=first_type if fill_type else None,
    )

    import_setting.click_next_expecting_step_one()

    # Step 1 is still the current step and step 2 never opened.
    expect(locators.modal_title).to_have_text("Add Import Setting")
    expect(locators.modal_next_button).to_be_visible()
    expect(locators.modal_file_input).to_have_count(0)
    expect(locators.mapping_rows).to_have_count(0)
    # The required fields are still marked, and the empty one is still empty.
    expect(locators.required_marker("Name")).to_be_visible()
    expect(locators.required_marker("Select Type")).to_be_visible()
    expect(locators.modal_name_input).to_have_value(name if fill_name else "")
    if not fill_type:
        expect(locators.modal_type_select).to_have_value("")
    # Nothing was sent, so nothing can have been created.
    assert import_setting.create_requests == [], (
        f"Next sent a create request although a required field was empty: {import_setting.create_requests}"
    )

    import_setting.cancel_modal()
    import_setting.search(name=name)
    expect(locators.row_for(name)).to_have_count(0)
    expect(locators.data_rows).to_have_count(0)


def test_save_creates_nothing_until_at_least_one_column_is_mapped(
    import_setting: ImportSettingPage, setup_cleanup: list[str]
) -> None:
    """Step 2 needs a column link: Save with the mapping untouched creates no import setting."""
    locators = import_setting.locators
    name = unique_name("NOMAP")
    setup_cleanup.append(name)

    import_setting.open_add_setup_modal()
    import_setting.fill_step_one(name=name, setup_type_label=import_setting.setup_type_options()[0])
    import_setting.click_next()
    response = import_setting.upload_file(UPLOAD_FILES["csv"][1])
    assert response.ok, f"The header parse failed: HTTP {response.status}"
    locators.mapping_rows.first.wait_for()
    assert import_setting.linked_column_count() == 0, "The upload pre-linked columns on its own"

    import_setting.save_expecting_no_create()

    assert import_setting.create_requests == [], (
        f"Save sent a create request although no column was linked: {import_setting.create_requests}"
    )
    expect(locators.modal).to_be_visible()
    expect(locators.step_badge(STEP_TWO_BADGE)).to_be_visible()

    import_setting.cancel_modal()
    import_setting.search(name=name)
    expect(locators.row_for(name)).to_have_count(0)
    expect(locators.no_results_message).to_be_visible()


# Flow 3 - Upload & Map, per file format


@pytest.mark.parametrize("file_format", ["csv", "xlsx"])
def test_create_import_setting_from_an_uploaded_file(
    import_setting: ImportSettingPage, setup_cleanup: list[str], file_format: str
) -> None:
    """The whole Add Setup flow for one upload format, from step 1 to the row in the list.

    ``xls`` is not covered here: the application cannot read a legacy ``.xls`` header at all,
    which ``test_xls_header_is_not_read_by_the_application`` pins.
    """
    locators = import_setting.locators
    file_type_label, path = UPLOAD_FILES[file_format]
    name = unique_name(file_format)

    # Step 1
    import_setting.open_add_setup_modal()
    import_setting.select_file_type(file_type_label)
    setup_type = import_setting.setup_type_options()[0]
    import_setting.fill_step_one(name=name, setup_type_label=setup_type)
    import_setting.click_next()

    # Step 2 opened and names the chosen format
    expect(locators.step_badge(STEP_TWO_BADGE)).to_be_visible()
    expect(locators.modal_file_input).to_be_visible()
    expect(locators.modal_upload_label).to_contain_text(file_type_label.upper())

    # The file is accepted and its columns are detected
    setup_cleanup.append(name)  # from here on a save could succeed, so register before it
    response = import_setting.upload_file(path)
    assert response.ok, f"The header parse failed: HTTP {response.status}"
    locators.mapping_rows.first.wait_for()
    assert import_setting.detected_columns() == sample_columns(), (
        "The application detected other columns than the sample file's header row"
    )
    expect(locators.mapping_count_badge).to_contain_text(f"0 of {len(sample_columns())} columns linked")

    # Map with the fields the application itself offers for this setup type
    linked = import_setting.map_columns(2)
    assert import_setting.linked_column_count() == len(linked)

    create_response = import_setting.save_expecting_create()
    assert create_response.ok, f"Creating the import setting failed: HTTP {create_response.status}"
    expect(locators.modal).to_have_count(0)

    # The new import setting is in the list, with the type and format it was created with
    row = locators.row_for(name)
    expect(row).to_have_count(1)
    values = import_setting.row_values(row)
    assert values["Setup Type"] == setup_type, f"The row shows the type {values['Setup Type']}"
    assert values["Setup Files"].casefold() == file_format, f"The row shows the file {values['Setup Files']}"

    # And the saved linking is the one that was made
    import_setting.open_view_modal(name)
    assert import_setting.linked_fields_in_view_modal() == dict(linked)
    import_setting.close_view_modal()


def test_xls_header_is_not_read_by_the_application(
    import_setting: ImportSettingPage, setup_cleanup: list[str]
) -> None:
    """XLS is offered as a File Type, but the application cannot parse a legacy .xls header.

    Pinned as it behaves today: the upload is answered with ``status: false`` and a message of
    its own, no column is detected, and no import setting can be created from it. The test
    fails - on purpose - as soon as the application starts reading .xls files, so the XLS flow
    can be completed then.
    """
    locators = import_setting.locators
    file_type_label, path = UPLOAD_FILES["xls"]
    name = unique_name("xls")
    setup_cleanup.append(name)

    import_setting.open_add_setup_modal()
    import_setting.select_file_type(file_type_label)
    import_setting.fill_step_one(name=name, setup_type_label=import_setting.setup_type_options()[0])
    import_setting.click_next()
    expect(locators.modal_upload_label).to_contain_text("XLS")

    response = import_setting.upload_file(path)
    payload = response.json()
    logger.warning("The application refused the .xls upload: %s", payload.get("message"))
    assert payload.get("status") is False, f"The application now reads .xls files: {payload}"
    assert payload.get("message"), "The application refused the .xls upload without a message"
    expect(locators.mapping_rows).to_have_count(0)

    import_setting.cancel_modal()
    import_setting.search(name=name)
    expect(locators.row_for(name)).to_have_count(0)


# Flow 4 - every Setup Type the dropdown offers


def test_every_setup_type_can_be_created_with_its_own_mapping_fields(
    import_setting: ImportSettingPage, setup_cleanup: list[str]
) -> None:
    """Each Setup Type the live dropdown offers is created once, mapped with its own fields.

    The types are read from the dropdown, never hardcoded, and each one brings its own list of
    fields in the "Link With Column" dropdowns - which is what is checked per type.
    """
    locators = import_setting.locators
    _file_type_label, path = UPLOAD_FILES["csv"]

    import_setting.open_add_setup_modal()
    setup_types = import_setting.setup_type_options()
    import_setting.cancel_modal()
    assert setup_types, "The Select Type dropdown offers no setup type"
    logger.info("Setup Types offered: %s", setup_types)

    fields_per_type: dict[str, list[str]] = {}
    for index, setup_type in enumerate(setup_types):
        name = unique_name(f"T{index}")
        import_setting.open_add_setup_modal()
        import_setting.fill_step_one(name=name, setup_type_label=setup_type)
        import_setting.click_next()
        setup_cleanup.append(name)
        response = import_setting.upload_file(path)
        assert response.ok, f"The header parse failed for {setup_type}: HTTP {response.status}"
        locators.mapping_rows.first.wait_for()
        assert import_setting.detected_columns() == sample_columns()

        fields = import_setting.mapping_field_labels()
        assert fields, f"The '{setup_type}' setup type offers no field to link with"
        fields_per_type[setup_type] = fields

        linked = import_setting.map_columns(2)
        assert {field for _column, field in linked} <= set(fields)
        create_response = import_setting.save_expecting_create()
        assert create_response.ok, f"Creating the '{setup_type}' import setting failed: {create_response.status}"

        row = locators.row_for(name)
        expect(row).to_have_count(1)
        assert import_setting.row_values(row)["Setup Type"] == setup_type

    # The types are genuinely different mappings, not one shared field list.
    distinct = {tuple(fields) for fields in fields_per_type.values()}
    assert len(distinct) == len(fields_per_type), (
        f"Two setup types offer the same mapping fields: { {k: v[:3] for k, v in fields_per_type.items()} }"
    )


# Flow 5 - search / filter / reset


def test_search_filters_and_reset(import_setting: ImportSettingPage, setup_cleanup: list[str]) -> None:
    """By Name, By Setup Type, By Setup Files, By Status, the four combined, and Reset."""
    locators = import_setting.locators
    file_type_label, path = UPLOAD_FILES["csv"]
    name = unique_name("FILTER")

    setup_cleanup.append(name)
    import_setting.create_setup(name, file_type_label=file_type_label, path=path)

    row = locators.row_for(name)
    expect(row).to_have_count(1)
    values = import_setting.row_values(row)
    status = values["Status"]  # whichever status the application gave the new setup
    setup_file = values["Setup Files"]
    logger.info("The created import setting is %s / %s / %s", values["Setup Type"], setup_file, status)

    # By Name - the unique automation name returns exactly its own record
    import_setting.search(name=name)
    expect(locators.data_rows).to_have_count(1)
    expect(locators.row_for(name)).to_be_visible()

    # By Setup Type - every returned row carries the selected type
    import_setting.reset()
    import_setting.search(setup_type_label=values["Setup Type"])
    expect(locators.row_for(name)).to_have_count(1)
    _every_row_shows(import_setting, "Setup Type", values["Setup Type"])

    # By Setup Files
    import_setting.reset()
    import_setting.search(setup_file_label=setup_file)
    expect(locators.row_for(name)).to_have_count(1)
    _every_row_shows(import_setting, "Setup Files", setup_file)

    # By Status - read from the created row, not assumed
    import_setting.reset()
    import_setting.search(status_label=status)
    expect(locators.row_for(name)).to_have_count(1)
    _every_row_shows(import_setting, "Status", status)

    # All four together, with the values of the created record
    import_setting.reset()
    import_setting.search(
        name=name,
        setup_type_label=values["Setup Type"],
        setup_file_label=setup_file,
        status_label=status,
    )
    expect(locators.data_rows).to_have_count(1)
    expect(locators.row_for(name)).to_be_visible()

    # Reset clears every filter and restores the unfiltered list
    import_setting.reset()
    expect(locators.name_input).to_have_value("")
    expect(locators.setup_type_select).to_have_value("")
    expect(locators.setup_files_select).to_have_value("")
    expect(locators.status_select).to_have_value("")
    expect(locators.row_for(name)).to_be_visible()
    assert locators.data_rows.count() > 0, "Reset left the table without any row"


def _every_row_shows(import_setting: ImportSettingPage, column: str, value: str) -> None:
    """Every row the filter returned carries this value in this column; the count is never assumed."""
    returned = import_setting.column_values(column)
    assert returned, f"The {column} filter returned no row although the created one is '{value}'"
    assert set(returned) == {value}, f"The {column} filter returned rows showing {sorted(set(returned))}"


# Flow 6 - edit


def test_edit_updates_the_saved_column_mapping(
    import_setting: ImportSettingPage, setup_cleanup: list[str]
) -> None:
    """Edit opens on Upload & Map with the saved mapping loaded; a changed link is saved.

    The Edit modal holds no Name or Setup Type field - the application only lets the column
    mapping be edited - so the safe editable field here is one column's linked field.
    """
    locators = import_setting.locators
    file_type_label, path = UPLOAD_FILES["csv"]
    name = unique_name("EDIT")

    # Create the record this test edits, and keep the mapping it was created with
    setup_cleanup.append(name)
    import_setting.open_add_setup_modal()
    import_setting.select_file_type(file_type_label)
    import_setting.fill_step_one(name=name, setup_type_label=import_setting.setup_type_options()[0])
    import_setting.click_next()
    import_setting.upload_file(path)
    locators.mapping_rows.first.wait_for()
    saved = dict(import_setting.map_columns(2))
    assert import_setting.save_expecting_create().ok

    # The edit form opens on Upload & Map with the current values loaded
    import_setting.open_edit_modal(name)
    expect(locators.modal_title).to_have_text("Edit Import Setting")
    expect(locators.step_badge(STEP_TWO_BADGE)).to_be_visible()
    expect(locators.mapping_rows).to_have_count(len(saved))
    assert import_setting.detected_columns() == list(saved)
    assert import_setting.linked_column_count() == len(saved)
    for index, field in enumerate(saved.values()):
        assert import_setting.selected_field(index) == field, "The saved mapping was not loaded into the edit form"

    # Change one link, save, and check the update was accepted
    column, new_field = import_setting.remap_column(0)
    update_response = import_setting.save_expecting_update()
    assert update_response.ok, f"Saving the edit failed: HTTP {update_response.status}"
    expect(locators.modal).to_have_count(0)

    # The edited record is still found by its name. The application does not refetch the list
    # after an update, so the search is also what brings the saved mapping back into the page.
    import_setting.search(name=name)
    expect(locators.data_rows).to_have_count(1)
    expect(locators.row_for(name)).to_be_visible()

    # The updated link is the one the list shows now
    expected = {**saved, column: new_field}
    import_setting.open_view_modal(name)
    assert import_setting.linked_fields_in_view_modal() == expected
    import_setting.close_view_modal()

    import_setting.open_edit_modal(name)
    assert import_setting.selected_field(0) == new_field, "The edited link was not the one that was loaded back"
    import_setting.cancel_modal()


def _row_names(import_setting: ImportSettingPage) -> set[str]:
    """The names the table currently lists; nothing is assumed about how many there are."""
    return set(import_setting.column_values("Name"))


# Flow 7 - delete


def test_delete_removes_the_automation_import_setting(
    import_setting: ImportSettingPage, setup_cleanup: list[str]
) -> None:
    """Delete asks for confirmation, removes only the automation record, and it stays gone."""
    locators = import_setting.locators
    file_type_label, path = UPLOAD_FILES["csv"]
    name = unique_name("DEL")

    setup_cleanup.append(name)
    import_setting.create_setup(name, file_type_label=file_type_label, path=path)
    expect(locators.row_for(name)).to_have_count(1)
    before = _row_names(import_setting)

    delete_response = import_setting.delete_setup(name)
    assert delete_response.ok, f"Deleting the import setting failed: HTTP {delete_response.status}"
    expect(locators.delete_dialog).to_have_count(0)

    # Only that one row went. The list is paginated, so a row from the next page can move up:
    # the check is that every other name is still there, never a row count.
    expect(locators.row_for(name)).to_have_count(0)
    survivors = _row_names(import_setting)
    assert name not in survivors
    missing = (before - {name}) - survivors
    assert not missing, f"Delete also removed import setting(s) it must not touch: {sorted(missing)}"

    # And it is not found by its own name any more
    import_setting.search(name=name)
    expect(locators.row_for(name)).to_have_count(0)
    expect(locators.data_rows).to_have_count(0)
