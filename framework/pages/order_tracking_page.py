"""Page object of the SHP Order Logs → Order Tracking page; filters and Search/Reset come from Order Processing."""

from __future__ import annotations

from playwright.sync_api import Page, Response

from framework.locators.order_tracking_locators import LIST_API_PATH, PAGE_URL, OrderTrackingLocators
from framework.pages.order_processing_page import OrderProcessingPage


class OrderTrackingPage(OrderProcessingPage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = OrderTrackingLocators(page)

    def open_from_sidebar(self) -> None:
        """Expand "Order Logs" (only while collapsed) and open its "Order Tracking" link."""
        self.locators.sidebar_menu_button.wait_for()
        if not self.locators.sidebar_submenu.is_visible():
            self.click(self.locators.sidebar_menu_button, "'Order Logs' sidebar menu")
        self._open_link(self.locators.order_tracking_link, "'Order Tracking' Order Logs sub-menu link")
        self.page.wait_for_url(PAGE_URL)

    @staticmethod
    def _is_list_response(response: Response) -> bool:
        return LIST_API_PATH in response.url and response.request.method == "GET"
