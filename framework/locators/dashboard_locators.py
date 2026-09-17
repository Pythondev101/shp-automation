"""Locators of the SHP dashboard (``/dashboard``).

Verified against the live DOM on 2026-09-11. The page has no ``data-testid``
attributes; elements are located by accessible role and name inside the page's
landmarks (sidebar, header banner, main content). Dashboard sections have no
landmark of their own, so each is identified by its heading. Values shown on the
page (counts, earnings, chart data) are dynamic and deliberately not part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page


class DashboardLocators:
    """Every element the dashboard tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        sidebar = page.get_by_role("complementary")
        header = page.get_by_role("banner")
        main = page.get_by_role("main")

        # Sidebar: branding and menu. Menu names start with an icon glyph, and entries with
        # a sub-menu are buttons rather than links, so names are matched as substrings.
        self.brand_logo: Locator = sidebar.get_by_role("img", name="SellerHub Pro", exact=True)
        self.brand_name: Locator = sidebar.get_by_text("SellerHub Pro", exact=True)
        menu = sidebar.get_by_role("navigation")
        self.dashboard_menu: Locator = menu.get_by_role("link", name="Dashboard")
        self.active_listing_menu: Locator = menu.get_by_role("button", name="Active Listing")
        self.manage_order_menu: Locator = menu.get_by_role("button", name="Manage Order")
        self.manage_channel_menu: Locator = menu.get_by_role("link", name="Manage Channel")
        self.my_account_menu: Locator = menu.get_by_role("button", name="My Account")
        self.help_center_menu: Locator = menu.get_by_role("link", name="Help Center")
        self.training_videos_menu: Locator = menu.get_by_role("link", name="Training videos")
        self.upgrade_plan_menu: Locator = menu.get_by_role("link", name="Upgrade Plan")
        self.customer_menu: Locator = menu.get_by_role("link", name="Customer")

        # Header.
        self.search_input: Locator = header.get_by_role(
            "textbox", name="Search by SKU, Part Number, Title or Order ID", exact=True
        )
        self.notifications_button: Locator = header.get_by_role("button", name="Notifications", exact=True)
        # The profile button is named after the signed-in account; it is the only header
        # button with a title attribute, which keeps the locator account-independent.
        self.profile_button: Locator = header.locator("button[title]")
        # Entry of the profile button's dropdown (verified 2026-09-16); its name starts with an icon glyph.
        self.sign_out_button: Locator = header.get_by_role("button", name="Sign out")

        # Main content.
        self.welcome_heading: Locator = main.get_by_role("heading", name="Welcome Seller", exact=True)
        # The cards are links whose names include the current count, e.g. "Active Orders 0".
        self.active_orders_card: Locator = main.get_by_role("link", name="Active Orders")
        self.today_order_card: Locator = main.get_by_role("link", name="Today Order")
        self.this_month_earnings_label: Locator = main.get_by_text("This Month Earnings", exact=True)
        self.orders_chart_heading: Locator = main.get_by_role("heading", name="Orders", exact=True)
        # ApexCharts names the chart after its type and series, e.g. "line chart with 3 data series: ...".
        self.orders_chart: Locator = main.get_by_role("application", name=re.compile(r"^line chart"))
        self.channels_heading: Locator = main.get_by_role("heading", name="Channels", exact=True)
        self.channels_date_range_input: Locator = main.get_by_role("textbox", name="Choose date range", exact=True)
        self.top_performing_products_heading: Locator = main.get_by_role(
            "heading", name="Top Performing Products", exact=True
        )
        self.recent_orders_heading: Locator = main.get_by_role("heading", name="Recent Orders", exact=True)
        self.common_order_status_heading: Locator = main.get_by_role(
            "heading", name="Common Order Status", exact=True
        )
        self.warehouse_order_status_heading: Locator = main.get_by_role(
            "heading", name="Warehouse Order Status", exact=True
        )
