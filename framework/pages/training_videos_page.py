"""Page object of the SHP Training Videos page."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from framework.locators.training_videos_locators import TrainingVideosLocators
from framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)

PLAY_LABEL_PREFIX = "Play "

READ_PLAYBACK = "video => ({paused: video.paused, position: video.currentTime})"


@dataclass(frozen=True)
class PlaybackState:
    """What the player of one card reports: whether it is paused and where it is."""

    paused: bool
    position: float

    @property
    def playing(self) -> bool:
        return not self.paused and self.position > 0


class TrainingVideosPage(BasePage):
    PATH = "/training-videos"

    PLAYBACK_TIMEOUT = 30_000
    """How long a started video may take to reach the server and really play, in ms."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.locators = TrainingVideosLocators(page)

    def open_from_sidebar(self) -> None:
        """Open the page the way a user does: the 'Training videos' sidebar menu; nothing else is clicked."""
        self.click(self.locators.sidebar_menu_entry, "'Training videos' sidebar menu")

    def playable_titles(self, wanted: int) -> list[str]:
        """Titles of the first ``wanted`` playable cards, skipping repeated titles.

        Titles are the page's own handle on a card (button name and player title),
        so a title used by two cards cannot identify one of them and is skipped.

        Raises:
            LookupError: the page offers fewer playable videos than requested.
        """
        buttons = self.locators.play_buttons
        buttons.first.wait_for()
        labels: list[str] = buttons.evaluate_all(
            "buttons => buttons.map(button => button.getAttribute('aria-label'))"
        )

        titles: list[str] = []
        for label in labels:
            title = label.removeprefix(PLAY_LABEL_PREFIX)
            if title not in titles:
                titles.append(title)
            if len(titles) == wanted:
                logger.info("Playable videos selected: %s", titles)
                return titles
        raise LookupError(
            f"The page offers {len(titles)} playable video(s) with a distinct title, {wanted} needed"
        )

    def play(self, title: str) -> None:
        """Start the video of ``title`` and wait until its player is embedded."""
        self.click(self.locators.play_button(title), f"play button of the video '{title}'")
        self.locators.player(title).wait_for()

    def playback_state(self, title: str) -> PlaybackState:
        """What the player of ``title`` reports right now, without waiting."""
        return PlaybackState(**self.locators.player_video(title).evaluate(READ_PLAYBACK))

    def wait_until_playing(self, title: str) -> PlaybackState:
        """Wait until the video of ``title`` really plays, and return the state then observed.

        Really playing means: the player's video element is not paused and its
        position has advanced between two readings, so a loaded but frozen player
        does not pass.

        Raises:
            PlaywrightTimeoutError: playback had not started within PLAYBACK_TIMEOUT.
        """
        video = self.locators.player_video(title)
        deadline = time.monotonic() + self.PLAYBACK_TIMEOUT / 1000
        video.wait_for(timeout=self.PLAYBACK_TIMEOUT)

        started_at: float | None = None
        while time.monotonic() < deadline:
            state = PlaybackState(**video.evaluate(READ_PLAYBACK))
            if state.playing:
                if started_at is None:
                    started_at = state.position
                elif state.position > started_at:
                    logger.info("Video '%s' plays (position %.1fs)", title, state.position)
                    return state
            else:
                started_at = None
            self.page.wait_for_timeout(500)
        raise PlaywrightTimeoutError(
            f"Video '{title}' did not play within {self.PLAYBACK_TIMEOUT} ms "
            f"(last state: {self.playback_state(title)})"
        )
