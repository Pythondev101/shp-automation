"""Locators of the SHP Listing → Common Listing → Create Listing → Single Listing page (``/single-listing/add``).

Verified against the live page on 2026-09-22. The page is titled "Add New Listing" and holds eight
sections (ids ``sec-store`` … ``sec-images``) reached through eight section buttons. The form
labels are not linked to their controls, so each field is located through its label: the field
is the label's parent element, which also holds the control and its validation message. "UPC"
is a label in both Item Specifics and Product Details, so fields are always scoped to a section.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from playwright.sync_api import Locator, Page

PAGE_URL = re.compile(r"/single-listing/add$")
FORM_OPTIONS_API_PATH = "/api/v1/single-listing/form-options"
"""The request that fills the policy, condition, listing and handling-time dropdowns."""
API_URL_PATTERN = "**/api/**"

REQUIRED_MESSAGE = "{label} is required."
"""The message the application shows under an empty required field on Save as Draft / Send to Live."""
IMAGES_REQUIRED_MESSAGE = "Please upload at least one product image."


class Section(NamedTuple):
    button: str
    """The section button's text."""
    element_id: str
    heading: str


SECTIONS = (
    Section("Store Setup", "sec-store", "eBay Store Setup"),
    Section("Condition", "sec-condition", "Condition"),
    Section("Item Specifics", "sec-specifics", "Item Specifics"),
    Section("Selling", "sec-selling", "Selling Details"),
    Section("Shipping", "sec-shipping", "Shipping & Pricing"),
    Section("Product", "sec-product", "Product Details"),
    Section("Description", "sec-description", "Description"),
    Section("Images", "sec-images", "Product Images"),
)
"""Every section button, in page order, with the section it leads to."""


class Field(NamedTuple):
    section_id: str
    label: str
    required: bool


FIELDS = (
    Field("sec-store", "Fulfillment Policy", True),
    Field("sec-store", "Payment Policy", True),
    Field("sec-store", "Return Policy", True),
    Field("sec-store", "eBay Category", True),
    Field("sec-condition", "Condition", True),
    Field("sec-condition", "Condition Description", False),
    Field("sec-specifics", "Brand Code", True),
    Field("sec-specifics", "Part Number / Product ID", True),
    Field("sec-specifics", "Other Part Number", True),
    Field("sec-specifics", "Interchange Part Number", True),
    Field("sec-specifics", "Brand", True),
    Field("sec-specifics", "Warranty", True),
    Field("sec-specifics", "UPC", True),
    Field("sec-specifics", "EPID", True),
    Field("sec-selling", "Listing Type", True),
    Field("sec-selling", "Private Listing", False),
    Field("sec-selling", "Listing Duration", True),
    Field("sec-selling", "Quantity", True),
    Field("sec-shipping", "Handling Time", True),
    Field("sec-shipping", "Start Price", True),
    Field("sec-shipping", "Item Cost", False),
    Field("sec-shipping", "Postal Code", True),
    Field("sec-shipping", "Site", False),
    Field("sec-product", "Title", True),
    Field("sec-product", "Sub Title", False),
    Field("sec-product", "SKU", True),
    Field("sec-product", "UPC", False),
    Field("sec-product", "Tags", False),
    Field("sec-product", "Video URL", False),
)
"""Every labelled form field, in page order; ``required`` = the label carries the red "*" marker."""

CHECKBOXES = ("Add Prop 65 Warning", "Charge tax on this product", "This is a physical product")


class SingleListingLocators:
    """Every element the Single Listing tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Page header.
        self.page_heading: Locator = self._main.get_by_role("heading", name="Add New Listing", exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")

        # Item Specifics, Description and Images extras.
        self.add_specification_button: Locator = self.section("sec-specifics").get_by_role(
            "button", name="Add Specification"
        )
        self.description_format_select: Locator = self.section("sec-description").get_by_title("Paragraph format")
        self.description_editor: Locator = self.section("sec-description").locator("[contenteditable='true']")
        self.images_label: Locator = self.section("sec-images").locator("label").filter(has_text="Product Images")
        self.select_from_library_button: Locator = self.section("sec-images").get_by_role(
            "button", name="Select from Library"
        )
        self.upload_from_storage_button: Locator = self.section("sec-images").get_by_role(
            "button", name="Upload from Storage"
        )
        self.images_required_message: Locator = self.section("sec-images").get_by_text(
            IMAGES_REQUIRED_MESSAGE, exact=True
        )

        # Action buttons at the bottom of the form (their names start with an icon glyph).
        self.save_as_draft_button: Locator = self._main.get_by_role("button", name="Save as Draft")
        self.send_to_live_button: Locator = self._main.get_by_role("button", name="Send to Live")

    def section(self, element_id: str) -> Locator:
        return self._page.locator(f"#{element_id}")

    def section_button(self, name: str) -> Locator:
        return self._main.get_by_role("button", name=name, exact=True)

    def section_heading(self, section: Section) -> Locator:
        return self.section(section.element_id).get_by_role("heading", name=section.heading, exact=True)

    def field_label(self, field: Field) -> Locator:
        return (
            self.section(field.section_id)
            .locator("label")
            .filter(has_text=re.compile(rf"^\s*{re.escape(field.label)}\s*\*?\s*$"))
        )

    def required_marker(self, field: Field) -> Locator:
        return self.field_label(field).get_by_text("*", exact=True)

    def field_control(self, field: Field) -> Locator:
        """The field's input, select or textarea (inputs wrapped in a "$" group included)."""
        return self.field_label(field).locator("xpath=..").locator("input, select, textarea").first

    def required_message(self, field: Field) -> Locator:
        return (
            self.field_label(field)
            .locator("xpath=..")
            .get_by_text(REQUIRED_MESSAGE.format(label=field.label), exact=True)
        )

    def checkbox(self, label: str) -> Locator:
        return self._main.get_by_role("checkbox", name=label, exact=True)
