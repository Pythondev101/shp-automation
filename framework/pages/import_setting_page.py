"""Page object of the SHP Setup → Import Setting page."""

from __future__ import annotations

import logging

from playwright.sync_api import Page, Response

from framework.locators.import_setting_locators import LIST_API_PATH, PAGE_URL, ImportSettingLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ImportSettingPage(BasePage):
    PATH = "/setup/import"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = ImportSettingLocators(page)
        self.last_list_response: Response | None = None
        """The table request the page answered on load."""

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
