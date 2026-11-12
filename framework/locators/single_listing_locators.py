"""Locators of the SHP Listing → Common Listing → Create Listing → Single Listing → Manual page (``/single-listing/add``).

Verified against the live page on 2026-09-30. The page is titled "Add New Listing" and holds five
sections (ids ``sec-store`` … ``sec-product``) reached through five section buttons. The form
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
DESCRIPTION_REQUIRED_MESSAGE = REQUIRED_MESSAGE.format(label="Description")
VALIDATION_TOAST = "Validation errors: {first_three}, and {remaining} more"
"""The toast shown with the field messages: the first three messages, comma-separated, then the rest as a count."""


class Section(NamedTuple):
    button: str
    """The section button's text."""
    element_id: str
    heading: str


SECTIONS = (
    Section("Store / Policy", "sec-store", "Store / Policy"),
    Section("Item Specifics", "sec-specifics", "Item Specifics"),
    Section("Selling Details", "sec-selling", "Selling Details"),
    Section("Shipping Details", "sec-shipping", "Shipping Details"),
    Section("Product Details", "sec-product", "Product Details"),
)
"""Every section button, in page order, with the section it leads to."""


class Field(NamedTuple):
    section_id: str
    label: str
    errors_when_empty: bool = True
    """False = the untouched form raises no error for it: it is preselected, or disabled until a category is chosen."""


FIELDS = (
    Field("sec-store", "Fulfillment Policy"),
    Field("sec-store", "Payment Policy"),
    Field("sec-store", "Return Policy"),
    Field("sec-store", "eBay Category"),
    Field("sec-store", "Specification", False),  # disabled until an eBay category is chosen
    Field("sec-store", "Spec Value", False),  # disabled until an eBay category is chosen
    Field("sec-store", "Condition"),
    Field("sec-store", "Condition Description"),
    Field("sec-specifics", "Brand Code"),
    Field("sec-specifics", "Part Number / Product ID"),
    Field("sec-specifics", "Other Part Number"),
    Field("sec-specifics", "Interchange Part Number"),
    Field("sec-specifics", "Brand"),
    Field("sec-specifics", "Warranty"),
    Field("sec-specifics", "UPC"),
    Field("sec-specifics", "EPID"),
    Field("sec-selling", "Listing Type"),
    Field("sec-selling", "Private Listing", False),  # "No" is preselected
    Field("sec-selling", "Listing Duration"),
    Field("sec-selling", "Quantity"),
    Field("sec-shipping", "Handling Time"),
    Field("sec-shipping", "Postal Code"),
    Field("sec-shipping", "Site", False),  # "US" is preselected
    Field("sec-product", "Title"),
    Field("sec-product", "Sub Title"),
    Field("sec-product", "SKU"),
    Field("sec-product", "UPC"),
    Field("sec-product", "Video URL"),
    Field("sec-product", "Start Price"),
    Field("sec-product", "Compare Price"),
    Field("sec-product", "Item Cost"),
    Field("sec-product", "Tags"),
    Field("sec-product", "Product Type"),
)
"""Every labelled form field, in page order. Each one is mandatory: its label carries the red "*" marker."""

CHECKBOXES = ("Add Prop 65 Warning", "Charge tax on this product", "This is a physical product")


class SingleListingLocators:
    """Every element the Single Listing tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._main = page.get_by_role("main")

        # Page header.
        self.page_heading: Locator = self._main.get_by_role("heading", name="Add New Listing", exact=True)
        self.breadcrumb: Locator = self._main.get_by_role("navigation", name="breadcrumb")

        # Item Specifics extra, and the Description editor and Product Images inside Product Details.
        self.add_specification_button: Locator = self.section("sec-specifics").get_by_role(
            "button", name="Add Specification"
        )
        product = self.section("sec-product")
        self.description_label: Locator = product.locator("label").filter(
            has_text=re.compile(r"^\s*Description\s*\*\s*$")
        )
        self.description_format_select: Locator = product.get_by_title("Paragraph format")
        self.description_editor: Locator = product.locator("[contenteditable='true']")
        self.description_required_message: Locator = self.description_label.locator("xpath=..").get_by_text(
            DESCRIPTION_REQUIRED_MESSAGE, exact=True
        )
        self.images_label: Locator = product.locator("label").filter(has_text="Product Images")
        self.select_from_library_button: Locator = product.get_by_role("button", name="Select from Library")
        self.upload_from_storage_button: Locator = product.get_by_role("button", name="Upload from Storage")
        self.images_required_message: Locator = self.images_label.locator("xpath=..").get_by_text(
            IMAGES_REQUIRED_MESSAGE, exact=True
        )

        # Action buttons at the bottom of the form (their names start with an icon glyph).
        self.save_as_draft_button: Locator = self._main.get_by_role("button", name="Save as Draft")
        self.send_to_live_button: Locator = self._main.get_by_role("button", name="Send to Live")

        # The toast that summarises the validation errors.
        self.validation_toast: Locator = page.get_by_role("status").filter(has_text="Validation errors:")

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
