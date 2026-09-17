"""Locators of the SHP Billing page (My Account → Billing).

Written from the Billing screenshot and the patterns verified on the other pages;
**not yet verified against the live Billing DOM**. The table controls and
pagination follow the Manage Channel page, which uses the same table component.

Billing values (plan names, amounts, statuses, dates, payment methods, invoices)
are data and are deliberately not part of any locator. The current plan's name,
amount and status/date are found by their position in the Current Plan section or
by the *format* of their text (a currency amount, a date), never by their value.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PAGE_HEADING = "Billing"
CURRENT_PLAN_LABEL = "Current Plan"

COLUMN_HEADERS = (
    "S.No",
    "Plan",
    "Amount",
    "Status",
    "Invoice",
    "Payment Method",
    "Period Start",
    "Period End",
)
"""Every column header of the billing table, in the order the page renders them."""

AMOUNT_FORMAT = re.compile(r"([$€£₹]|\b[A-Z]{3}\b)\s?\d")
"""Text shaped like an amount (currency symbol or code followed by a number); the value is not matched."""

DATE_FORMAT = re.compile(
    r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}"  # 2026-09-14, 14/09/2026
    r"|[A-Z][a-z]{2,8}\.? \d{1,2},? \d{4}"  # Sep 14, 2026
    r"|\d{1,2} [A-Z][a-z]{2,8},? \d{4}"  # 14 Sep 2026
)
"""Text shaped like a date; the value is not matched."""


class BillingLocators:
    """Every element the Billing tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: "My Account" opens the sub-menu that holds "Billing".
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_my_account_menu: Locator = sidebar_menu.get_by_role("button", name="My Account")
        self.sidebar_billing_entry: Locator = sidebar_menu.get_by_role("link", name="Billing")

        # The page title may repeat as a card title (as on Manage Channel), so the first one is taken.
        self.page_heading: Locator = self._main.get_by_role("heading", name=PAGE_HEADING, exact=True).first

        # Current Plan summary: the innermost block holding the "Current Plan" heading and an amount.
        # The heading reads "Current Plan (billed)" (h6); the suffix may vary, so only its start is matched.
        current_plan_heading = page.get_by_role("heading", name=re.compile(rf"^{CURRENT_PLAN_LABEL}"), level=6)
        self.current_plan_label: Locator = self._main.locator(current_plan_heading)
        # A ``has`` locator is searched inside each candidate, so it must not be scoped to ``main`` itself.
        self.current_plan_section: Locator = (
            self._main.locator("div").filter(has=current_plan_heading).filter(has_text=AMOUNT_FORMAT).last
        )
        # The plan name is the section's h4 heading; its value is not matched.
        self.current_plan_name: Locator = self.current_plan_section.get_by_role("heading", level=4)
        self.current_plan_amount: Locator = self.current_plan_section.get_by_text(AMOUNT_FORMAT).first
        self.current_plan_status_date: Locator = self.current_plan_section.get_by_text(DATE_FORMAT).first

        # Table and its "Show <n> entries" control.
        self.show_entries_select: Locator = self._main.get_by_role("combobox", name="Entries per page", exact=True)
        self.table: Locator = self._main.get_by_role("table")

        # Pagination. The current page number is marked with a class only (D28).
        self.pagination: Locator = self._main.get_by_role("navigation", name="Pagination")
        self.previous_button: Locator = self.pagination.get_by_role("button", name="Previous", exact=True)
        self.next_button: Locator = self.pagination.get_by_role("button", name="Next", exact=True)
        self.current_page: Locator = self.pagination.locator("li.active").get_by_role("button")

    def column_header(self, name: str) -> Locator:
        """Column header ``name``; matched as a substring because sortable headers may append a "⇅" glyph."""
        return self._main.get_by_role("columnheader", name=name)
