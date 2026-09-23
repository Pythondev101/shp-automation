"""Page object of the SHP Setup → Import Setting page."""

from __future__ import annotations

import logging

from pathlib import Path

from playwright.sync_api import Locator, Page, Request, Response

from framework.locators.import_setting_locators import (
    COLUMN_HEADERS,
    FILTER_PARAMS,
    ITEM_API_PATH,
    LIST_API_PATH,
    PAGE_URL,
    PARSE_HEADER_API_PATH,
    ImportSettingLocators,
)
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ImportSettingPage(BasePage):
    PATH = "/setup/import"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = ImportSettingLocators(page)
        self.last_list_response: Response | None = None
        """The table request the page answered on load."""
        self._applied_filters: tuple[str, ...] = ()
        """The filters the list currently shows; Search sends no request when they do not change."""
        self.create_requests: list[str] = []
        """Every create request the page has sent, so a test can prove none was sent."""
        page.on("request", self._record_create_request)

    def _record_create_request(self, request: Request) -> None:
        if request.method == "POST" and request.url.split("?")[0].rstrip("/").endswith(LIST_API_PATH):
            self.create_requests.append(request.url)

    def open(self) -> Response | None:
        response = super().open()
        self._applied_filters = ()
        return response

    def open_from_sidebar(self) -> None:
        """Expand "Setup" and open its "Import Setting" link.

        Clicking an expanded entry collapses it again, so it is clicked only while collapsed.
        """
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'Setup' sidebar menu")
        with self.page.expect_response(self._is_list_response) as response:
            self.click(self.locators.import_setting_link, "'Import Setting' Setup sub-menu link")
        self.last_list_response = response.value
        self._applied_filters = ()
        self.page.wait_for_url(PAGE_URL)
        self.dismiss_guide_dialog()

    def dismiss_guide_dialog(self) -> None:
        """Close the onboarding dialog the page opens over itself while no import setting exists.

        Nothing inside the dialog is used; it is closed so the page underneath can be checked.
        """
        if self.locators.guide_dialog.count() and self.locators.guide_dialog.is_visible():
            self.click(self.locators.guide_dialog_close_button, "close (×) of the import-setting guide dialog")
            self.locators.guide_dialog.wait_for(state="hidden")

    @staticmethod
    def _is_list_response(response: Response) -> bool:
        return LIST_API_PATH in response.url and response.request.method == "GET"

    def dismiss_open_modal(self) -> None:
        """Close whatever modal is open, so a failed test cannot block the next action."""
        if self.locators.modal.count() and self.locators.modal.is_visible():
            self.click(self.locators.modal_close_icon.first, "the close (x) of the open modal")
            self.locators.modal.wait_for(state="hidden")

    # Add / Edit Import Setting modal - step 1 (Type & Name)

    def open_add_setup_modal(self) -> None:
        self.click(self.locators.add_setup_button, "'+ Add Setup'")
        self.locators.modal.wait_for()

    def select_file_type(self, label: str) -> None:
        """Choose one of the File Type buttons (CSV / Xls / XLSX), as the page labels them."""
        self.click(self.locators.file_type_button(label), f"the '{label}' File Type button")

    def file_type_labels(self) -> list[str]:
        """The File Type choices the modal offers, read from the live buttons."""
        return [text.strip() for text in self.locators.file_type_buttons.all_inner_texts()]

    def selected_file_type(self) -> str:
        """The File Type button the modal currently has selected ("btn-primary")."""
        buttons = self.locators.file_type_buttons
        for index in range(buttons.count()):
            if "btn-primary" in (buttons.nth(index).get_attribute("class") or ""):
                return buttons.nth(index).inner_text().strip()
        return ""

    def setup_type_options(self) -> list[str]:
        """Every selectable Setup Type label, read from the live dropdown.

        The placeholder option (empty value) is left out; nothing about the list is assumed.
        """
        options = self.locators.modal_type_select.locator("option")
        return [
            options.nth(index).inner_text().strip()
            for index in range(options.count())
            if options.nth(index).get_attribute("value")
        ]

    def fill_step_one(self, *, name: str | None = None, setup_type_label: str | None = None) -> None:
        """Fill the fields that are given; the ones left out keep whatever they hold."""
        if name is not None:
            self.fill(self.locators.modal_name_input, name, "the Add Import Setting Name field")
        if setup_type_label is not None:
            logger.info("Select the '%s' Setup Type", setup_type_label)
            self.locators.modal_type_select.select_option(label=setup_type_label)

    def click_next(self) -> None:
        """Go to step 2 with both required fields filled."""
        self.click(self.locators.modal_next_button, "'Next'")
        self.locators.modal_file_input.wait_for()

    def click_next_expecting_step_one(self) -> None:
        """Click Next with a required field missing and let the page settle.

        The application sends no request in this case, so there is nothing to wait for; waiting
        for the network to go idle keeps the wait bound to the application rather than a sleep.
        """
        self.click(self.locators.modal_next_button, "'Next' (expecting step 1 to stay open)")
        self.page.wait_for_load_state("networkidle")

    # Step 2 (Upload & Map)

    def upload_file(self, path: Path) -> Response:
        """Choose the file and return the header-parse response the application answers with."""
        logger.info("Upload %s", path.name)
        with self.page.expect_response(self._is_parse_header_response) as response:
            self.locators.modal_file_input.set_input_files(path)
        return response.value

    def detected_columns(self) -> list[str]:
        """The file columns the application read out of the uploaded file, in its own order."""
        rows = self.locators.mapping_rows
        return [self.locators.mapping_column_name(index).inner_text().strip() for index in range(rows.count())]

    def mapping_field_labels(self, index: int = 0) -> list[str]:
        """The fields one mapping row offers, read from the live dropdown (placeholder left out)."""
        options = self.locators.mapping_select(index).locator("option")
        return [
            options.nth(position).inner_text().strip()
            for position in range(options.count())
            if options.nth(position).get_attribute("value")
        ]

    def map_columns(self, count: int) -> list[tuple[str, str]]:
        """Link the first ``count`` file columns, each to a field that is still free.

        A field can be used once, so the application disables the ones already taken; the first
        option that is still enabled is chosen. Returns the ``(file column, field)`` pairs made.
        """
        linked = []
        for index in range(count):
            select = self.locators.mapping_select(index)
            option = select.locator("option:not([disabled])").nth(1)  # nth(0) is the placeholder
            value = option.get_attribute("value") or ""
            label = option.inner_text().strip()
            column = self.locators.mapping_column_name(index).inner_text().strip()
            logger.info("Link the file column '%s' with the field '%s'", column, label)
            select.select_option(value)
            linked.append((column, label))
        return linked

    def remap_column(self, index: int) -> tuple[str, str]:
        """Link one already-mapped file column with a different field and return the new pair.

        The fields already taken are disabled by the application, so the first enabled option
        other than the current one is a free field. Used to edit a saved mapping.
        """
        select = self.locators.mapping_select(index)
        current = select.input_value()
        option = select.locator(f"option:not([disabled]):not([value='']):not([value='{current}'])").first
        value = option.get_attribute("value") or ""
        label = option.inner_text().strip()
        column = self.locators.mapping_column_name(index).inner_text().strip()
        logger.info("Re-link the file column '%s' with the field '%s'", column, label)
        select.select_option(value)
        return column, label

    def selected_field(self, index: int) -> str:
        """The field one mapping row currently links to, read from its selected option."""
        select = self.locators.mapping_select(index)
        return select.locator(f"option[value='{select.input_value()}']").inner_text().strip()

    def linked_column_count(self) -> int:
        """How many columns the modal reports as linked, from its "n of m columns linked" badge."""
        return int(self.locators.mapping_count_badge.inner_text().split(" of ")[0].strip())

    def save_expecting_create(self) -> Response:
        with self.page.expect_response(self._is_create_response) as response:
            self.click(self.locators.modal_save_button, "'Save'")
        self.locators.modal.wait_for(state="hidden")
        self.wait_for_table()
        return response.value

    def save_expecting_update(self) -> Response:
        with self.page.expect_response(self._is_update_response) as response:
            self.click(self.locators.modal_save_button, "'Save' in the Edit Import Setting modal")
        self.locators.modal.wait_for(state="hidden")
        return response.value

    def save_expecting_no_create(self) -> None:
        """Click Save with the mapping incomplete; the application sends no create request."""
        self.click(self.locators.modal_save_button, "'Save' (expecting nothing to be created)")
        self.page.wait_for_load_state("networkidle")

    def cancel_modal(self) -> None:
        self.click(self.locators.modal_cancel_button, "'Cancel' in the Import Setting modal")
        self.locators.modal.wait_for(state="hidden")

    def close_modal_with_icon(self) -> None:
        self.click(self.locators.modal_close_icon, "the close (x) of the Import Setting modal")
        self.locators.modal.wait_for(state="hidden")

    def create_setup(
        self,
        name: str,
        *,
        setup_type_label: str | None = None,
        file_type_label: str = "CSV",
        path: Path,
        columns: int = 2,
    ) -> Response:
        """The whole Add Setup flow, from the header button to the create response.

        Without a setup type the first one the live dropdown offers is used; nothing is assumed
        about which types exist.
        """
        self.open_add_setup_modal()
        self.select_file_type(file_type_label)
        self.fill_step_one(name=name, setup_type_label=setup_type_label or self.setup_type_options()[0])
        self.click_next()
        self.upload_file(path)
        self.locators.mapping_rows.first.wait_for()
        self.map_columns(columns)
        return self.save_expecting_create()

    # Row actions

    def open_edit_modal(self, name: str) -> None:
        row = self.locators.row_for(name)
        self.click(self.locators.row_action_button(row, "Edit"), f"the Edit action of the '{name}' row")
        self.locators.modal.wait_for()

    def open_view_modal(self, name: str) -> None:
        row = self.locators.row_for(name)
        self.click(self.locators.row_action_button(row, "View"), f"the View Linking action of '{name}'")
        self.locators.view_modal.wait_for()

    def linked_fields_in_view_modal(self) -> dict[str, str]:
        """The saved linking as the View modal shows it: ``{file column: field}``."""
        rows = self.locators.view_modal_rows
        linking = {}
        for index in range(rows.count()):
            cells = rows.nth(index).locator("td")
            linking[cells.nth(0).inner_text().strip()] = cells.nth(1).inner_text().strip()
        return linking

    def close_view_modal(self) -> None:
        self.click(self.locators.view_modal_close_button, "'Close' in the View Linking modal")
        self.locators.view_modal.wait_for(state="hidden")

    def delete_setup(self, name: str) -> Response:
        """Delete the import setting with this exact name through its row action and confirmation."""
        row = self.locators.row_for(name)
        self.click(self.locators.row_action_button(row, "Delete"), f"the Delete action of '{name}'")
        self.locators.delete_dialog.wait_for()
        with self.page.expect_response(self._is_delete_response) as response:
            self.click(self.locators.delete_dialog_confirm_button, "'Delete' in the confirmation")
        self.locators.delete_dialog.wait_for(state="hidden")
        self.wait_for_table()
        # The rows are re-rendered after the refetch, so the delete is finished only once the
        # row itself is gone - a count read before that still comes from the previous render.
        self.locators.row_for(name).first.wait_for(state="detached")
        return response.value

    # Search / filter

    def search(
        self,
        *,
        name: str | None = None,
        setup_type_label: str | None = None,
        setup_file_label: str | None = None,
        status_label: str | None = None,
    ) -> Response | None:
        """Set the filters that are given, click Search and return the table response.

        ``None`` when the application answered the click with no request of its own, which it
        does while the filters are the ones the list already shows.
        """
        expected: list[str] = []
        if name is not None:
            self.fill(self.locators.name_input, name, "the By Name filter")
            expected.append(f"{FILTER_PARAMS['name']}={name}")
        for select, label, description, key in (
            (self.locators.setup_type_select, setup_type_label, "By Setup Type", "setup_type"),
            (self.locators.setup_files_select, setup_file_label, "By Setup Files", "setup_files"),
            (self.locators.status_select, status_label, "By Status", "status"),
        ):
            if label is not None:
                logger.info("Select '%s' in the %s filter", label, description)
                select.select_option(label=label)
                expected.append(f"{FILTER_PARAMS[key]}={select.input_value()}")

        if tuple(expected) == self._applied_filters:
            # The application sends no request at all when Search is clicked with the filters
            # the list already shows, so there is nothing to wait for - only the table.
            self.click(self.locators.search_button, "'Search' (the filters are unchanged)")
            self.wait_for_table()
            return self.last_list_response

        def is_this_search(response: Response) -> bool:
            # Changing a filter control makes the page refetch unfiltered on its own, so only
            # the response that carries every filter of this search is the one to wait for.
            return self._is_list_response(response) and all(part in response.url for part in expected)

        with self.page.expect_response(is_this_search) as response:
            self.click(self.locators.search_button, "'Search'")
        self.last_list_response = response.value
        self._applied_filters = tuple(expected)
        self.wait_for_table()
        return response.value

    def show_all_entries(self) -> None:
        """Switch "Show entries" to the largest size the page offers.

        The filters are applied to the rows the page has already loaded, not by the server, so
        a record on a later page would not be found by its own name. The size is read from the
        live dropdown, never assumed.
        """
        options = self.locators.show_entries_select.locator("option")
        values = [options.nth(index).get_attribute("value") or "0" for index in range(options.count())]
        largest = max(values, key=int)
        if self.locators.show_entries_select.input_value() == largest:
            return
        logger.info("Show %s entries per page", largest)
        with self.page.expect_response(self._is_list_response) as response:
            self.locators.show_entries_select.select_option(largest)
        self.last_list_response = response.value
        self.wait_for_table()

    def reset(self) -> None:
        """Clear every filter. The page refetches, so the network is waited on, never a sleep."""
        self.click(self.locators.reset_button, "'Reset'")
        self._applied_filters = ()
        self.wait_for_table()

    def column_values(self, column: str) -> list[str]:
        """One column of the whole table, read in a single call so the rows cannot shift in between."""
        return [text.strip() for text in self.locators.column_cells(column).all_inner_texts()]

    def row_values(self, row: Locator) -> dict[str, str]:
        """One row as ``{column header: text}``, read from the live table."""
        cells = row.locator("td")
        return {header: cells.nth(index).inner_text().strip() for index, header in enumerate(COLUMN_HEADERS)}

    def wait_for_search_result(self, name: str) -> None:
        """Wait until the filtered table shows either that row or its no-row cell."""
        self.locators.row_for(name).or_(self.locators.empty_state_cell).first.wait_for()

    def wait_for_table(self) -> None:
        """Wait until the table has re-rendered after a list request.

        The application replaces the rows only after the response has arrived, so a row read
        straight after it can still come from the previous render - or from a moment where the
        body is empty. Waiting for the network to go quiet and for a body row to be there keeps
        every read bound to the application instead of to a sleep.
        """
        self.page.wait_for_load_state("networkidle")
        self.locators.body_rows.first.wait_for()

    @staticmethod
    def _is_parse_header_response(response: Response) -> bool:
        return PARSE_HEADER_API_PATH in response.url and response.request.method == "POST"

    @staticmethod
    def _is_create_response(response: Response) -> bool:
        return response.request.method == "POST" and response.url.split("?")[0].rstrip("/").endswith(
            LIST_API_PATH
        )

    @staticmethod
    def _is_update_response(response: Response) -> bool:
        return response.request.method == "PUT" and ITEM_API_PATH.search(response.url) is not None

    @staticmethod
    def _is_delete_response(response: Response) -> bool:
        return response.request.method == "DELETE" and ITEM_API_PATH.search(response.url) is not None
