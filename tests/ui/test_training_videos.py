"""Training Videos: the page opens from the sidebar, shows its videos, and plays one at a time.

The page is reached by clicking the "Training videos" sidebar menu only; no other
menu entry is used. Video content (titles, descriptions, authors, dates, durations),
cards whose video is unavailable and the rest of the page are not verified, and no
application data is changed.

Videos are YouTube embeds, so these tests need outbound access to youtube.com.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from framework.pages.training_videos_page import TrainingVideosPage

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


@pytest.fixture
def training_videos(authenticated_page: Page) -> TrainingVideosPage:
    """The Training Videos page, opened from the sidebar of the signed-in dashboard."""
    page = TrainingVideosPage(authenticated_page)
    page.open_from_sidebar()
    return page


def test_training_videos_page_opens_successfully(training_videos: TrainingVideosPage, base_url: str) -> None:
    expect(training_videos.page).to_have_url(f"{base_url}{TrainingVideosPage.PATH}")


def test_training_videos_heading_is_visible(training_videos: TrainingVideosPage) -> None:
    expect(training_videos.locators.page_heading).to_be_visible()


def test_video_cards_are_visible(training_videos: TrainingVideosPage) -> None:
    expect(training_videos.locators.video_cards.first).to_be_visible()
    expect(training_videos.locators.play_buttons.first).to_be_visible()


@pytest.mark.functional
def test_selected_video_starts_playing(training_videos: TrainingVideosPage) -> None:
    title = training_videos.playable_titles(1)[0]

    training_videos.play(title)

    expect(training_videos.locators.player(title)).to_be_visible()
    assert training_videos.wait_until_playing(title).playing


@pytest.mark.functional
def test_only_one_video_plays_at_a_time(training_videos: TrainingVideosPage) -> None:
    first, second = training_videos.playable_titles(2)
    training_videos.play(first)
    assert training_videos.wait_until_playing(first).playing

    training_videos.play(second)

    assert training_videos.wait_until_playing(second).playing
    # The first video's player is gone, so it cannot play on: its card offers Play again.
    expect(training_videos.locators.player(first)).to_have_count(0)
    expect(training_videos.locators.play_button(first)).to_be_visible()
    expect(training_videos.locators.players).to_have_count(1)
