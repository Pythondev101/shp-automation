"""Locators of the SHP Manage Order page, "All Orders" view (``/orders``).

Verified against the live page on 2026-09-15. The filter controls are named by their
labels, the tabs above the filter bar are buttons in a list ("All Orders" first, then one
per channel), and order data is deliberately not part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/orders$")

COLUMN_HEADERS = (
    "S.No",
    "Flag",
    "System Status",
    "Notes",
    "Order ID",
    "Age",
    "Order Date",
    "Order Status",
    "Total Amount",
    "Profit $",
    "Profit %",
    "Buyer Name",
    "Buyer ID",
    "Qty",
    "Part Number",
    "Tracking ID",
)
"""Every column header of the orders table, in the order the page renders them."""


class ManageOrderLocators:
    """Every element the Manage Order tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: "Manage Order" is an accordion button whose nested list holds "All Orders" and one link per channel.
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_button: Locator = sidebar_menu.get_by_role("button", name="Manage Order")
        # ``has`` is resolved inside each list item, so the button is located from the page, not the sidebar.
        menu_item = sidebar_menu.get_by_role("listitem").filter(
            has=page.get_by_role("button", name="Manage Order")
        )
        self.sidebar_submenu: Locator = menu_item.get_by_role("list")
        self.all_orders_link: Locator = self.sidebar_submenu.get_by_role("link", name="All Orders", exact=True)

        # Page header area. Help and Flagged names start with an icon glyph, so they are substring matches.
        self.page_heading: Locator = self._main.get_by_role("heading", name="Manage Order", exact=True)
        self.help_button: Locator = self._main.get_by_role("button", name="Help")
        self.flagged_button: Locator = self._main.get_by_role("button", name="Flagged")

        # Tabs: the list holding the "All Orders" button; every other button in it is a channel tab.
        tab_list = self._main.get_by_role("list").filter(
            has=page.get_by_role("button", name="All Orders", exact=True)
        )
        self.all_orders_tab: Locator = tab_list.get_by_role("button", name="All Orders", exact=True)
        self.channel_tabs: Locator = tab_list.get_by_role("button").filter(
            has_not_text=re.compile(r"^\s*All Orders\s*$")
        )

        # Search / filter section.
        self.system_status_select: Locator = self._main.get_by_role("combobox", name="System Status", exact=True)
        self.order_status_select: Locator = self._main.get_by_role("combobox", name="Order Status", exact=True)
        self.order_date_input: Locator = self._main.get_by_role("textbox", name="By Order Date", exact=True)
        self.creation_date_input: Locator = self._main.get_by_role("textbox", name="By Creation Date", exact=True)
        self.buyer_name_input: Locator = self._main.get_by_role("textbox", name="Buyer Name", exact=True)
        self.buyer_id_input: Locator = self._main.get_by_role("textbox", name="Buyer ID", exact=True)
        self.part_number_input: Locator = self._main.get_by_role("textbox", name="Part#", exact=True)
        self.order_id_input: Locator = self._main.get_by_role("textbox", name="Order ID", exact=True)
        self.search_button: Locator = self._main.get_by_role("button", name="Search", exact=True)
        self.reset_button: Locator = self._main.get_by_role("button", name="Reset", exact=True)

        # Table and its control.
        self.show_entries_select: Locator = self._main.get_by_role("combobox", name="Entries per page", exact=True)
        # Scoped to the table holding an "Order ID" header, so no other table on the page can match.
        # ``has`` is resolved inside each table, so the header is located from the page, not from main.
        self.table: Locator = self._main.get_by_role("table").filter(
            has=page.get_by_role("columnheader", name=re.compile(r"^\W*Order ID(?!\w)"))
        )

    def column_header(self, name: str) -> Locator:
        """Column header ``name``; a sortable header appends a glyph, so only a following word breaks the match."""
        return self._main.get_by_role("columnheader", name=re.compile(rf"^\W*{re.escape(name)}(?!\w)"))
