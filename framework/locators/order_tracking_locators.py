"""Locators of the SHP Order Logs → Order Tracking page (``/order-logs/tracking``).

The page shares the Order Processing layout (filters, table, empty state), so only what
differs is defined here: the sub-menu link, the heading and the extra "Tracking #" column.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

from framework.locators.order_processing_locators import OrderProcessingLocators

PAGE_URL = re.compile(r"/order-logs/tracking$")
LIST_API_PATH = "/api/v1/order-logs/tracking"
"""The request Search, Reset and the first load send for the table rows."""

COLUMN_HEADERS = (
    "S.No",
    "Status",
    "Order ID",
    "Order Status",
    "Total",
    "Buyer",
    "Qty",
    "Part #",
    "Tracking #",
    "Order Date",
)
"""Every column header of the table, in the order the page renders them."""


class OrderTrackingLocators(OrderProcessingLocators):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.order_tracking_link: Locator = self.sidebar_submenu.get_by_role("link", name="Order Tracking", exact=True)
        self.page_heading: Locator = self._main.get_by_role("heading", name="Order Tracking Logs", exact=True)

    def column_cells(self, header: str) -> Locator:
        return self.data_rows.locator(f"td:nth-child({COLUMN_HEADERS.index(header) + 1})")
