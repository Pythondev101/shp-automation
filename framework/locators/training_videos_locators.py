"""Locators of the SHP Training Videos page (``/training-videos``).

Verified against the live DOM on 2026-09-12. The page has no ``data-testid``
attributes. Each video is a Bootstrap card without a landmark or id, so a card is
identified by what the application itself exposes: a playable card holds a button
named ``Play <video title>``, and while it plays, a YouTube ``iframe`` whose
``title`` is that same video title. Video titles, descriptions, authors and dates
are content and are deliberately not part of any locator.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

PLAY_BUTTON_NAME = re.compile(r"^Play .")
"""Accessible name of a playable card's button: ``Play`` followed by the video title."""


class TrainingVideosLocators:
    """Every element the Training Videos tests use. Locators are lazy: nothing is looked up until used."""

    def __init__(self, page: Page) -> None:
        self._main = page.get_by_role("main")

        # Sidebar: the only menu entry these tests click.
        sidebar_menu = page.get_by_role("complementary").get_by_role("navigation")
        self.sidebar_menu_entry: Locator = sidebar_menu.get_by_role("link", name="Training videos")

        self.page_heading: Locator = self._main.get_by_role("heading", name="Training Videos", exact=True)
        # One title heading per card, playable or not: the cards rendered on the page.
        self.video_cards: Locator = self._main.get_by_role("heading", level=6)
        # Cards that offer playback; cards whose video is gone show a placeholder instead of a button.
        self.play_buttons: Locator = self._main.get_by_role("button", name=PLAY_BUTTON_NAME)
        # Every embedded player currently on the page (the page embeds one at most).
        self.players: Locator = self._main.locator("iframe")

    def play_button(self, title: str) -> Locator:
        """Play button of the card of ``title``; absent while that video plays."""
        return self._main.get_by_role("button", name=f"Play {title}", exact=True)

    def player(self, title: str) -> Locator:
        """The embedded player of ``title``; absent until that video is started."""
        # and_() keeps the title an attribute match, so titles with quotes need no escaping.
        return self.players.and_(self._main.get_by_title(title, exact=True))

    def player_video(self, title: str) -> Locator:
        """The ``video`` element inside the embedded player of ``title``."""
        return self.player(title).content_frame.locator("video")
