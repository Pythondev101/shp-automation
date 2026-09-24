# SHP Test Automation

External (black-box) test automation framework for the **SHP web application**.
This repository contains tests only; it does not contain SHP application code.

This file is the single source of truth for the framework. It is updated after every approved change.

## Current status

| Item | State |
|---|---|
| Phase | **Step 10 – My Profile functionality complete** (21 my-profile tests; manage channel: 29; training videos: 5; dashboard: 3; login: 16) |
| Automated modules | Login – page elements, links, client-side validation, valid sign-in, session persistence. Dashboard – visibility of sidebar, header and content sections. Training Videos – page opens from the sidebar, videos are shown, a video plays and only one plays at a time. Manage Channel – visibility of the page's UI controls and every table column header, the "Add a new connection" popup, and the full connect → verify → delete journey against SHP's local dev sandbox. My Account → My Profile – visibility of every field and control of the three sections; editable fields, dropdowns and the Country → State → City dependency, Save Profile with restore, and password change with immediate restore |
| Latest run | 2026-09-14: My Profile **21/21 on Chromium** (password restored to the `.env` value). 2026-09-12: full suite 60/60 on Chromium. The full suite has not been re-run since Step 10, and not cross-browser since Step 7 |
| Next pending step | Awaiting instruction. Suggested: a full cross-browser suite run to confirm the total (expected 180 = 60 per browser) |

## Tech stack

| Package | Version | Purpose |
|---|---|---|
| Python | 3.13 (verified) | Language |
| pytest | 9.1.1 | Test runner, markers, fixtures, logging, JUnit report |
| playwright | 1.62.0 | Browser automation (Chromium, Firefox, WebKit); built-in HTTP client for API tests |
| pytest-playwright | 0.9.0 | Browser/page fixtures, cross-browser runs, screenshots/traces/videos (brings `pytest-base-url`) |
| python-dotenv | 1.2.3 | Loads the local `.env` file |

Other Python versions supported by Playwright should work but are not yet verified.

## Project structure

```
SHP_Automation/
├── README.md            # this document
├── requirements.txt     # pinned direct dependencies
├── pytest.ini           # markers, strict mode, logging, artifact and report defaults
├── .env.example         # configuration template (committed)
├── .gitignore
├── .github/
│   └── workflows/
│       └── automation-tests.yml   # GitHub Actions pipeline (see Continuous integration)
├── framework/           # reusable non-test code
│   ├── __init__.py
│   ├── config.py        # the only place configuration is read
│   ├── locators/        # locators of each page (what elements are and how to find them)
│   │   ├── __init__.py
│   │   ├── login_locators.py
│   │   ├── dashboard_locators.py
│   │   ├── training_videos_locators.py
│   │   ├── manage_channel_locators.py
│   │   ├── my_profile_locators.py
│   │   ├── billing_locators.py
│   │   └── help_center_locators.py
│   └── pages/           # page actions and page objects (what a user can do on each page)
│       ├── __init__.py
│       ├── base_page.py # page actions shared by every page object
│       ├── login_page.py
│       ├── dashboard_page.py
│       ├── training_videos_page.py
│       ├── manage_channel_page.py
│       ├── my_profile_page.py
│       ├── billing_page.py
│       └── help_center_page.py
└── tests/
    ├── conftest.py      # shared fixtures (incl. authenticated_page), logging and sign-in safety hooks
    └── ui/
        ├── test_login.py
        ├── test_dashboard.py
        ├── test_training_videos.py
        ├── test_manage_channel.py
        ├── test_my_profile.py
        ├── test_billing.py
        └── test_help_center.py
```

Generated locally and git-ignored: `.venv/`, `.env`, `test-results/`, `reports/`, `__pycache__/`, `.pytest_cache/`.

**Growth rule:** folders are created only when their first real content exists:

| Folder | Created when |
|---|---|
| `framework/pages/`, `framework/locators/`, `tests/ui/` | created in Step 2 (Login page) |
| `framework/api/` + `tests/api/` | the first API module is automated |
| `tests/integration/` | the first cross-layer (UI → API → DB) or E2E flow is automated |
| `framework/db/` | database access details are provided |
| `test_data/` | test data outgrows inline `@pytest.mark.parametrize` |

Folders are organised by **test layer**; test categories are **markers**, so a test is written once and tagged with every category it belongs to.

## Setup

Run every command from the project root.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium firefox webkit
Copy-Item .env.example .env      # then fill in the values
```

If script execution is blocked, skip activation and call the interpreter directly: `.venv\Scripts\python -m pytest`.

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install --with-deps chromium firefox webkit   # --with-deps installs Linux system libraries
cp .env.example .env             # then fill in the values
```

## Configuration

All configuration is read by `framework/config.py`; tests and page objects never read environment variables directly.
Real environment variables (e.g. set by CI) take precedence over values in `.env`.

| Variable | Required | Description |
|---|---|---|
| `SHP_BASE_URL` | Yes, for every test | Application URL, e.g. `http://52.44.166.66:8080` |
| `SHP_USERNAME` | For tests that log in | **Email address** of the dedicated automation account (the login form has an Email field) |
| `SHP_PASSWORD` | For tests that log in | Password of the dedicated automation account |

- Credentials come only from `.env` / the environment; they are never written in tests, page objects, logs or this document.
- `.env` holds real values and is git-ignored; `.env.example` is the committed template.
- A missing required value stops the affected test with a clear `ConfigError` (it is an error, not a skip, so CI cannot pass silently).
- The password is excluded from the `Credentials` object's text representation, so it does not appear in logs or tracebacks.
- `--base-url <url>` overrides `SHP_BASE_URL` for a single run.

## Running tests

```bash
pytest                                                  # all tests, Chromium, headless
pytest tests/ui/test_login.py                           # one module (Login page)
pytest tests/ui/test_dashboard.py                       # one module (Dashboard visibility)
pytest tests/ui/test_training_videos.py                 # one module (Training Videos)
pytest tests/ui/test_manage_channel.py                  # one module (Manage Channel: page, popup, connect + delete)
pytest tests/ui/test_my_profile.py                      # one module (My Account → My Profile visibility + functionality; changes and restores the password)
pytest tests/ui/test_billing.py                         # one module (My Account → Billing visibility)
pytest tests/ui/test_help_center.py                     # one module (Help Center visibility)
pytest -m smoke                                         # one category
pytest -m "regression and not api"                      # marker expressions
pytest -m "not destructive"                             # everything that writes no data
pytest -m destructive                                   # the create/edit/delete and account-state tests
pytest -m shared_state                                  # only the tests that change profile, password or plan
pytest tests/ui                                         # one layer
pytest --browser firefox                                # another browser
pytest --browser chromium --browser firefox --browser webkit   # cross-browser
pytest --headed --slowmo 500                            # watch the browser while debugging
pytest --video retain-on-failure                        # also keep videos of failed tests
pytest --base-url http://other-host:8080                # target another environment once
```

Exit codes (for CI): `0` all passed, `1` failures or errors, `2` interrupted (including the sign-in safety stop, see [Login safety](#login-safety-account-lockout)), `4` usage error, `5` no tests collected.

## UI architecture (Page Object Model)

Each UI page is split into four layers; a layer only uses the layers above it.

| Layer | Location | Responsibility |
|---|---|---|
| Locators | `framework/locators/<page>_locators.py` | One class per page that builds every Playwright locator of that page. The only place selectors are written. |
| Page actions | `framework/pages/base_page.py` | `BasePage`: actions shared by all pages – `open()` (navigates to the page's `PATH`), `click()`, `fill()`, `fill_secret()` (for passwords: value never logged and masked in error messages), `press()`, and `_untraced()` (keeps secret-handling steps out of Playwright traces). Each action is logged to `reports/pytest.log`; filled values never are. |
| Page object | `framework/pages/<page>_page.py` | One class per page, inheriting `BasePage`: the page's route (`PATH`), its locators (`self.locators`) and page-specific actions (e.g. `go_to_register()`). No assertions. |
| Tests | `tests/ui/test_<page>.py` | Arrange with page-object actions, assert with Playwright's auto-waiting `expect(...)` on the page object's locators. No raw selectors. |

**Locator strategy** (verified against the live DOM, not guessed):

1. `data-testid` if the application adds one (SHP has none today).
2. Accessible role + name, e.g. `get_by_role("button", name="Sign in", exact=True)` – the way a user and screen reader see the page.
3. Stable form attributes such as `name`, e.g. `input[name='email']` – used where labels are not linked to their inputs.
4. Exact text only for messages whose text is what the test verifies, e.g. `get_by_text("Email is required", exact=True)` (SHP's validation messages have no role or id).
5. CSS classes, XPath and positional selectors are avoided.

Locators are scoped to a page landmark (`complementary` sidebar, `banner` header, `main`) where the page has one, so the same name elsewhere on the page cannot match.

**Adding a page:** inspect its DOM, create `framework/locators/<page>_locators.py` and `framework/pages/<page>_page.py` (inheriting `BasePage`, setting `PATH`), then `tests/ui/test_<page>.py`. A fixture used by one test module lives in that module; it moves to a `conftest.py` once a second module needs it.

## Login tests

`tests/ui/test_login.py` – page `/login` (page object `LoginPage`). All tests carry the `authentication` and `regression` markers. No application data is changed. The `#` column maps to the Login requirements list.

| # | Test | Verifies | Extra markers |
|---|---|---|---|
| 1 | `test_login_url_opens_successfully` | `/login` responds with an HTTP success status and the browser stays on `/login` | `smoke` |
| 2 | `test_login_page_is_displayed` | Heading "Sign in to your account" is visible | `smoke` |
| 3 | `test_email_field_is_visible_and_enabled` | Email field is visible, enabled and editable | `smoke` |
| 4 | `test_password_field_is_visible_and_enabled` | Password field is visible, enabled and editable | `smoke` |
| 5 | `test_sign_in_button_is_visible_and_enabled` | "Sign in" button is visible and enabled | `smoke` |
| 6 | `test_forgot_password_link_opens_forgot_password_page` | "Forgot password?" link is visible; clicking it opens `/forgot-password` showing "Forgot your password?" | `functional` |
| 7 | `test_register_link_opens_register_page` | "Register" link is visible; clicking it opens `/register` showing "Create your account" | `functional` |
| 8 | `test_password_is_masked_by_default` | Typed text in the password field is masked (`type="password"`) | – |
| 9 | `test_password_visibility_toggle_shows_and_hides_password` | Eye button is visible; first click reveals the text (`type="text"`, button name "Hide password"), second click masks it again ("Show password"); the value is kept | `functional` |
| 10 | `test_fields_accept_valid_input` | Email and password fields keep the typed values | `functional` |
| 11 | `test_empty_email_shows_required_message_without_sign_in_request` | Submitting without an email shows "Email is required" (only), stays on `/login`, and sends **no** API request | `functional` |
| 12 | `test_empty_password_shows_required_message_without_sign_in_request` | Submitting without a password shows "Password is required" (only), stays on `/login`, and sends **no** API request | `functional` |
| 13–16 | `test_valid_credentials_sign_in_and_open_dashboard` | The `.env` account signs in with the Sign in button: server confirms, browser lands on `/dashboard`, the signed-in header ("Notifications" button) is visible, the login form is gone | `smoke`, `functional` |
| 17 | `test_session_persists_after_page_refresh` | A signed-in page stays on `/dashboard` and signed in after a reload | `functional` |
| 18 | `test_enter_key_submits_login_form` | Pressing Enter in the password field signs in and lands on `/dashboard` | `functional` |
| 19 | `test_password_is_not_written_to_logs` | After a sign-in, the password is absent from `reports/pytest.log`, the captured log records and the `Credentials` text form (and the sign-in is present in the log, so the check is meaningful) | – |
| 20 | fixture `authenticated_page` | Reusable signed-in page for future tests (see below); used by tests 17 and 19 | – |

Tests 8–12 type only dummy values (`validation.check@example.com`, a dummy password text) and never submit them to the server.

Login facts observed on 2026-09-11: the user field is **Email** (`name="email"`, `type="email"`); validation is client-side (react-hook-form, form has `novalidate`) with the messages "Email is required", "Enter a valid email address" and "Password is required"; the form posts `email` + `password` to `POST /api/v1/auth/web_login`; success answers `{"status": true, ...}` and the app navigates to `/dashboard` (to `/upgrade-plan` for a suspended account); the token is kept in `localStorage` (`shp-auth`), no cookies, so a reload keeps the session; a new sign-in does not end earlier sessions; visiting `/login` while signed in shows the login page (no redirect).

### Login safety (account lockout)

SHP may deactivate an account after 3 wrong-password attempts. The framework therefore:

- **Never** submits wrong passwords, invalid email/password combinations or lockout scenarios, and never retries a sign-in.
- Signs in only with the `.env` account, through `LoginPage.login()`, which submits exactly once and checks the server's answer.
- Raises `AuthenticationError` when the server does not confirm a sign-in (or gives no readable answer). A hook in `tests/conftest.py` then **stops the whole run** after that test (exit code `2`, `Interrupted: Sign-in was not confirmed...`), so no later test can try again. Fix `SHP_USERNAME` / `SHP_PASSWORD` before re-running – each run makes at most one failed attempt.
- Validation tests (11, 12) abort every `/api/**` request inside the browser (`blocked_api_requests` fixture) and assert that none was attempted, so nothing can reach the server even if client-side validation broke.
- Real sign-ins per full run: 3 per browser (tests 13–16 and 18, plus the first use of `authenticated_page`).

### Reusing a signed-in session (`authenticated_page`)

Fixture in `tests/conftest.py` for any future test that needs a signed-in user:

```python
def test_something(authenticated_page: Page) -> None:
    ...  # the page is signed in and open on /dashboard
```

The first test that uses it signs in through the login form; the resulting browser storage is kept **in memory only** (never written to disk) and reused by later tests, each in its own fresh browser context. One sign-in per browser per run; every test still works when run alone.

### Keeping the password out of logs, traces and reports

- `Credentials` hides the password from its text form; `fill_secret()` logs `Fill password field (value hidden)`, masks the value in Playwright error messages and hides its frame from pytest tracebacks.
- Playwright traces record typed text **and request bodies** (the sign-in request contains the password). `LoginPage.login()` therefore stops tracing completely while the credentials are typed and sent, and restarts it once the login form is gone. The trace of a sign-in test starts after that step.
- If a sign-in fails, the password field is cleared before the screenshot and trace are taken (the screenshot then also shows "Password is required" under the empty field).
- Verified 2026-09-11 by scanning every file in `test-results/` (with `--tracing on`) and `reports/` for the password: not found, for successful and (simulated) rejected sign-ins.
- Traces of signed-in tests do contain the session token (request headers, `localStorage`); treat `trace.zip` files as confidential.

## Dashboard tests

`tests/ui/test_dashboard.py` – page `/dashboard` (page object `DashboardPage`, locators `DashboardLocators`). All tests carry the `smoke` and `regression` markers and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run.

**Visibility only:** counts, earnings, chart data, product rows and percentages are dynamic and are not checked. Nothing is clicked (no sidebar navigation, no date-range selection), and no application data is changed.

| Test | Verifies visible |
|---|---|
| `test_sidebar_branding_and_menu_are_visible` | SellerHub Pro logo and name; menu entries Dashboard, Active Listing, Manage Order, Manage Channel, My Account, Help Center, Training videos, Upgrade Plan, Customer |
| `test_header_elements_are_visible` | Top search bar, Notifications button, user/profile button |
| `test_dashboard_sections_are_visible` | Browser is on `/dashboard`; "Welcome Seller" heading; Active Orders and Today Order cards; This Month Earnings; Orders chart (heading and chart); Channels section and its date-range field; Top Performing Products, Recent Orders, Common Order Status and Warehouse Order Status sections |

Dashboard facts observed on 2026-09-11: no `data-testid`; the page has `complementary` (sidebar), `banner` (header) and `main` landmarks. Menu entries with a sub-menu (Active Listing, Manage Order, My Account) are buttons, the others links, and every menu name starts with an icon glyph. Dashboard sections are Bootstrap cards without a landmark or ID, so each section is identified by its heading (`h5`, `h3` for "Welcome Seller"); "This Month Earnings" is plain text. The Active Orders / Today Order cards are links whose names include the current count. The profile button is named after the account's full name, so it is located as the only header button with a `title` attribute. The Orders chart is an ApexCharts SVG with role `application` and a name starting "line chart". The Channels date-range field is a read-only text field (placeholder "Choose date range") next to a hidden duplicate input, which the role locator ignores.

## Training Videos tests

`tests/ui/test_training_videos.py` – page `/training-videos` (page object `TrainingVideosPage`, locators `TrainingVideosLocators`). All tests carry the `smoke` and `regression` markers and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run. The page is reached by clicking the **"Training videos" sidebar menu only**; no other menu entry is used.

**Scope:** the page opening, its heading, that video cards are shown, and playback. Video content (titles, descriptions, authors, dates, durations), cards whose video is unavailable and every other module are not verified. Nothing is created, edited or deleted.

| # | Test | Verifies | Extra markers |
|---|---|---|---|
| 1 | `test_training_videos_page_opens_successfully` | The sidebar menu opens `/training-videos` | – |
| 2 | `test_training_videos_heading_is_visible` | Heading "Training Videos" is visible | – |
| 3 | `test_video_cards_are_visible` | Video cards are rendered and visible, at least one of them playable | – |
| 4–5 | `test_selected_video_starts_playing` | Starting the first playable video embeds its player, and that player really plays (not paused, position advancing) | `functional` |
| 6–7 | `test_only_one_video_plays_at_a_time` | After the first video plays, starting a second one plays it too, while the first video's player is gone (its card offers "Play" again) and exactly one player is on the page | `functional` |

Training Videos facts observed on 2026-09-12: no `data-testid`; the page reuses the dashboard's `complementary` / `banner` / `main` landmarks. Each video is a Bootstrap card without a landmark or id, holding an `h6` title. A card whose video is available shows a YouTube thumbnail behind a button named `Play <video title>`; a card whose video is gone shows a "Video unavailable" placeholder and no button. Clicking a play button replaces that card's button with `<iframe title="<video title>" src="https://www.youtube.com/embed/<id>?autoplay=1">`, and the embed starts by itself in Chromium, Firefox and WebKit. **The application embeds at most one player:** starting a second video unmounts the first player and restores the first card's play button, which is what "only one video plays at a time" is asserted on. Different cards may point at the same YouTube video, so the player is identified by its `title` (the card's video title), never by the embed URL.

**Playback check:** `TrainingVideosPage.wait_until_playing(title)` reads the `video` element inside the embed (`paused`, `currentTime`) and returns only once the video is not paused *and* its position has advanced between two readings, so a loaded but frozen player does not pass. It gives up after 30 s with a Playwright `TimeoutError`, which fails the test with the usual screenshot and trace. These tests therefore need outbound access to `youtube.com`.

**Playback tests in CI (2026-09-22):** on GitHub-hosted runners YouTube replaces the embed with *"Sign in to confirm you're not a bot"* (the runners' datacenter IPs are flagged), so the player stays `paused=True, position=0` in every browser; this is not a headless or Linux issue (all three browsers play headless locally). **Update (2026-09-22): the `video_playback` job has been removed from the workflow.** There is no self-hosted runner, and on GitHub-hosted runners the tests fail with `Video 'VIKASH' did not play within 30000 ms (last state: PlaybackState(paused=True, position=0))`. `test_selected_video_starts_playing` and `test_only_one_video_plays_at_a_time` stay in the suite unchanged, and the `read_only` job still deselects them. **They run locally only:** `pytest tests/ui/test_training_videos.py`. To bring them back into CI, register a self-hosted runner and restore the job from git history.

## Manage Channel tests

`tests/ui/test_manage_channel.py` – page `/channels` (page object `ManageChannelPage`, locators `ManageChannelLocators`). All tests carry the `regression` marker and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run. The page is reached by clicking the **"Manage Channel" sidebar menu only**; no other menu entry is used.

### Page visibility (tests 1–13, `smoke`)

**Visibility only:** the existing channel rows and their values (channel name, token expiry, status, config date, cron time slot) are data and are not verified. **Nothing on the page is clicked** – no Add New, Help, Search, Reset, Edit, Delete, Re-auth, Product, Order, row expand, pagination or filter.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_manage_channel_page_opens_successfully` | The sidebar menu opens `/channels` and the page heading "Channel Connection" is visible |
| 2 | `test_page_header_elements_are_visible` | Breadcrumb area, Help button, "+ Add New" button |
| 3 | `test_filter_bar_is_visible` | Channel Name label and input, Connection label and dropdown, Search button, Reset button |
| 4 | `test_table_and_its_controls_are_visible` | "Show ... entries" dropdown, table container |
| 5–12 | `test_table_header_is_visible[<header>]` | One test per column header (parametrized): S.No, Channel Name, Token Expiry, Action, Manage Products, Manage Orders, Config Date, Cron Config Time Slot |
| 13 | `test_pagination_area_is_visible` | "Showing ... entries" count, pagination area, Previous button, current page indicator, Next button |

### "Add a new connection" popup (tests 14–27, `functional`)

Covers the part of the add-channel flow that stays **inside SHP**: opening the popup, the platform options, selecting eBay, the Channel Name field and leaving through Cancel. Fixture `connection_popup` opens the page and clicks "+ Add New".

**These tests create, change and delete no application data.** Next is pressed only with an **empty** channel name, which the popup rejects in the browser; it is never pressed with a valid name here, so no connection is started. The existing EBAY channel is only read, never edited or deleted. (Connecting a channel is covered by tests 28–29 below.)

| # | Test | Verifies |
|---|---|---|
| 14 | `test_add_new_opens_the_connection_popup` | "+ Add New" opens the popup: heading "Add a new connection", Next and Cancel buttons |
| 15–19 | `test_platform_option_is_visible[<platform>]` | One test per platform (parametrized): eBay, Shopify, Temu, Amazon, Walmart |
| 20–23 | `test_platform_that_is_not_released_cannot_be_selected[<platform>]` | Shopify, Temu, Amazon and Walmart are **disabled** ("Coming soon") |
| 24 | `test_ebay_platform_can_be_selected` | eBay can be chosen, becomes checked, and reveals an editable Channel Name field |
| 25 | `test_channel_name_field_accepts_the_test_value` | The field keeps the typed test value `AUTOMATION TEST CHANNEL` |
| 26 | `test_channel_name_is_required_to_continue` | Next without a channel name shows "Channel name is required", the popup stays open and the browser stays on `/channels` |
| 27 | `test_cancel_closes_the_popup_without_creating_a_channel` | Cancel closes the popup; no row named `AUTOMATION TEST CHANNEL` exists and the original EBAY row is still there |

**Popup facts observed on 2026-09-12:** the popup is **one step, not a wizard** – it opens showing only the Platform picker with Cancel / **Next**, and choosing a platform reveals the Channel Name field in the same popup. It is a Bootstrap modal **without `role="dialog"`**, so it is scoped by the CSS class `.modal.show`. Each platform is a `radio` wrapped in a label holding the platform name and logo, so the radio's accessible name matches the platform name. **Only eBay is enabled**; the other four radios carry `disabled` and a "Coming soon" badge. The Channel Name field has no linked label and the page's filter bar holds a second "Channel Name" textbox, so the popup's field is pinned to `input[name='channel_name']` (placeholder "e.g. My Store"). "Next" is also the name of the pagination button, so every popup button is scoped to the popup. Validation is client-side (the form has `novalidate`): Next with an empty name shows "Channel name is required" and sends nothing. The header's "×" button has no accessible name, so only Cancel is used to close the popup. Channel Name is a free display name: the recorded flow typed "Amazon" while eBay was selected, so it does **not** define the platform.

### Connect a channel and delete it again (tests 28–30, `functional`)

The rest of the journey: pressing Next with a valid channel name, authorising the
connection, returning to the page, and removing the created channel again. Fixture
`connected_channel` connects one channel per test under a **unique** name
(`AUTOMATION TEST CHANNEL <8 random hex characters>`), yields the page object showing
it, and deletes it afterwards if the test did not.

**These are the first tests that create application data.** Each creates exactly one
channel and removes it in the same test; both tests also assert that the account's real
`EBAY` channel is still present. No credentials of any kind are typed (see the sandbox
facts below).

| # | Test | Verifies |
|---|---|---|
| 28 | `test_sandbox_authorization_connects_the_new_channel` | The sandbox authorisation completes, the browser is back on `/channels` with the "Channel Connection" heading and the banner "eBay channel connected successfully.", the new channel's row is visible, and the `EBAY` row is untouched |
| 29 | `test_delete_removes_only_the_channel_the_test_created` | The row's Delete opens "Delete this channel?" with "Yes, delete"; confirming shows "Checking before we continue…" with the confirm button **disabled** during its countdown; the modal then becomes "Confirm once more" and "Delete permanently" removes the channel; the row is gone, the popup is closed, and the `EBAY` row is still there |

| 30 | `test_new_channel_appears_in_sidebar_submenus_until_deleted` | The new channel's row is visible; expanding the sidebar's **Active Listing** and then **Manage Order** shows a sub-menu link with the channel's exact name under each (the sub-menu pages are **not** opened); back through the "Manage Channel" sidebar menu, the channel is deleted through all three stages, its row is gone and the `EBAY` row is still there |

**Sidebar sub-menu facts observed on 2026-09-14:** "Active Listing" and "Manage Order" are sidebar buttons whose list item holds a nested list with **one link per connected channel**, named exactly after the channel (Manage Order also lists "All Orders" first). The menus behave as an **accordion** – expanding one collapses the other, and a collapsed entry's nested list is not in the accessibility tree – so `ManageChannelPage.expand_sidebar_menu()` clicks an entry only while its sub-menu is hidden. A new channel is already listed in the sidebar of the tab the sandbox authorisation returns to. Locators: `ManageChannelLocators.sidebar_submenu_button()`, `sidebar_submenu()`, `sidebar_submenu_channel()`; the menu names are `SIDEBAR_CHANNEL_MENUS`. Verified 1/1 on Chromium.

**Connect-flow facts observed on 2026-09-12:** Next posts to `POST /api/v1/channels/ebay/initiate`
and opens **a new browser tab** at `/api/v1/channels/ebay/dev-sandbox/authorize?...`. That page
is **SHP's own local dev sandbox, not eBay** – it is served by the application itself, is titled
"Sign in — eBay (Local Dev Sandbox)" and states "This is a local fake sign-in. No data leaves your
machine and no real eBay account is used. Any credentials are accepted." It also accepts the
**empty** form, so the automation only presses its "Sign in" button and types nothing; there is no
separate consent screen. The tab is then redirected to `/channels?connected=ebay&status=success&action=insert`
and immediately to `/channels`, where the banner and the new row appear. **The authorisation lands
in the new tab, not the original one** – the tab the connection was started from still shows the
table from before – so the tests continue on the page object returned by `authorize_in_sandbox()`.

**Delete-flow facts observed on 2026-09-12:** every row has a Delete button, so it is scoped to its
row by channel name. Delete is **one modal that walks through three stages**, not three modals: it
opens as "Delete this channel?" (Cancel / "Yes, delete"), becomes "Checking before we continue…"
with a disabled button named "Please wait 5s" counting down to "Please wait 1s", and then becomes
"Confirm once more" with the button enabled and renamed "Delete permanently". Pressing it sends
`DELETE /api/v1/channels/<id>`, closes the modal and reloads the table. Because the button's
accessible name changes, the final confirmation is located by the name "Delete permanently" alone –
no CSS class and no waiting is needed, the locator simply does not match until the countdown ends.

Manage Channel facts observed on 2026-09-12: the sidebar entry leads to `/channels`; no `data-testid`; the page reuses the dashboard's `complementary` / `banner` / `main` landmarks. "Channel Connection" is **two** headings – the page title (`h3`) and the card title (`h4`) – so the page heading is pinned to `level=3`. The Help and Add New buttons' accessible names start with an icon glyph, so they are matched as substrings. Filter labels are plain `label` elements not linked to their fields, so they are located by exact text, while the fields carry their own accessible name (placeholder `Channel Name`, `aria-label="Connection"` / `"Entries per page"`). Sortable column headers append a `⇅` glyph to their text, so headers are matched as substrings. The entry count line contains live numbers ("Showing 1 to 1 of 1 entries") and is matched with the regex `^Showing .+ entries$`. Previous and Next are **disabled** while a single page of channels exists – visibility only, so this does not matter. The current page number is marked with a CSS class and no `aria-current`.

**Viewport:** below 1600 px wide the page folds its last two columns ("Config Date", "Cron Config Time Slot") into expandable "+" rows and removes them from the DOM, replacing them with a "Show all columns" button. The tests therefore set the viewport to `ManageChannelPage.FULL_TABLE_VIEWPORT` (1600×900) before opening the page, so all eight headers are rendered. No other module changes the viewport.

## My Profile tests

`tests/ui/test_my_profile.py` – page `/profile` (page object `MyProfilePage`, locators `MyProfileLocators`). All tests carry the `regression` marker and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run. The page is reached the way a user reaches it: the **"My Account" sidebar menu, then its "My Profile" entry**; no other menu entry is used, and Billing is not opened.

### Visibility (tests 1–7, `smoke`)

**Visibility only.** Nothing is edited, uploaded, saved or submitted, and the eye icons are only checked to be present.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_my_profile_page_opens_successfully` | The sidebar leads to `/profile` and the "My Profile" heading is visible |
| 2–4 | `test_page_section_is_visible[<section>]` | One test per section (parametrized): Personal & Contact Information, Business & Address Information, Security |
| 5 | `test_personal_and_contact_information_fields_are_visible` | Avatar, Upload Photo, Full Name, Username, Email, Change Email, Mobile, Change Phone, Gender, Date of Birth |
| 6 | `test_business_and_address_information_fields_are_visible` | Company Name, Country, State, City, Timezone, Pincode, Address 1, Address 2, Description, Save Profile |
| 7 | `test_security_fields_are_visible` | Current Password + its eye icon, New Password + its eye icon, Confirm New Password + its eye icon, Change Password |

### Functionality (tests 8–21, `functional`)

Fields covered: Full Name, Username, Gender, Date of Birth, Company Name, Country, State, City, Timezone, Pincode, Address 1, Address 2, Description, Save Profile, and the Security card (Current / New / Confirm New Password, their eye icons, Change Password). **Not touched:** Change Email, Change Phone, their OTPs, Upload Photo, Billing. Most tests type or choose values **without saving**, so each test's fresh browser context discards them. Only tests 16, 20 and 21 write to the account, and each one restores the original value itself (see below).

| # | Test | Verifies |
|---|---|---|
| 8 | `test_username_field_is_read_only` | Username is **disabled** (read-only in the application); it is not force-edited |
| 9–13 | `test_text_field_accepts_valid_text[<field>]` | Full Name, Company Name, Address 1, Address 2 and Description each keep the typed text `SHP Automation Test` (not saved) |
| 14 | `test_gender_option_can_be_selected` | The Gender dropdown's options load and an option other than the current one can be chosen and stays selected (not saved) |
| 15 | `test_date_of_birth_accepts_a_valid_date` | Date of Birth keeps the valid date `1990-05-15` (not saved) |
| 16 | `test_full_name_rejects_numeric_only_value` | Saving the numeric-only name `12345` is **not accepted by the server**, and after a reload Full Name still holds its original value. If the server ever accepts it, the test fails and saves the original name back |
| 17 | `test_country_state_city_dependency` | Choosing a country other than the saved one (the first of up to 10 the application has states for) loads `GET /api/v1/profile/states?country_id=<id>`. State resets to "Select", the State list becomes **exactly** the states that request returned, and City empties. Choosing a state (the first with cities) loads `GET /api/v1/profile/cities?state_id=<id>`, and the City list becomes exactly those cities. A city can then be selected. Countries and states are taken from the application, not hard-coded (not saved) |
| 18 | `test_timezone_option_can_be_selected` | The Timezone dropdown's options load and another option can be selected (not saved) |
| 19 | `test_pincode_accepts_a_valid_postal_code` | Pincode keeps the postal code the application itself suggests for the profile's country (its placeholder `e.g. <example>`), and no "Enter a valid postal code" message appears (not saved) |
| 20 | `test_save_profile_persists_the_change` | Only **Company Name** is changed, to `SHP Automation Test Company`. Save Profile gets `status: true` and shows the toast "Profile updated successfully.", and the value is still there after a reload. The original company name is then saved back, and a reload confirms it |
| 21 | `test_change_password_and_restore_original` | Current Password (from `.env`) plus the temporary password `tester1` in New and Confirm New Password. Each eye icon reveals its own field (`type="text"`, "Hide password") and masks it again ("Show password"). Change Password gets `status: true` and the toast "Password changed successfully.". The password is then **immediately changed back** (current = temporary, new = the `.env` password), and that restore must also get `status: true`. The restore is also the proof that the temporary password was really set, so no extra sign-in is made |

**Data safety.** Tests 16 and 20 capture the original value before changing it. In a `finally` block they reload and, if the saved value differs, save the original back. The password test puts the restore in a `finally` block that runs whenever the first change was confirmed, so a failing check after that change still restores the password first. If the restore itself fails, the test fails with `PASSWORD NOT RESTORED` and the server's message. No wrong current password, invalid password or repeated attempt is ever submitted, because the account may be deactivated after wrong passwords.

**Passwords.** They come from `Credentials` (`.env`) and are typed with `fill_secret()`, so their values are never logged. `MyProfilePage.handling_passwords()` stops tracing for the whole password flow, because traces record typed text and the request bodies, and it empties the three password fields when the flow ends, so a failure screenshot cannot show one. Assertions never compare password values, only attributes and server answers. Verified 2026-09-14: neither password appears in any file under `reports/` or `test-results/`.

My Profile facts observed on 2026-09-12: the sidebar's "My Account" is a button that expands a sub-menu holding the links "My Profile" (`/profile`) and "Billing"; no `data-testid`; the page reuses the dashboard's `complementary` / `banner` / `main` landmarks. "My Profile" is both the page heading (`h5`) and the last breadcrumb entry, so the heading is pinned to the heading role at level 5; the three section titles are `h6`. **The form fields have no accessible name whatsoever** – every `<label>` is unlinked (no `for`/`id`) and the controls carry no `name`, `id`, `placeholder` or `aria-label` – except the three password fields, which have placeholders. Each field is therefore found through its label's text (see D37). Username is `disabled`; Email and Mobile are `readonly` and change through their "Change Email" / "Change Phone" buttons next to them. Date of Birth is a native `input[type="date"]`, so the field and its calendar are one control. "Upload Photo" is a `<label>` wrapping a hidden file input, not a button, so it is matched by its text. The avatar is a circle holding the account's initial, named by `aria-label` ("No profile photo" while the account has none). The Save Profile and Change Password button names start with an icon glyph, so they are matched as substrings. All three eye buttons are named "Show password", so each is taken from its own password field.

My Profile functionality facts observed on 2026-09-14, from the live page and its front-end code, with every write request blocked during inspection except one Save with all values unchanged:
- **Endpoints.** The form loads `GET /api/v1/profile`. States and cities are loaded per selection from `GET /api/v1/profile/states?country_id=<id>` and `GET /api/v1/profile/cities?state_id=<id>` (answer `{"status", "message", "data": {"states"|"cities": [{"id", "name"}]}}`), and choosing the country that is already selected sends no request. Save Profile posts the whole form as `multipart/form-data` to `POST /api/v1/profile`. Change Password posts `old_password` and `new_password` to `POST /api/v1/profile/password`.
- **Dropdowns.** Their options are filled in after the field renders, so `MyProfilePage.selectable_values()` waits for the first real option. Changing the country resets State and City.
- **Client-side checks.** Save Profile checks only that Full Name is not empty, that a country is selected, and the pincode format of that country. Full Name has `maxlength="30"` and **no client-side numeric check**, so a numeric-only name is sent and rejected by the server. Address 1 and Address 2 have `maxlength="50"`.
- **Pincode.** The placeholder shows the application's example for the chosen country (`e.g. <example>`), and a value that does not match the country's format shows "Enter a valid postal code for <country>. Example: …".
- **Change Password.** The client requires the new password to have ≥ 6 characters with a letter and a digit, and to match its confirmation. On success it shows "Password changed successfully." and empties the three fields, and the user stays signed in.
- **Toasts.** Both success messages are toasts with role `status`, rendered outside `main`.

## Billing tests

`tests/ui/test_billing.py` – My Account → Billing (page object `BillingPage`, locators `BillingLocators`). All tests carry the `smoke` and `regression` markers and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run. The page is reached through the **"My Account" sidebar menu, then its "Billing" entry**. The fixture widens the viewport to 1600×900 first, like Manage Channel (D26).

**Visibility only.** No billing value is checked (plan names, amounts, statuses, dates, payment methods, invoices). Nothing on the page is clicked: no Invoice, sorting, Show entries, pagination or payment action.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_billing_page_opens_successfully` | "Billing" heading |
| 2 | `test_current_plan_section_is_visible` | "Current Plan" label and its section, the current plan name, amount and status/date area |
| 3 | `test_table_and_its_controls_are_visible` | "Show ... entries" control, billing table |
| 4–11 | `test_table_header_is_visible[<header>]` | One test per column header (parametrized): S.No, Plan, Amount, Status, Invoice, Payment Method, Period Start, Period End |
| 12 | `test_pagination_area_is_visible` | Pagination area, Previous button, current page indicator, Next button |

**Status: written, not yet run, and the locators are not verified against the live DOM.** They were written from the Billing screenshot and the patterns verified on the other pages:
- The Show entries control (`combobox` "Entries per page"), the pagination (`navigation` "Pagination", `li.active`, D28) and the column headers (`columnheader`, substring match) assume the same table component as Manage Channel.
- The heading is taken as the first `heading` named "Billing" in `main`.
- The current plan values are located without their values. The section is the innermost block holding the "Current Plan" heading and an amount. The amount is the first text shaped like a currency amount. The status/date area is the first text shaped like a date.
- **Fixed 2026-09-14 from the first run's failure report (page snapshot):** the label is an h6 heading reading "Current Plan (billed)", so the exact text "Current Plan" did not match. It is now matched as an h6 heading whose name starts with "Current Plan". The plan name is the section's h4 heading. **Second fix, same day:** the section locator filtered blocks by `has=` a heading locator that was itself scoped to `main`. Playwright searches a `has` locator *inside* each candidate block, and no block contains `main`, so nothing matched. The inner heading locator is now built from the page, as `channel_row()` does on Manage Channel. The snapshot also confirmed the "Billing" h3 heading, the "Entries per page" combobox, the table and the eight column headers (sortable ones end with "⇅" or "▼", matched as substrings).
- `BillingPage` has no `PATH`, because the route is not known yet, so the tests do not assert the URL.

If a test fails on its first run, re-check that locator against the live page.

## Help Center tests

`tests/ui/test_help_center.py` – page `/help-center` (page object `HelpCenterPage`, locators `HelpCenterLocators`). All tests carry the `regression` marker and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run. The page is reached by clicking the **"Help Center" sidebar menu only**. The fixture widens the viewport to 1600×900 first, like Manage Channel (D26).

### Visibility (tests 1–14, `smoke`)

**Visibility only.** No case data is checked, and nothing on the page is clicked. These tests are unchanged in Step 13, except that `smoke` moved from the module to each of them, so the functional tests are not smoke.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_help_center_page_opens_successfully` | "Help Center" heading |
| 2 | `test_page_header_elements_are_visible` | Breadcrumb area, "+ Raise New Case" button |
| 3 | `test_filter_bar_is_visible` | Search label and input, Priority dropdown, Status dropdown, Date Range field, Search button, Reset button |
| 4 | `test_table_and_its_controls_are_visible` | "Show ... entries" control, Help Center table |
| 5–13 | `test_table_header_is_visible[<header>]` | One test per column header (parametrized): S.No, Case Id, Description, File, Priority, Status, Position, Chat, Action, Date & Time (Position added 2026-09-22, see D38) |
| 14 | `test_pagination_area_is_visible` | "Showing ... entries" text, pagination area, Previous button, current page number, Next button |

Help Center facts observed on 2026-09-14 (from the first run's failure snapshot): the sidebar entry is a link to `/help-center`; the heading is an `h5`. The search input is named by its placeholder "Case ID / Subject / Description" and the Date Range field by "Choose date range". **The Priority, Status and Show entries dropdowns have no accessible name** (no `aria-label`, unlike Manage Channel's "Entries per page"), and their labels are unlinked. Each is therefore taken as the first `select` after its label text (the D37 pattern). "Search", "Priority" and "Status" also name a button or column header, so the filter labels are matched on `label` elements only. Previous and Next are disabled while one page of cases exists (visibility only). The current page number uses `li.active` (D28).

### Functionality (tests 15–25, `functional`) – Step 13

**Test data.** The functional tests raise **one automation case per browser per run**. Its subject is `AUTOMATION TEST CASE <8 random hex characters>`, its description is `Automation test case description <same hex>`, and its priority is High. The module-scoped `_automation_cases` cache keeps that case, and the `automation_case` fixture hands it to every dependent test. **The cache depends on the clean-up fixture (`created_cases`), so both are set up and torn down together.** Pytest groups parametrized items by parameter, so in a cross-browser run a test of another browser can run between this module's tests (e.g. `test_search_by_text_returns_the_case[firefox-subject]` between the WebKit tests). `created_cases` depends on `browser_name`, so that browser switch tears it down and its clean-up deletes the case. The cache is torn down with it, and the next test raises a fresh case instead of reusing the deleted one. Before this was fixed, the priority, status, date range, combined filter, reset and chat tests of the interrupted browser failed with "Locator expected to be visible" / "expected to have text 'Active'" (seen on Firefox and WebKit, 2026-09-16). Test 15 raises the case and fills the cache. A test run on its own gets the case raised by the fixture. **If raising the case fails, every dependent test errors with "Blocked: raising the automation case failed earlier in this run."** It never falls back to other cases. The Case Id is read from the list, never hard-coded. The only chat message is sent to the automation case. Since Step 14, this case is also registered for automatic clean-up and deleted after the module (see below).

| # | Test | Verifies |
|---|---|---|
| 15 | `test_raise_new_case_creates_a_listed_case` | "+ Raise New Case" opens the "Raise New Case" modal. Priority, Subject, Description, Raise Case and Cancel are visible and enabled. Raising the case shows the toast "Case raised successfully.", closes the modal, and lists exactly one row with the case's description, priority High, status Active and a Case Id |
| 16 | `test_search_by_case_id_returns_the_case` | Search by the case's Case Id: every listed Case Id equals it, and the case is listed |
| 17–18 | `test_search_by_text_returns_the_case[subject\|description]` | Search by the unique subject, then by the description: every listed row is the automation case |
| 19 | `test_priority_filter_shows_only_the_selected_priority` | Priority "High": every listed priority is High, and the case is listed |
| 20 | `test_status_filter_shows_the_selected_status` | Status "Inactive": the Active case is hidden and every listed status is Inactive. Status "Active": the case is listed as Active and no Inactive case is listed |
| 21 | `test_date_range_filter_shows_cases_in_the_range` | Picking today in the Date Range calendar sets the field to `dd-mm-yyyy`. Every listed Date & Time falls on today, and the case is listed |
| 22 | `test_combined_filters_return_only_matching_cases` | Search (subject) + Priority High + Status Active + today, all at once: every listed row satisfies all four, and the case is listed |
| 23 | `test_reset_restores_default_filters_and_list` | After those four filters, Reset empties Search and Date Range, sets Priority and Status back to "All" (value `""`), restores the unfiltered "Showing … entries" text, and lists the case again |
| 24 | `test_chat_on_active_case_sends_a_message` | For the automation case (found by its Case Id), Chat is enabled and opens its thread, headed "Case <id>". The reply box and Send are enabled, and `Automation test message` appears in the thread after sending |
| 25 | `test_closed_case_chat_cannot_receive_replies` | For the first listed case whose Status reads "Closed" (existing data, read only), Chat opens a thread headed "Case <id>" and "Closed". The thread shows "This case is closed and can no longer receive replies." and has **no reply box and no Send button**. Nothing is typed or sent. The test skips if the first page has no Closed case |

**Filter assertions.** Data is dynamic, so no test counts rows. Each filter test asserts that no listed row's cell breaks the filter (`column_cells(<header>).filter(has_not_text=…)` has count 0) and that the automation case is listed. The zero-count check keeps retrying until the rows the filter excludes have gone. `apply_filters()` and `reset_filters()` also wait for the case list request (`GET /api/v1/help-center?…`).

Help Center functionality facts observed on 2026-09-14 (live page and its API; the inspection raised one automation case and sent one message to it):
- **Raise New Case** is a Bootstrap modal without a dialog role (`.modal.show`, D29), with the heading "Raise New Case" (`h5`). It holds Priority (Low / Urgent / Medium / High), Subject * (`maxlength` 60), Description * (`maxlength` 250), CC Mail and an Attachment (image), plus Cancel and Raise Case. Its labels are unlinked, so each field is the first control after its label (D37 pattern). Raise Case posts `multipart/form-data` (`subject`, `description`, `priority`, `cc_mail`) to `POST /api/v1/help-center`, which answers `{"status": true, "message": "Case raised successfully.", "data": {"id", "case_id"}}`. The toast has role `status` and is rendered outside `main`. The list then reloads with the new case at the top, as Active.
- **The list shows the Description, not the Subject.** Rows are therefore found by the unique description. The Search field still matches Case Id, Subject and Description.
- **Filters apply only when Search is pressed.** Each sends `GET /api/v1/help-center?page_no=1&no_of_rows=10` plus `search=`, `filter_priority=` (0 Low, 1 Urgent, 2 Medium, 3 High), `filter_status=` (1 Active, 0 Inactive) and `filter_date_from=` / `filter_date_to=` (`yyyy-mm-dd`). Reset clears every field and reloads the unfiltered list. An empty result shows one row, "No cases found.".
- **Date Range** is a flatpickr range picker. The visible field is read-only. Its calendar is appended outside the page and marked open only by the class `.flatpickr-calendar.open` (D39). Each day carries an `aria-label` like "September 14, 2026". Clicking the same day twice selects that one day and closes the calendar, and the field then shows `14-09-2026`.
- **Chat** is a button in each row whose name starts with an icon glyph, so it is matched as a substring. It opens a modal headed `Case <case id>` plus a status badge, loads `GET /api/v1/help-center/<id>/comments`, and for an open case offers a "Write a reply…" box and Send. Send posts `comment` to `POST /api/v1/help-center/<id>/comments` ("Comment posted."), and the thread reloads showing the message.
- **Closed cases:** the row's Chat button is **not disabled**. It opens the thread read-only: the comments answer has `is_closed: true`, `can_reply: false` and a `lock_reason`. The footer shows "This case is closed and can no longer receive replies." in place of the reply box and Send, so the application enforces the rule by offering no way to reply at all. Closed cases also have no Edit/Delete actions.
- **Status filter vs. Closed:** the Status filter offers only All / Active / Inactive. A Closed case has API `status: 1` (the value behind "Active") with `ticket_position: "Closed"`, so **filtering by "Active" also lists Closed cases**, whose Status column reads "Closed". Test 20 therefore asserts only that Inactive cases are excluded. **Whether Closed cases should be excluded is not defined – open question for the product owner.**

Decisions (Help Center):
- **D38** – Row cells have no name of their own. A column's cells are therefore located by position (`td:nth-child(n)`), where `n` comes from `COLUMN_HEADERS`, the header order verified by tests 5–13. This is the one documented positional selector.
  - **Fix (2026-09-22):** the page added a **Position** column (e.g. "Pending") between Status and Chat, but `COLUMN_HEADERS` still listed 9 headers. Every column after Status was therefore shifted by one: "Date & Time" resolved to `td:nth-child(9)`, which is now the Action cell (Edit/Delete icons, no text), so `has_not_text=^dd-mm-yyyy ` always matched one row. Only tests 21 and 22 failed, because they are the only filter tests that assert a column after Status (Search, Priority and Status sit before it). The date picker, the `dd-mm-yyyy` format, the one-day range and the Search wait were all correct. Fix: `"Position"` added to `COLUMN_HEADERS` in `framework/locators/help_center_locators.py`, between "Status" and "Chat". This also adds `test_table_header_is_visible[Position]`.
- **D39** – The open Date Range calendar is located by the CSS class `.flatpickr-calendar.open`, like the modal (D29). Flatpickr renders it outside the page with no role, id or name, and only the open calendar carries `open`. Days inside it are then located by their `aria-label`.
- **Fix (2026-09-22) – intermittent failures on a slow server.** Two symptoms that come and go: (1) `Page.goto: Timeout 30000ms exceeded` errors while a test was being set up; (2) `test_table_header_is_visible[<header>]` failing with "Locator expected to be visible" on a different header each run (Status, Action). Cause: the test server is slow. Its own JS bundle (`/assets/index-*.js`) took 1.8 s on one load and 6.2 s on the next. A single header check took 10–23 s, and when the server spikes, navigation passes the 30 s default. Also, `open_from_sidebar()` only clicked the menu entry, so the 5 s `expect` started before the case list had loaded. Fixes: `HelpCenterPage.open_from_sidebar()` now waits for the case list request (`GET /api/v1/help-center?…`), the same wait `apply_filters()` uses; `authenticated_page` in `tests/conftest.py` sets a 60 s navigation timeout (`NAVIGATION_TIMEOUT_MS`). No sleeps were added, and assertions and `expect` timeouts are unchanged. Result: 27 passed, 1 skipped (no Closed case on page 1).

Limitations (Help Center):
- ~~**Cases accumulate.**~~ **Resolved in Step 14:** every case a run raises is now deleted after the module (see "Edit, Delete and clean-up"). The 5 cases left by Step 13 runs, from before clean-up existed, are still in the account (see the blocker there).
- Test 25 depends on existing data: a Closed case on the first page of the list. It cannot create one (closing is not a user action here), so it skips when none is shown.
- Tests 21–23 select today's date on the machine running them, and the browser shows dates in that machine's time zone. The server stores UTC, and it is not known which zone its date filter uses. A run between midnight and the UTC offset (00:00–05:30 IST) could therefore miss the case; this has not been observed.
- The Status filter question above; also, with no Inactive cases in the account, test 20's "every listed status is Inactive" is checked against an empty list.
- Copy changes to "Case raised successfully.", "This case is closed and can no longer receive replies.", "Write a reply…", the "Raise New Case" heading or the modal labels break the matching locators.

**Result:** 25/25 on Chromium (2026-09-14): 14 visibility and 11 functional items. The first run failed tests 24 and 25 because the Chat button's name starts with an icon glyph. After the substring-match fix, the whole module passed. Not yet run on Firefox or WebKit.

**Files (Step 13):** modified `framework/locators/help_center_locators.py`, `framework/pages/help_center_page.py`, `tests/ui/test_help_center.py`, `README.md` (this section only). Created: none.

### Edit, Delete and clean-up (tests 26–27, `functional`) – Step 14

Tests 1–25 are unchanged. The edit and delete tests each raise a **fresh automation case of their own** (same subject/description convention and priority High as test 15). They never touch the shared case or any other case.

| # | Test | Verifies |
|---|---|---|
| 26 | `test_edit_case_updates_priority_and_description` | The case's Edit (found by its Case Id) opens the "Edit Case" modal, prefilled with the case's Subject, Description and Priority High. Changing Priority to Medium and Description to `<description> edited` (the unique tag stays), then pressing Update, shows the toast "Case updated successfully." and closes the modal. The row then shows the new Description, Priority Medium and Status Active, and still does after a fresh search by Case Id (reloaded from the server). Subject is left unchanged |
| 27 | `test_delete_case_removes_it_from_the_list` | The case is searched for by Case Id and identified by **Case Id and unique description together** (never by position). Its Delete opens "Delete this case?" with "Delete case <id>? This cannot be undone.". Delete shows the toast "Case deleted successfully.", closes the modal and removes the row. Searching by the description and then by the Case Id shows "No cases found." and no row for the case |

**Automatic clean-up.** The module-scoped `created_cases` fixture tracks, per browser, every case the module raises (description → Case Id).
- Every raise registers its description **before** the case is submitted: test 15, the shared `automation_case` fixture, and tests 26–27. The Case Id is added once it is read from the list, so a case whose confirmation failed can still be cleaned up by its description.
- Test 27 removes its case from the tracker only after it has verified the deletion.
- After the module's last test, the fixture's teardown runs **whether the tests passed or failed**. It opens a fresh context with the stored signed-in session, opens the Help Center from the sidebar and calls `HelpCenterPage.delete_automation_case()` for every tracked case.
- That method searches by Case Id, or by description when the Id is unknown. It deletes only a row matching both, and proves the deletion by the row disappearing. A case that is no longer listed (e.g. already deleted) is logged and skipped.
- Every case is attempted, even after one fails. A case that cannot be deleted is logged and reported as a teardown **ERROR** naming its Case Id and description. The ERROR is reported next to any test failure and never replaces it.
- **Safety:** `delete_automation_case()` raises `ValueError` for any description not starting with `Automation test case description ` (`HelpCenterPage.AUTOMATION_CASE_DESCRIPTION_PREFIX`), and `RuntimeError` when the search does not single out one case. Manual cases cannot be deleted by a test or by the clean-up.
- **Result:** a full Help Center run leaves **no automation case of its own behind**. A full run raises 4 cases per browser: the shared case, the edit and delete cases, and a fresh shared case for the `[description]` search, which runs after the module's clean-up (see Test data). Test 27 deletes one case, and the two clean-ups delete the other three.

Help Center Edit/Delete facts observed on 2026-09-14 (live page and its API; the inspection raised one automation case, edited it and deleted it):
- Active cases have two icon buttons in the Action cell, `title="Edit"` and `title="Delete"`. **Their accessible name comes from the icon glyph, not the title**, so role + name does not match them; they are located by title (`get_by_title`). Closed cases have no actions.
- Edit opens a Bootstrap modal (`.modal.show`, D29) headed "Edit Case", with the same fields as Raise New Case plus Cancel and Update. **The form fills itself asynchronously** from `GET /api/v1/help-center/<id>`, so `open_edit_form()` waits for that response and the test asserts the prefilled values before changing anything. Filling too early leaves the fields empty and Update answers "Subject and description are required.". Update sends `PUT /api/v1/help-center/<id>` (`multipart/form-data`: `subject`, `description`, `priority`, `cc_mail`), answered with "Case updated successfully.", and the list reloads.
- Delete opens a small modal (`.modal.show`) headed "Delete this case?" (`h6`) with "Delete case <case id>? This cannot be undone.", Cancel and Delete. Delete sends `DELETE /api/v1/help-center/<id>` ("Case deleted successfully.") and the list reloads.
- **Search sends no request when its text is unchanged**, so a repeated search with the same text must not wait for the list request. Toasts of earlier actions can still be on screen, so two identical toasts may exist at once.

Decision (Help Center):
- **D40** – Help Center clean-up uses a **module-scoped tracker with a teardown in a fresh context**, rather than a per-test finalizer. The shared case is used by many tests and may only be deleted after the last one. A fresh context also works when a test failed with a modal still open. Deletion is guarded by the automation description prefix, like D33 for channels.

Limitations (Step 14):
- If the run is killed (not merely failing), the teardown does not run, and that run's `AUTOMATION TEST CASE <hex>` cases remain; delete them by hand.
- The clean-up needs the stored signed-in session. If sign-in never succeeded, no case was raised, so there is nothing to clean up.
- Copy changes to "Edit Case", "Update", "Delete this case?", the confirmation sentence, the two toasts or "No cases found." break the matching locators.
- **Existing flake in test 25 (not changed):** in the second run it skipped with "No case with Status 'Closed' on the first page" although the Closed case exists. The Status badges render shortly after the first Case Id cell, and test 25 counts the Closed rows once without retrying. A read-only check showed 0 Closed rows at that moment and 1 three seconds later. Fixing it was outside this task.

**Result:** Chromium, 2026-09-14.
- **First run: 25 passed, 1 failed, 1 error.** Test 27 waited for a list request that a repeated identical search never sends. The clean-up teardown reported one case because two identical delete toasts broke a strict toast check; that case had in fact been deleted. Both are fixed: the search order changed, and the clean-up now checks that the row is gone.
- **Second run: 26 passed, 1 skipped** (test 25, the flake above). All 27 Help Center items pass except the flaky test 25. The clean-up logged "Clean-up deleted every automation case of this run (2)".
- A read-only search afterwards found **no case from Step 14 runs**. Not run on Firefox or WebKit.

**Blocker / open item:** the **5 automation cases left by Step 13 runs**, created before clean-up existed, are still in the account: 09140753504, 09140750016, 09140735493, 09140732513, 09140725297 (all `Automation test case description <hex>`). They are not tracked by any run, so the clean-up does not touch them. Deleting them needs approval.

**Files (Step 14):** modified `framework/locators/help_center_locators.py`, `framework/pages/help_center_page.py`, `tests/ui/test_help_center.py`, `README.md` (Help Center section only). Created: none.

## Customer tests

`tests/ui/test_customer.py` – Customer page (page object `CustomerPage`, locators `CustomerLocators`). Run with `pytest tests/ui/test_customer.py`. All tests carry the `smoke` and `regression` markers and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run. The page is reached by clicking the **"Customer" sidebar menu only**. The fixture widens the viewport to 1600×900 first, like Manage Channel (D26).

**Visibility only.** No customer data is checked. Nothing on the page is clicked: no Search, Reset, Export, Date Range, Channel filter, sorting or Show entries. No data is changed.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_customer_page_opens_successfully` | "Customer" heading |
| 2 | `test_page_header_elements_are_visible` | Breadcrumb area, Export button, access-logging notice |
| 3 | `test_filter_bar_is_visible` | Customer Name label and input, Order Id label and input, Date Range field, Channel dropdown, Search button, Reset button, the "select From & To date to enable Export" hint |
| 4 | `test_table_and_its_controls_are_visible` | "Show ... entries" control, customer table |
| 5–18 | `test_table_header_is_visible[<header>]` | One test per column header (parametrized): S.No, Channel, Order ID, Buyer User ID, Name, Street 1, Street 2, State/Province, Country, Phone, Postal Code, Address ID, Address Owner, Created |
| 19 | `test_empty_state_message_is_visible_when_no_customers` | Once the table has finished loading, the empty-state message row is visible. It skips when the first row is a data row (more than one cell) |

Locator notes (written from the screenshot and the Help Center patterns, then confirmed by the live run):
- Filter labels are matched on `label` elements only ("Channel" also names a column header). Each field is the first `input` / `select` after its label (D37 pattern). The Date Range field is named by its placeholder "Choose date range", and Show entries is the first `select` after the text "Show".
- The access-logging notice and the Export hint are matched by their subject (`access … log`, `From … To … Export`), not their exact wording. The empty-state row is matched as text starting with "No" and containing found / available / data / records.
- Column headers are matched from the start of the name, ignoring a leading or trailing glyph, so "Name" cannot match another header. A "/" in the name is escaped, because Playwright's selector parser ends a regex at an unescaped "/" (this broke State/Province on the first run).
- `CustomerPage` has no `PATH`, because the route is not verified, so the tests do not assert the URL.

**Result:** Chromium, 2026-09-14.
- First run: 17 passed, 1 failed (State/Province regex), 1 skipped. The empty-state test counted rows before they had rendered.
- After both fixes: the module passed with 18 passed and 1 skipped, and the reworked empty-state test then passed on its own (the account has no customers).
- Not run on Firefox or WebKit.

**Files (Step 15):** created `framework/locators/customer_locators.py`, `framework/pages/customer_page.py`, `tests/ui/test_customer.py`. Modified: `README.md` (this section only).

## Upgrade Plan tests

`tests/ui/test_upgrade_plan.py` – Upgrade Plan page (page object `UpgradePlanPage`, locators `UpgradePlanLocators`). Run with `pytest tests/ui/test_upgrade_plan.py`. All tests carry the `smoke` and `regression` markers and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run. The page is reached by clicking the **"Upgrade Plan" sidebar menu only**.

**Visibility only.** No price, limit, usage value, subscription date, plan name or plan state is checked. Nothing on the page is clicked: no Upgrade, Downgrade, Current Plan, Manage Auto-Pay, info icon or Cancel subscription. No data is changed.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_page_header_is_visible` | "Upgrade Plan" heading, breadcrumb area |
| 2 | `test_subscription_summary_is_visible` | Subscription status and Auto-Pay status items (each label with its value), the renewal item under whichever label the plan state gives it, Manage Auto-Pay button |
| 3 | `test_current_usage_section_is_visible` | "Current Usage" heading, the usage tiles section |
| 4–13 | `test_usage_tile_is_visible[<label>]` | One test per usage tile (parametrized): No of Staff, No of Folder Allowed, Image Memory Uses, No Of Images, No of Draft Product, No of SKU Allowed, No of Warehouse, No of Channel, No of Setup, Max Report |
| 14 | `test_every_rendered_plan_card_is_visible` | Plans section; at least one plan card; for **every rendered card**: the card, plan name, price/billing period, feature list and its first item, and the action/status button where the card has one |

**Dynamic plan cards.** The available plans, the current plan, names, prices, limits and the Upgrade / Downgrade / Current Plan state change, so none of them is hard-coded, and neither is the number of plans. The test discovers the cards at run time and checks the structure they share, so it keeps working when plans are added, removed, renamed or reordered, or when the current plan changes. This was confirmed during inspection: the screenshot showed 6 plans with Gold current, while the live page on the same day showed 10 plans with Silver current.

Upgrade Plan facts observed on 2026-09-15 (one read-only inspection; only the sidebar entry was clicked):
- The heading is an `h5`, and the breadcrumb is `navigation "breadcrumb"`.
- **Subscription summary.** Each item is a `span` holding a label span ("Subscription:", "Auto-Pay:", and the renewal label) and a value span. **The third label is dynamic:** the application renders `Renews on:` while the subscription has a renewal date and `Active until:` while it has none (`renews_on ? "Renews on:" : "Active until:"` in its own code). It was hardcoded as "Active until:" when these tests were written (2026-09-15, Auto-Pay Off) and failed on 2026-09-24 once the account's subscription renewed on Oct 12, 2026; `renewal_item()` now matches either label and the test checks that exactly one of them is there. The label's own span also matches a `has` filter, so an item is the span that holds its label **and** text after it. "Manage Auto-Pay" is a **link** styled as a button, and its name starts with an icon glyph.
- **Current Usage** is a card with an `h6` heading and one tile per usage label. The labels are unnamed spans, matched by exact text inside the section. The section is the innermost block holding the heading and both the first and last tile label.
- **Plan cards have no role, id or name.** Each card holds an `h5` plan name, an info button (`aria-label` "View full details of the <plan> plan"), the price as two spans ("$ 5" and "/ day"), a feature `list`, and one action button: Upgrade, Downgrade or a disabled "Current Plan". The current card also shows a "Current" badge.
- A card is therefore located as the **innermost block holding an `h5` heading, a list and text shaped like a price** (`<currency> <number> / <period>`). The price is required because the page title (`h5`) and the breadcrumb (a list) share a block. The plans section is the outermost block holding a card but not the Current Usage heading. The action button is the card's button with letters in its text, which leaves out the text-less info button.

**Result:** Chromium, 2026-09-15.
- **First run: 12 passed, 2 failed.** The Subscription item matched its own label span as well (strict mode). The first "card" was the page-title/breadcrumb block. Both locators were fixed as described above.
- **Second run: 14/14 passed.**
- Not run on Firefox or WebKit.

**Files (Step 17):** created `framework/locators/upgrade_plan_locators.py`, `framework/pages/upgrade_plan_page.py`, `tests/ui/test_upgrade_plan.py`. Modified: `README.md` (this section only).

### Downgrade and upgrade back (test 15, `functional`) – Step 18

`test_downgrade_then_upgrade_back_to_the_original_plan` **changes the account's plan and restores it**. Module markers are now `regression` for the whole module, `smoke` on tests 1–14 (Help Center pattern), and `functional` on test 15. Tests 1–14 are otherwise unchanged. Run it alone with `pytest "tests/ui/test_upgrade_plan.py::test_downgrade_then_upgrade_back_to_the_original_plan"`.

| Phase | What happens / is verified |
|---|---|
| Capture | Original plan (the card whose button is the disabled "Current Plan"), its card features, the Auto-Pay summary value and every Current Usage tile |
| Downgrade | Target: the nearest lower plan (Downgrade cards, cheapest first, walked from the current plan down). The target's card must list a numeric or ∞ limit for every mapped usage module. Its Plan Comparison checks must all pass; if one fails, the dialog is closed and the next plan is tried. Flow: **Downgrade → Plan Comparison "Proceed" → "Downgrade to <plan>" checkout → "Confirm Downgrade"** (no charge; account credit) |
| After downgrade | Target is the current plan; Current Usage matches its limits and differs from before; Auto-Pay unchanged |
| Upgrade back | Original plan's **Upgrade → "Upgrade to <plan>" checkout → confirm**. The button reads "Confirm Upgrade" when account credit covers the charge, otherwise "Pay <amount> & Upgrade" (saved Stripe test card) |
| After upgrade | Original plan is current again; Current Usage matches its limits; Auto-Pay unchanged |
| Restoration (`finally`) | Always runs: reloads the page and, if the original plan is not current, changes back to it and waits. It fails loudly with `RESTORE FAILED` when that does not work |

**Auto-Pay handling.** Both checkout dialogs have a "Turn on Auto-Pay" checkbox. It is set to match the original Auto-Pay state before confirming (original Off → unchecked), and the summary value is checked after each change. So Auto-Pay is never changed, and no Billing-page Auto-Pay action is used.

**Current Usage verification.** A tile's limit is compared with the plan card feature it maps to (`USAGE_PLAN_FEATURES`): Staff, Draft Products, Warehouses, Channels, Setups, Reports. A number N must appear as `/ N`, and ∞ as "Unlimited". Folder Allowed, Image Memory, Images and SKU Allowed have no card feature, so the test only checks that they still show a value. The limits "take effect shortly after you confirm", so the page is reloaded until the plan and usage match (up to 120 s).

Facts observed on 2026-09-15:
- The dialogs are Bootstrap modals (`.modal.show`) without a dialog role.
- Plan Comparison marks each module with a `bi-check-circle-fill` icon when the account meets the lower plan.
- Stripe runs in Test mode with the saved card Visa •••• 4242.

**Result:** Chromium, 2026-09-15. Silver was current at the start, Auto-Pay was Off, and Gold was chosen as the downgrade target.
- **First run: 14 passed, 1 failed.** The downgrade to Gold succeeded and Current Usage updated (e.g. Staff 1/10 → 1/2, Max Report 0/5 → 0/2). The upgrade back timed out because the confirm button read "Confirm Upgrade", which the locator did not match. The account was left on Gold, and Silver was restored straight away by a one-off script (Auto-Pay stayed Off; usage matched the original). The locator was then fixed.
- **Second run (test 15 alone): passed.** Downgrade to Gold, Current Usage updated; upgrade back to Silver, Current Usage restored; Auto-Pay Off throughout.
- **Final state:** Silver is current and Auto-Pay is Off, matching the start. The "Active until" date after the restore was not compared.
- Test 15 not re-run together with tests 1–14 after the fix. Not run on Firefox or WebKit.
- Each run adds plan-change rows to the Billing history.

**Files (Step 18):** modified `framework/locators/upgrade_plan_locators.py`, `framework/pages/upgrade_plan_page.py`, `tests/ui/test_upgrade_plan.py`, `README.md` (this section only). No file created.

## Active Listing tests

`tests/ui/test_active_listing.py` – a channel's Active Listing page, e.g. `/active-listing/ebay/<id>` (page object `ActiveListingPage`, locators `ActiveListingLocators`). Run with `pytest tests/ui/test_active_listing.py`. All tests carry the `smoke` and `regression` markers and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run.

**Dynamic channel selection.** The fixture expands the **"Active Listing"** sidebar menu and opens the **first channel link its sub-menu lists** (currently `EBAY`). No channel name is hard-coded. The heading is matched as "… All Product" (currently "Ebay All Product"), and the URL only as containing `/active-listing/`. The tests therefore keep working when channels are renamed or added.

**Visibility only.** No product data is checked, and no product row is hard-coded. Nothing on the page is clicked: no Search, Reset, Show entries, Show all columns, sorting, Edit, Status, details, item specifics, images, policies or pagination.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_active_listing_page_opens_successfully` | URL contains `/active-listing/`; "<Channel> All Product" heading |
| 2 | `test_page_header_elements_are_visible` | Breadcrumb area, Help button |
| 3 | `test_filter_bar_is_visible` | UPC Number label and input, SKU label and input, Title label and input, Search button, Reset button |
| 4 | `test_table_and_its_controls_are_visible` | Show entries control, Show all columns button, product table |
| 5–22 | `test_table_header_is_visible[<header>]` | One test per column header (parametrized): S.No, Edit, Status, Title, Product Id, UPC Number, Postal Code, Sub Title, SKU, Quantity, Start Price, Category, Listing Type, Details, Item Specifics, Images, Item Description, Policies |
| 23 | `test_empty_state_message_is_visible_when_no_products` | Once loading has finished, the table's single-cell message row is visible; its text is not checked. It skips when the first row is a data row |

Active Listing facts observed on 2026-09-15 (one read-only inspection; only the sidebar menu and its channel link were clicked):
- The sub-menu link is named after the channel and points to `/active-listing/<platform>/<id>`. The heading is an `h3`, and the breadcrumb is `navigation "breadcrumb"`.
- The filter labels are unlinked `label` elements. "UPC Number", "SKU" and "Title" also name column headers, so labels are matched on `label` elements only. The inputs are named by their placeholders: "UPC Number", "Product SKU" and "Product Title". The unnamed Show entries `select` is the page's only dropdown.
- **Viewport:** the table removes columns from the DOM as the page gets narrower. At 1280 px only 8 of the 18 headers render, and at 1920 px Item Specifics, Images, Item Description and Policies are still missing. All 18 render from 2560 px. The fixture therefore sets `ActiveListingPage.FULL_TABLE_VIEWPORT` (2560×900) first, like Manage Channel (D26). "Show all columns" stays visible at that width.
- The account has no synced products, so the table shows one message row ("No products have been synced for this channel yet. …").

**Result:** Chromium, 2026-09-15: **23/23 passed** on the first run. The empty-state test passed and did not skip. Not run on Firefox or WebKit.

**Files (Step 19):** created `framework/locators/active_listing_locators.py`, `framework/pages/active_listing_page.py`, `tests/ui/test_active_listing.py`. Modified: `README.md` (this section only).

## Manage Order tests

`tests/ui/test_manage_order.py` – the Manage Order "All Orders" view, `/orders` (page object `ManageOrderPage`, locators `ManageOrderLocators`). Run with `pytest tests/ui/test_manage_order.py`. All tests carry the `smoke` and `regression` markers and use the `authenticated_page` fixture, so they add no sign-in beyond the one per browser per run.

The fixture sets `ManageOrderPage.FULL_TABLE_VIEWPORT` (2560×900), expands the **"Manage Order"** sidebar menu, opens its **"All Orders"** link and waits for the `/orders` URL.

**Visibility only.** No order data is checked (amounts, profit, buyer, quantity, tracking or status values). Nothing on the page is clicked: no tabs, Help, Flagged, Search, Reset, filters, date pickers, Show entries, sorting or order rows.

| # | Test | Verifies visible |
|---|---|---|
| 1 | `test_manage_order_page_opens_successfully` | URL ends with `/orders`; "Manage Order" heading |
| 2 | `test_page_header_elements_are_visible` | All Orders tab, Help button, Flagged button |
| 3 | `test_channel_tab_is_visible_when_present` | The first channel tab (currently "EBAY"); skips if none appears |
| 4 | `test_search_and_filter_section_is_visible` | System Status and Order Status dropdowns, By Order Date and By Creation Date fields, Buyer Name, Buyer ID, Part# and Order ID inputs, Search and Reset buttons, Show entries control |
| 5 | `test_orders_table_is_visible` | Orders table |
| 6–21 | `test_table_header_is_visible[<header>]` | One test per column header (parametrized): S.No, Flag, System Status, Notes, Order ID, Age, Order Date, Order Status, Total Amount, Profit $, Profit %, Buyer Name, Buyer ID, Qty, Part Number, Tracking ID |

Manage Order facts observed on 2026-09-15 (one read-only inspection; only the sidebar menu and its All Orders link were clicked):
- The sidebar sub-menu lists "All Orders" (`/orders`) and one link per channel (`/orders?type_of_order=<id>`). The heading is an `h3`.
- The tabs are buttons in a list ("All Orders", then one per channel). Channel tabs render after "All Orders", so test 3 waits for the first one before skipping.
- The filter controls have accessible names from their labels. The Show entries select is named "Entries per page". Header names carry a sort glyph (e.g. "Flag⇅", "Order Date▼"), so headers are matched by prefix.
- **Viewport:** below a wide viewport the table folds its last columns into "+" rows (at the default width, Profit $ through Tracking ID were missing — 7 columns). All 16 render at 2560 px.
- The dashboard's two tables are still in the DOM right after the click, so the page object waits for the `/orders` URL and the table locator is scoped to the table with an "Order ID" header.

**Result:** Chromium, 2026-09-15: **21/21 passed** (after two locator/wait fixes: the viewport, then the table race). Not run on Firefox or WebKit.

**Files (Step 20):** created `framework/locators/manage_order_locators.py`, `framework/pages/manage_order_page.py`, `tests/ui/test_manage_order.py`. Modified: `README.md` (this section only).

## Order Logs → Order Processing tests

`tests/ui/test_order_processing.py` – the Order Processing Logs page, `/order-logs/processing` (page object `OrderProcessingPage`, locators `OrderProcessingLocators`). Run with `pytest tests/ui/test_order_processing.py`. All tests carry `regression`, plus `smoke` (navigation, visibility) or `functional` (no-data, filters), and use `authenticated_page`.

The fixture expands the **"Order Logs"** sidebar menu (only while collapsed), clicks **"Order Processing"**, waits for the table request `GET /api/v1/order-logs/processing` and the URL. No order data is hardcoded; every check holds whether the table is empty (today) or has rows. Not tested: Order Tracking, sorting, order details, edit/update/delete.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_order_processing_opens_from_order_logs_menu` | **Navigation:** sub-menu expanded, URL, "Order Processing Logs" heading, Order Processing link is the active one (`aria-current="page"`) |
| 2 | `test_page_heading_and_breadcrumb_are_visible` | Heading, breadcrumb |
| 3 | `test_filters_and_controls_are_visible` | Order Status, Date Range, Buyer, Part #, Order ID, Search, Reset, Show entries |
| 4 | `test_table_is_visible` | Table |
| 5–13 | `test_table_header_is_visible[<header>]` | S.No, Status, Order ID, Order Status, Total, Buyer, Qty, Part #, Order Date |
| 14 | `test_table_loads_with_rows_or_empty_state` | **No data:** table request OK; with no data rows "No records found." is shown, with rows it is not |
| 15 | `test_controls_stay_usable_when_table_is_empty` | Every filter/control enabled, text inputs editable, a Search still answers with a valid state; skips if the table has rows |
| 16 | `test_order_status_filter` | Selects the first status besides "All", Search, valid state, every row's Order Status matches; **skips while the dropdown offers only "All"** (today) |
| 17 | `test_date_range_filter` | 1st of this month → today picked in the calendar, field value ends with today (`dd-mm-yyyy`), Search, valid state |
| 18–20 | `test_text_filter[Buyer / Part # / Order ID]` | Types `automation-test`, Search, valid state, every row's column contains the value |
| 21 | `test_reset_clears_filters` | Date range + 3 text filters applied, Reset: Order Status "All", every field empty, valid state |

"Valid state" = the table request answered with a 2xx status, heading and table visible, and either rows or the empty-state message.

Order Processing facts observed on 2026-09-22 (read-only inspection; only the sidebar, Search and Reset were clicked):
- The filter labels are not linked to their controls, so each control is located as the sibling after its `<label>` (Order Status and Order ID are also column headers, so only labels are matched). Date Range is flatpickr: its visible field is named by its placeholder "Choose date range". Show entries is an unnamed select after "Show".
- Order Status options come from `GET /api/v1/order-logs/options`; today it holds only "All".
- The empty table has one row with a single cell "No records found.".
- **Search sends no request when the filters are unchanged**, so every Search in these tests follows a filter change.

**Result:** Chromium, 2026-09-22: **20 passed, 1 skipped** (test 16, no status to select). One fix during the run: test 15 now fills Buyer before Search (see the last fact). Not run on Firefox or WebKit.

**Files:** created `framework/locators/order_processing_locators.py`, `framework/pages/order_processing_page.py`, `tests/ui/test_order_processing.py`. Modified: `README.md` (this section only).

## Order Logs → Order Tracking tests

`tests/ui/test_order_tracking.py` – the Order Tracking Logs page, `/order-logs/tracking` (page object `OrderTrackingPage`, locators `OrderTrackingLocators`). Run with `pytest tests/ui/test_order_tracking.py`. Markers and fixture as for Order Processing.

The page has the same layout as Order Processing, so `OrderTrackingPage` / `OrderTrackingLocators` subclass the Order Processing ones and only redefine the sub-menu link ("Order Tracking"), the heading ("Order Tracking Logs"), the URL, the table request (`GET /api/v1/order-logs/tracking`) and the column list (adds **Tracking #**). The fixture opens the page through **"Order Logs"** → **"Order Tracking"**. No order data is hardcoded. Not tested: Order Processing, sorting, order or tracking details/actions, edit/update/delete.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_order_tracking_opens_from_order_logs_menu` | **Navigation:** sub-menu expanded, URL, "Order Tracking Logs" heading, Order Tracking link is the active one (`aria-current="page"`) |
| 2 | `test_page_heading_and_breadcrumb_are_visible` | Heading, breadcrumb |
| 3 | `test_filters_and_controls_are_visible` | Order Status, Date Range, Buyer, Part #, Order ID, Search, Reset, Show entries |
| 4 | `test_table_is_visible` | Table |
| 5–14 | `test_table_header_is_visible[<header>]` | S.No, Status, Order ID, Order Status, Total, Buyer, Qty, Part #, Tracking #, Order Date |
| 15 | `test_table_loads_with_rows_or_empty_state` | **No data:** table request OK; with no data rows "No records found." is shown, with rows it is not |
| 16 | `test_controls_stay_usable_when_table_is_empty` | Every filter/control enabled, text inputs editable, a Search still answers with a valid state; skips if the table has rows |
| 17 | `test_order_status_filter` | First status besides "All", Search, valid state, every row's Order Status matches; **skips while the dropdown offers only "All"** (today) |
| 18 | `test_date_range_filter` | 1st of this month → today, Search, valid state |
| 19–21 | `test_text_filter[Buyer / Part # / Order ID]` | Types `automation-test`, Search, valid state, every row's column contains the value |
| 22 | `test_reset_clears_filters` | Date range + 3 text filters applied, Reset: Order Status "All", every field empty, valid state |

"Valid state" as for Order Processing. The table is empty today ("No records found.").

**Result:** Chromium, 2026-09-22: **21 passed, 1 skipped** (test 17, no status to select). Not run on Firefox or WebKit.

**Files:** created `framework/locators/order_tracking_locators.py`, `framework/pages/order_tracking_page.py`, `tests/ui/test_order_tracking.py`. Modified: `README.md` (this section only).

## Reports → Order Report tests

`tests/ui/test_reports_order_report.py` – the Reports page, `/reports`, Order Report tab (page object `ReportsPage`, locators `ReportsLocators`). Run with `pytest tests/ui/test_reports_order_report.py`. All tests carry `regression`, plus `smoke` (navigation, visibility) or `functional` (filters), and use `authenticated_page`.

The fixture sets `ReportsPage.FULL_TABLE_VIEWPORT` (2560×900), clicks the sidebar **"Reports"** link, waits for the table request `GET /api/v1/reports/orders` and the URL, then opens the **Order Report** tab (it is the default tab, so it is clicked only while another tab is active). Not tested: Request Report, Download, Help, the Inventory/Listing/Stock Report tabs (only their visibility), sorting, pagination behaviour.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_order_report_opens_from_reports_menu` | **Navigation:** URL, "Reports" heading, Order Report tab visible and selected (`active` class) |
| 2 | `test_page_header_elements_are_visible` | Heading, breadcrumb, Help, Request Report |
| 3–6 | `test_report_tab_is_visible[<tab>]` | Order Report, Inventory Report, Listing Report, Stock Report |
| 7 | `test_filters_and_controls_are_visible` | Channel, Order Status, Buyer Name, Part#, Order ID, Search, Reset, Show entries |
| 8 | `test_table_is_visible` | Table |
| 9–18 | `test_table_header_is_visible[<header>]` | S.No, Channel, Order Status, By Order Date, By Creation Date, Buyer Name, Part Number, Order Id, Request Date, Download |
| 19 | `test_footer_and_pagination_are_visible` | "Showing x to y of z entries", Previous, current page number, Next |
| 20–21 | `test_dropdown_filter[Channel / Order Status]` | Selects the value a visible row holds (else the first option besides the default), Search, valid state, every row's column equals it; skips if the dropdown offers no option |
| 22–24 | `test_text_filter[Buyer Name / Part# / Order ID]` | Uses the first visible non-empty value of the column (then at least one row must return), else `automation-test`; Search, valid state, every row's column contains it |
| 25 | `test_combined_filters` | Channel + Order Status from one visible row (else the first option of each), Search, valid state, every row matches both |
| 26 | `test_reset_clears_filters` | Order Status + 3 text filters (`automation-test`) applied → empty state; Reset: Channel "All Channels", Order Status "All", text fields empty, valid state, the unfiltered row count is back |

"Valid state" = the table request answered with a 2xx status, table visible, and either rows or the empty-state message "No results match your filters".

**Dynamic data:** no row count, request date, order ID, buyer name, channel or download status is hardcoded. Filter values come from the visible rows or the dropdown options (Channel options come from the account's channels); empty cells show "—" and are never used as filter values.

Order Report facts observed on 2026-09-22 (read-only inspection; only the sidebar link, the dropdowns, Search and Reset were used):
- Filter controls are named by `aria-label` (Channel, Order Status, Entries per page) or placeholder (Buyer Name, Part#, Order ID). Search sends `filter_channel`, `filter_order_status`, `filter_buyer_name`, `filter_part_number`, `filter_order_id`; it sends no request while the filters are unchanged.
- Report tabs are buttons in a list; the selected one has the `active` class (no `aria-selected`). Help, Request Report and the sidebar link names start with an icon glyph, so they are substring matches. Headers carry a sort glyph (e.g. "Channel⇅"), so they are matched by prefix.
- **Viewport:** at 1280 px the table folds its last columns into a "+" expand row, which shifts every cell by one column; all 10 columns render at 2560 px.
- Today the table holds 2 report requests; Buyer Name, Part Number and Order Id are all "—", so the text filters use `automation-test` and check the empty state.

**Result:** Chromium, 2026-09-22: **26/26 passed** (after two fixes during the run: the sidebar link name has an icon glyph, and the wide viewport). Not run on Firefox or WebKit.

**Files:** created `framework/locators/reports_locators.py`, `framework/pages/reports_page.py`, `tests/ui/test_reports_order_report.py`. Modified: `README.md` (this section only).

## Listing → Common Listing tests

`tests/ui/test_common_listing.py` – the Common Listing page, `/common-listing` (page object `CommonListingPage`, locators `CommonListingLocators`). Run with `pytest tests/ui/test_common_listing.py`. All tests carry `regression`, plus `smoke` (navigation, visibility) or `functional` (filters), and use `authenticated_page`.

The fixture sets `CommonListingPage.FULL_TABLE_VIEWPORT` (2560×900), expands the **"Listing"** sidebar menu (only while collapsed), clicks **"Common Listing"**, waits for the table request `GET /api/v1/common-listing` and the URL. Not tested: Create Listing, Edit, Details, Item Specifics, Images, Item Description, Conditional Description, sorting, pagination, Drafts, Product Images.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_common_listing_opens_from_listing_menu` | **Navigation:** Listing sub-menu expanded, URL, "Common Listing" heading, Common Listing link is the active one (`aria-current="page"`) |
| 2 | `test_page_header_elements_are_visible` | Heading, breadcrumb, Help, Create Listing |
| 3 | `test_filters_and_controls_are_visible` | UPC Number, SKU, Product Id, Title, Channel Filter, Status, By Published Date, Search, Reset, Show entries |
| 4 | `test_table_is_visible` | Table |
| 5–21 | `test_table_header_is_visible[<header>]` | S.No, Edit, Status, Product Id, Channel Name, Title, UPC, Postal Code, Sub Title, SKU, Quantity, Start Price, Details, Item Specifics, Images, Item Description, Conditional Description |
| 22–25 | `test_text_filter[UPC Number / SKU / Product Id / Title]` | Uses the first visible non-empty value of the column (then at least one row must return), else `automation-test`; Search, valid state, every row's column contains it |
| 26–27 | `test_dropdown_filter[Channel Filter / Status]` | Selects the value a visible row holds (else the first option besides the default), Search, valid state, every row's Channel Name / Status equals it; skips if the dropdown offers no option |
| 28 | `test_published_date_filter` | 1st of this month → today picked in the calendar, field value ends with today (`dd-mm-yyyy`), Search, valid state |
| 29 | `test_combined_filters` | Channel Filter + Status from one visible row (else the first option of each), Search, valid state, every row matches both |
| 30 | `test_reset_clears_filters` | All 4 text filters (`automation-test`), both dropdowns and a one-day date range applied → empty state; Reset: every field empty, dropdowns back to "All Channels" / "All", valid state, the unfiltered row count is back |

"Valid state" = the table request answered with a 2xx status, heading and table visible, and either rows or the empty-state message "No products found.".

**Dynamic data:** no row count, UPC, SKU, Product Id, title, channel, status or date is hardcoded. Text values come from the visible rows, dropdown values from the rendered options (Channel options come from `GET /api/v1/common-listing/channels`), dates from today's date. Channel and status are compared case-insensitively.

Common Listing facts observed on 2026-09-22 (read-only inspection; only the sidebar, the filters, Search and Reset were used):
- The filter labels are unlinked `label` elements, so each control is the sibling after its label. By Published Date is flatpickr (visible field named by its placeholder "Choose date range"). Show entries is an unnamed select after "Show".
- The table has an **unnamed first column** before S.No, so cells are addressed at header position + 2.
- Search sends `search_upc`, `search_sku`, `search_product_id`, `search_title`, `channel_id`, `status`, `date_from`, `date_to`; it **sends no request while the filters are unchanged**. Reset clears every field and reloads without filters.
- The Channel Filter options come from their own request (`GET /api/v1/common-listing/channels`), answered separately from the table rows, so the fixture waits for both.
- Empty cells show "—"; it is never used as a filter value.
- The table was empty at first ("No products found."); later on 2026-09-22 it held listings, so the filters then ran against real rows.

**Fix (2026-09-22):** a later run failed `test_text_filter[UPC Number]` and `[SKU]` and skipped `test_dropdown_filter[Channel Filter]`. The text tests typed the "—" placeholder of an empty cell as the filter value, so no row matched. The Channel test read the options before their request answered. `first_value()` now skips "—", and `open_from_sidebar()` also waits for the channels request. After the fix, all 9 filter tests passed with no skip, and the full file passed **30/30 on Chromium in one run** (10 min 11 s).

**Result:** Chromium, 2026-09-22: **30/30 passed** (29 in the full file run; the navigation test errored in setup because `/login` timed out on the slow server, and passed on re-run). The live server was slow (5–40 s per test). Not run on Firefox or WebKit.

**Files:** created `framework/locators/common_listing_locators.py`, `framework/pages/common_listing_page.py`, `tests/ui/test_common_listing.py`. Modified: `README.md` (this section and a change-log row).

### Create Listing → Single Listing → Manual

`tests/ui/test_single_listing.py` – the "Add New Listing" page, `/single-listing/add` (page object `SingleListingPage`, locators `SingleListingLocators`). Run with `pytest tests/ui/test_single_listing.py`. All tests carry `regression`, plus `smoke` (navigation, visibility) or `functional` (section buttons, validation), and use `authenticated_page`.

**Navigation (updated 2026-09-23):** "Single Listing" is no longer a one-click entry. It is a **sub-menu toggle** (`aria-expanded`) inside the Create Listing dropdown; clicking it navigates nowhere and instead reveals a nested list with **Manual** and **Generate Listing By AI**. The automated path is **Create Listing → Single Listing → Manual**, which opens the same `/single-listing/add` "Add New Listing" form as before. **The "Generate Listing By AI" flow is currently not covered** – the option's visibility is asserted, it is never clicked.

The toggle and both sub-options carry a Bootstrap icon whose glyph joins their accessible name, so their names are matched as the word surrounded by non-word characters (`_named()` in `common_listing_locators.py`) instead of `exact=True`.

The `single_listing` fixture opens Common Listing, presses **Create Listing**, expands **Single Listing**, clicks **Manual**, waits for `GET /api/v1/single-listing/form-options` (fills the dropdowns) and the URL, then sets a 1280×720 viewport. **No field is ever filled.** As a safety net the fixture aborts every non-GET `/api/` request and records it; the validation tests fail if any was attempted, so no listing can be saved or sent live even if client-side validation broke. Not tested: Multi Listing, Generate Listing By AI, a successful Save as Draft / Send to Live, image upload, Add Specification, the description editor's toolbar, category search and policy logic.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_create_listing_menu_offers_single_and_multi_listing` | Create Listing opens its menu; "Single Listing" and "Multi Listing" (the application's wording) visible |
| 2 | `test_single_listing_offers_manual_and_ai_options` | "Single Listing" expands its sub-menu; "Manual" and "Generate Listing By AI" visible (AI is only checked, never opened) |
| 3 | `test_single_listing_opens_add_new_listing_page` | **Navigation:** Manual opens URL `/single-listing/add`, "Add New Listing" heading, breadcrumb |
| 4 | `test_section_buttons_and_actions_are_visible` | 8 section buttons (Store Setup, Condition, Item Specifics, Selling, Shipping, Product, Description, Images), Save as Draft, Send to Live |
| 5–12 | `test_section_is_visible[<section>]` | Each section and its heading: eBay Store Setup, Condition, Item Specifics, Selling Details, Shipping & Pricing, Product Details, Description, Product Images |
| 13–41 | `test_field_is_visible[<section>-<label>]` | 29 labelled fields: label, control, and the red `*` marker present on required fields / absent on optional ones (see below) |
| 42 | `test_checkboxes_description_and_image_controls_are_visible` | Add Prop 65 Warning, Charge tax on this product, This is a physical product; Add Specification; description "Paragraph format" select and editor; Product Images label with `*`, Select from Library, Upload from Storage |
| 43–50 | `test_section_button_scrolls_to_its_section[<button>]` | Scrolls to the far end of the form, checks the section heading is off-screen, clicks the button, heading fully in the viewport, URL unchanged |
| 51–52 | `test_empty_form_is_rejected[Save as Draft / Send to Live]` | Every required field has `is-invalid` and its message "<label> is required." inside its own field; Images shows "Please upload at least one product image."; no optional field is marked; still on `/single-listing/add` with the heading; no write request attempted |

Fields (page order; **required** in bold): Store Setup – **Fulfillment Policy**, **Payment Policy**, **Return Policy**, **eBay Category**; Condition – **Condition**, Condition Description; Item Specifics – **Brand Code**, **Part Number / Product ID**, **Other Part Number**, **Interchange Part Number**, **Brand**, **Warranty**, **UPC**, **EPID**; Selling – **Listing Type**, Private Listing, **Listing Duration**, **Quantity**; Shipping – **Handling Time**, **Start Price**, Item Cost, **Postal Code**, Site; Product – **Title**, Sub Title, **SKU**, UPC, Tags, Video URL; Images – **Product Images**.

Single Listing facts observed on 2026-09-22 (read-only inspection; the empty form was submitted with every write request blocked, and none was sent):
- Labels are not linked to their controls; a field is the label's parent element, which holds the control and its message. "UPC" is a label in both Item Specifics and Product Details, so fields are scoped to their section (`#sec-store` … `#sec-images`).
- Section buttons scroll the window so the section sits near the top; the buttons get no active state. The Save as Draft / Send to Live bar stays on screen, so the "scroll to bottom" step targets Upload from Storage.
- Save as Draft and Send to Live run the **same** client-side validation on the empty form: 21 field messages plus the image message, no toast, no request, no navigation.
- The Create Listing menu's `<ul>` has no list role, so it is located as the options' nearest `ul`; the Single Listing sub-menu is the toggle's following-sibling `<ul>` inside the same list item.

**Result:** Chromium, 2026-09-22: first full run 47/51; 4 failed on test code (menu container locator; the scroll-to-bottom target was the always-visible action bar). After the fix the 9 affected tests (menu + 8 section buttons) passed; the 42 others had passed in the full run → **51/51**. The full file was not re-run in one go afterwards. Not run on Firefox or WebKit. No listing was created, saved or sent live.

**Navigation fix (2026-09-23):** the application turned "Single Listing" into a sub-menu, so every test errored in setup – the click no longer navigated, and the icon glyph added to the toggle's accessible name broke the `exact=True` match. Only the navigation locators and `open_from_common_listing()` changed; no field or validation test was rewritten. Re-run on Chromium, 2026-09-23: **52/52 passed** in one run (3 min 58 s). No listing was created, saved or sent live, and "Generate Listing By AI" was never opened.

**Files:** created `framework/locators/single_listing_locators.py`, `framework/pages/single_listing_page.py`, `tests/ui/test_single_listing.py`. Modified: `framework/locators/common_listing_locators.py` (Create Listing menu and its two options), `framework/pages/common_listing_page.py` (`open_create_listing_menu`, `choose_single_listing`), `README.md` (this subsection and a change-log row).

## Setup → Import Setting tests

`tests/ui/test_import_setting.py` – the Import Setting page, `/setup/import` (page object `ImportSettingPage`, locators `ImportSettingLocators`). Run with `pytest tests/ui/test_import_setting.py`. **Visibility only** – no filter, button, link or table behaviour is exercised. All 12 test items carry `regression` and `smoke` and use `authenticated_page`.

The `import_setting` fixture expands the **"Setup"** sidebar menu (only while collapsed), clicks **"Import Setting"**, waits for the table request `GET /api/v1/setup/import` and the URL, then closes the onboarding dialog the page opens over itself (see below). Not tested: Search, Reset, the four filters, Add Setup, Help & sample files, Read the guide first, View Linking, Status, the Action buttons, pagination, sorting, file upload/import, and every other Setup page.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_import_setting_opens_from_setup_menu` | **Navigation:** Setup sub-menu expanded, URL `/setup/import`, "Setup Import List" heading, Import Setting link is the active one (`aria-current="page"`) |
| 2 | `test_page_header_elements_are_visible` | Heading, breadcrumb, Help & sample files, + Add Setup |
| 3 | `test_filters_and_controls_are_visible` | By Name label and input, By Setup Type, By Setup Files, By Status, Search, Reset, Show entries |
| 4 | `test_table_is_visible` | Setup Import table |
| 5–11 | `test_table_header_is_visible[<header>]` | S.No, Name, Setup Type, Setup Files, View Linking, Status, Action |
| 12 | `test_empty_state_is_visible_while_no_import_setting_exists` | **Dynamic:** table and its first body row always visible; with no data – empty-state cell, "You don't have any import settings yet.", the empty-state + Add Setup and "Read the guide first" buttons; with data – no empty-state cell, and heading, + Add Setup, Search and Reset still visible |

**Dynamic no-data handling:** nothing about the rows is hardcoded. The empty-state row is the one cell that spans every column (`td[colspan]`), so `data_rows` is the body rows without it. When import settings exist later, test 12 checks the table and the page controls instead of the empty-state message, so it does not fail for a missing empty state.

Import Setting facts observed on 2026-09-23 (read-only inspection; only the "Setup" menu, its "Import Setting" link and the guide dialog's × were clicked):
- While the account has **no import setting the page opens an onboarding dialog** ("New to import settings? Start here") over itself on **every** load, not only the first. It carries a second table (Setup type / What kind of file it maps / Sample file), so the page's own table is identified by its "View Linking" column header, and the fixture closes the dialog (`dismiss_guide_dialog()`) before anything is checked. Nothing inside the dialog is used or tested.
- The filter labels are unlinked `label` elements, so each control is the sibling after its label. The controls have no name, `id` or `aria-label`. Show entries is an unnamed select after "Show".
- The header "+ Add Setup" and the empty-state "+ Add Setup" share the same name, so the header one is the first in the DOM and the empty-state one is scoped to the table.
- The page header buttons and both empty-state buttons start with an **icon glyph**, so their names are substring matches.
- The breadcrumb navigation (Dashboard / Setup / Import Setting) is `nav[aria-label="breadcrumb"]`. Once import settings exist, `main` holds a **second** navigation, `nav[aria-label="Pagination"]`, so the breadcrumb is always addressed by its name.
- The empty-state message uses a typographic apostrophe (U+2019).

**Result:** Chromium, 2026-09-23: **12/12 passed** (2 min 10 s). Two fixes were needed during verification: the page header and empty-state button names were matched exactly although they start with an icon glyph, and the breadcrumb was located as the only `navigation` in `main`, which broke as soon as the page held data and rendered a Pagination navigation. Both runs also proved the dynamic branch of test 12: the first (2 min 41 s) ran against an empty list, the re-run against a list with import settings. Not run on Firefox or WebKit. Nothing was created, edited, deleted, imported or uploaded.

**Files:** created `framework/locators/import_setting_locators.py`, `framework/pages/import_setting_page.py`, `tests/ui/test_import_setting.py`. Modified: `README.md` (this section and a change-log row).

### Import Setting functional tests (Add Setup → Upload & Map → search → edit → delete)

`tests/ui/test_import_setting_functional.py` – the complete Import Setting workflow. Run with `pytest tests/ui/test_import_setting_functional.py`. 13 test items in 10 functions, all `regression` + `functional` + `destructive`; the 12 visibility tests in `test_import_setting.py` are unchanged. The `import_setting` fixture opens the page through the sidebar and switches **Show entries to its largest size**, so a filter never has to look for a record on a later page.

**Upload files.** `test_data/import_setting_sample.csv` is the supplied sample (9 columns, 2 rows); `import_setting_sample.xls` and `import_setting_sample.xlsx` hold the **same** rows and exist only for this format coverage. The expected column list is read from the CSV header at run time, never hardcoded.

**Clean-up.** `setup_cleanup` is a finalizer: a name is registered **before** the Save that could create it, and every registered name is searched and deleted after the test, whatever it did – including after a failure, since a reload closes a modal a failed test left open. Only registered automation names are ever deleted. A name that survives fails the teardown, which is *added* to the test failure and names the setup left behind. A full run leaves **zero** automation import settings.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_add_setup_modal_opens_with_its_step_one_fields` | "Add Import Setting" modal, both step badges (step 1 current), File Type label with the CSV / Xls / XLSX buttons, Name, Select Type, their required markers, Cancel, Next, close icon |
| 2 | `test_file_type_choices_match_the_prepared_upload_files` | The three formats the modal offers are exactly the three the test data covers, CSV is preselected, and each button becomes the selected one when clicked |
| 3–5 | `test_next_keeps_step_one_open_until_name_and_type_are_filled[…]` | **Mandatory fields**, 3 combinations (both empty / name only / type only): step 2 never opens, the required markers are shown, the typed value stays, no request is sent, and no import setting is created |
| 6 | `test_save_creates_nothing_until_at_least_one_column_is_mapped` | Step 2 with the file uploaded but no column linked: Save sends no create request, the modal stays on step 2, nothing is created |
| 7–8 | `test_create_import_setting_from_an_uploaded_file[csv\|xlsx]` | **Whole flow per format:** File Type → unique name → Setup Type → Next → step 2 opens and names the format → upload accepted → the detected columns equal the sample header → "0 of 9 columns linked" → 2 columns linked with the fields the application offers → Save → create response OK, modal closed, row in the list with the right Setup Type and Setup Files, and View Linking shows the mapping that was made |
| 9 | `test_xls_header_is_not_read_by_the_application` | **XLS blocker, pinned:** the upload is answered with `status: false` and the application's own message, no column is detected and nothing is created (see below) |
| 10 | `test_every_setup_type_can_be_created_with_its_own_mapping_fields` | Every Setup Type the live dropdown offers (today Listing, Inventory, Order Processing, Order Status) is created once with the CSV file; each one's "Link With Column" fields are read from the UI, must be non-empty, and must differ between the types; each new row shows its own type |
| 11 | `test_search_filters_and_reset` | By Name (the unique name returns exactly one row), By Setup Type, By Setup Files and By Status each on their own (**every** returned row carries the selected value), all four combined (one row), and Reset (all four controls empty and the unfiltered list back). The status and the file are read from the created row, never assumed, and no row count is hardcoded |
| 12 | `test_edit_updates_the_saved_column_mapping` | Edit opens "Edit Import Setting" straight on Upload & Map with the saved mapping loaded (columns, linked count and each selected field), one link is changed, Save answers `PUT …/setup/import/<id>` OK, the record is still found by its name, View Linking shows the updated mapping and re-opening Edit loads it back |
| 13 | `test_delete_removes_the_automation_import_setting` | The row's Delete opens the "Delete import setting?" confirmation, confirming answers `DELETE …/setup/import/<id>` OK, only that name disappears (every other listed name is still there – no row count), and a search by its name finds nothing |

**Coverage summary:** mandatory validation 3 cases + the unmapped-file case; CSV and XLSX created end to end, XLS pinned as a blocker; all 4 Setup Types created; Upload & Map (upload, column detection, mapping, save) per format and per type; 4 single filters + combined + Reset; edit and delete each on an automation-owned record only.

Import Setting facts observed on 2026-09-23 while automating the workflow (everything below was verified live):
- The Add / Edit modal is a Bootstrap modal **without** a `dialog` role, so it is located as `.modal.show`; only one is open at a time.
- **Nothing is imported here.** Step 2 sends the file to `POST /api/v1/setup/import/parse-header`, the application reads the **header row only** and discards the file. Create is `POST /api/v1/setup/import`, update `PUT …/<id>`, delete `DELETE …/<id>`.
- **Mandatory fields show no error text.** With Name or Select Type empty, Next does nothing at all – no message, no `is-invalid` class, no request. The required state the tests check is the application's own: the red asterisk on both labels and the fact that step 2 never opens.
- **Save needs at least one linked column**; with none linked the application sends no create request either.
- Each Setup Type brings its **own** field list in "Link With Column" (Listing 9 fields, Inventory 5, Order Processing 26, Order Status 16). A field can be used once; the ones already taken are `disabled`.
- **XLS cannot be used (application defect).** `Xls` is offered as a File Type and the file input accepts `.xls`, but the backend answers `{"status": false, "message": "Unable to read file header: openpyxl does not support the old .xls file format, please use xlrd to read this"}` – its own hint "Legacy `.xls` may fail to parse" is in fact always true. No XLS import setting can be created until the application is fixed; test 9 fails on purpose as soon as it is.
- The **View Linking modal is cached per record**: opening it, editing the record and opening it again shows the *old* mapping until the list is fetched again. The application does not refetch the list after an update either, so the edit test searches (which refetches) before it checks the new mapping.
- **Search is a no-op while the filters do not change.** Clicking Search with the filters the list already shows sends **no request at all**, so a step that waits for a table response there hangs. `search()` remembers the filters the list shows and only waits for a response when they change; a delete waits for its own row to disappear rather than for a row count.
- **Filtering is server-side** (`filter1` name, `filter2` setup type, `filter3` setup file, `filter4` status), but changing a filter control also makes the page refetch **unfiltered**, so `search()` waits for the response that carries every filter of that search. Reading the table right after any list response can otherwise hit the previous render: `wait_for_table()` waits for the network and a body row, and whole columns are read in one call (`column_values`).
- The Name column is rendered with `text-transform: capitalize`, so the automation names are upper case throughout; the field allows 30 characters.
- The Edit modal holds **no** Name or Setup Type field – only the mapping – so the editable field the test changes is one column's linked field.

**Result:** Chromium, 2026-09-23: **13/13 functional passed**, and **25/25** together with the 12 visibility tests (2 min 38 s), twice in a row. The account finished with **zero** automation import settings left. Not run on Firefox or WebKit. Four problems were found and fixed during verification: the clean-up searched for its record while the table still showed the previous render (all reads now go through `wait_for_table()` / `column_values()`); Search was answered by the page's own unfiltered refetch (it now waits for the response carrying its filters); and the delete test compared row counts, which breaks as soon as the list is paginated (it now compares the names). A fourth appeared in a later run: the clean-up's verification search repeated the filters the list already had, the application answered the click with no request, and the 30 s response wait turned every data-writing test's teardown into an ERROR (the tests themselves had passed). Both the unchanged-filter case and the row read after a delete are now handled; two consecutive full runs finished 25/25 with nothing left behind. Records left behind by those earlier runs were deleted.

**Files:** created `tests/ui/test_import_setting_functional.py`, `test_data/import_setting_sample.csv`, `test_data/import_setting_sample.xls`, `test_data/import_setting_sample.xlsx`. Modified: `framework/locators/import_setting_locators.py` (modal, mapping, row and filter locators), `framework/pages/import_setting_page.py` (the workflow, search and clean-up actions), `README.md` (this subsection and a change-log row).

## My Account → Card Setting tests

`tests/ui/test_card_setting.py` – the Card Setting page, `/card-setting` (page object `CardSettingPage`, locators `CardSettingLocators`). Run with `pytest tests/ui/test_card_setting.py`. 7 test items, all `regression`: 1 `smoke`, 6 `functional`, of which 5 are `destructive` + `shared_state`. Uses `authenticated_page`.

The `card_setting` fixture expands the **"My Account"** sidebar menu (only while collapsed), clicks **"Card Setting"**, waits for `GET /api/v1/card-setting` and the URL, and – on the first test of the run – records the account's existing cards and its default card so both can be restored afterwards.

### Payment safety

The application runs **Stripe in test mode** (`pk_test_…`); the Add Card form is Stripe's card element in a cross-origin iframe (`iframe[title="Secure card payment input frame"]`).

- Card data comes from configuration only: `SHP_TEST_CARD_NUMBER/_EXPIRY/_BRAND`, `SHP_TEST_CARD_2_*` and the shared `SHP_TEST_CARD_CVC` (see `.env.example`), read by `get_sandbox_cards()` into a frozen `SandboxCard`. **Only Stripe's published test card numbers belong there – never a real card.** No number, expiry or CVC is hardcoded anywhere in the framework or the tests. When the variables are not set the whole module **skips**; CI therefore skips it until the secrets are added.
- `SandboxCard` keeps `number` and `cvc` out of `repr()`, so they cannot reach a log line, a pytest traceback or the JUnit report; `str()` yields `Visa ****5556 exp 11/2030`, which is what the application itself displays and the only form used in log messages and failure messages.
- Number and CVC are typed with `fill_secret()` (value never logged, masked in Playwright error messages) and the whole add step – typing, ticking the box and submitting – runs inside `_untraced()`. Tracing only restarts once the modal, and with it the iframe still holding the values, is gone.
- Nothing triggers a payment, a charge, a subscription change or an invoice, and no declined or invalid card is ever submitted. Only the payment provider's tokenisation call and SHP's own `/api/v1/card-setting` requests are made.
- Verified 2026-09-23 with `--tracing on`: the full card numbers appear in **no** file under `reports/` or `test-results/`, including all 7 extracted `trace.zip` archives. `reports/pytest.log` shows `Fill card number field (value hidden)` and `Fill card CVC field (value hidden)`.

### Tests

| # | Test | Markers | Verifies |
|---|---|---|---|
| 1 | `test_card_setting_opens_from_my_account_menu` | `smoke` | **Navigation:** My Account sub-menu expanded, URL `/card-setting`, Card Setting is the active link (`aria-current="page"`), "Card Setting" heading, breadcrumb, + Add Card, at least one card tile, exactly one Default tile |
| 2 | `test_add_card_modal_opens_with_its_controls` | `functional` | **Add Card modal:** title, "Card details" label, the Stripe element and its card-number / expiry / CVC inputs, the "Set as default card" checkbox (unchecked), the Stripe notice, Cancel and Add Card enabled, the close (×) icon; Cancel closes the modal and adds nothing |
| 3 | `test_add_sandbox_card_without_the_default_checkbox` | `functional`, `destructive`, `shared_state` | **Add without default:** the sandbox card is accepted and appears as a new tile; its number is shown **masked to the last four digits only** and the full number is nowhere on the page; it is **not** default, it offers Set default and delete, the account's previous default still holds the badge, and exactly one tile is Default |
| 4 | `test_set_default_moves_the_default_to_the_added_card` | `functional`, `destructive`, `shared_state` | **Set default:** the added card gets the Default badge and loses both action buttons; the previously default card loses the badge and gets its Set default button back; exactly one tile is Default |
| 5 | `test_remove_deletes_only_the_card_this_run_added` | `functional`, `destructive`, `shared_state` | **Delete:** the original default is put back first (a default card has no delete button), then the trash icon opens the "Remove card?" confirmation naming the card's brand and masked number; Remove closes it, the tile is gone, every pre-existing card is still listed, the tile count is back to the original, and the account's default is the original one again |
| 6 | `test_add_sandbox_card_with_the_default_checkbox_makes_it_default` | `functional`, `destructive`, `shared_state` | **Add with "Set as default":** the second sandbox card is created, appears masked, and is **Default straight away** without a second click; the previous default loses its badge; exactly one tile is Default |
| 7 | `test_run_leaves_the_original_cards_and_default_behind` | `functional`, `destructive`, `shared_state` | **Clean-up / restore:** the original default is set back, the second card is removed, and the resulting card list equals the list recorded before the run, default flag included |

### Clean-up and restoration strategy

Two layers, so a card this run creates cannot survive a failure:

1. **In the flow** – tests 5 and 7 remove the card their flow added and put the original default back; each drops the card from the tracker only after the page has confirmed it is gone.
2. **In the fixture** – the module-scoped `card_state` fixture holds the cards the run created (each is registered **before** it is submitted) and, after the module's last test, opens a fresh signed-in context and: removes every card still tracked (restoring the original default first when the tracked card is currently the default, because a default card has no delete button), puts the original default back if it is not, and compares the resulting card list with the one recorded at the start. Anything that could not be removed or restored is logged and raised as a teardown error naming the card by brand, masked number and expiry – reported **in addition to**, never instead of, a test's own failure.

Pre-existing cards are never deleted; only their default flag is moved and put back. A test refuses to run (with a clear message) when the account already holds a card matching the configured sandbox card, so it can never mistake somebody else's card – or a leftover from a crashed earlier run – for the one it added.

Card Setting facts observed on 2026-09-23 (the only writes were the sandbox cards these tests add and delete again):
- Every saved card is a Bootstrap **card tile**, not a table row: masked number (`•••• •••• •••• 5454`, U+2022), then `<Brand> · Exp MM/YYYY`. The default tile carries a "Default" badge and has **no** action buttons; every other tile has "Set default" and an icon-only delete button, located by `button.btn-outline-danger` because it has no accessible name.
- A card is addressed by its **masked last four digits *and* its brand / expiry line**: the account holds two cards ending in `4242` that differ only in expiry.
- `filter(has_text=...)` matches an element's whole concatenated text content, in which the number line runs straight into the brand line (`… 5556Visa · Exp …`). A `\b` after the digits therefore never matches; the digits are anchored to the masking bullets in front of them instead (`masked_number_pattern()`).
- The Add Card modal renders **inside `main`** and repeats the name "Add Card" on its submit button, so the page's own button is the first of the two in the DOM. Both modals share the `.modal` class and are told apart by their own title ("Add Card" / "Remove card?").
- The page has no toast that can be waited on reliably: after every change it re-sends `GET /api/v1/card-setting`, which is what the page object waits for (the delete request is the same path with the card's id appended, hence an exact match). Set default is confirmed by the badge instead of by a request.
- Adding a card round-trips through the payment provider before SHP answers (5–10 s observed), so the modal, the list reload and the badge use a 45 s timeout.
- A new card is **not** made default unless "Set as default card" is ticked – verified against an account that already had a default card.

**Result:** Chromium, 2026-09-23: **7/7 passed** (1 min 20 s; 1 min 15 s on the `--tracing on` re-run). Two fixes were needed during verification: the card tile was matched with a `\b` word boundary that cannot match in concatenated text content, and the clean-up context navigated with Playwright's 30 s default instead of the framework's 60 s navigation timeout. The account finished with exactly its four original cards and its original default card (MasterCard, masked `5454`). Not run on Firefox or WebKit. No payment, charge, subscription change or invoice was triggered, and no pre-existing card was deleted.

**Files:** created `framework/locators/card_setting_locators.py`, `framework/pages/card_setting_page.py`, `tests/ui/test_card_setting.py`. Modified: `framework/config.py` (`SandboxCard`, `get_sandbox_cards()`), `.env.example` (the seven `SHP_TEST_CARD*` names), `README.md` (this section, the marker table and a change-log row).

## My Account → Email Templates tests

`tests/ui/test_email_templates.py` – the Email Templates page, `/email-templates` (page object `EmailTemplatesPage`, locators `EmailTemplatesLocators`). Run with `pytest tests/ui/test_email_templates.py`. **Visibility only** – no filter, button or table behaviour is exercised, and nothing is created, edited or deleted. All 11 test items carry `regression` and `smoke` and use `authenticated_page`.

The `email_templates` fixture expands the **"My Account"** sidebar menu (only while collapsed), clicks **"Email Templates"**, waits for the table request `GET /api/v1/email-templates` and the URL. Not tested: Search, Reset, the Name and Status filters, Add Template, the row Actions (edit/delete), Channel behaviour, sorting, pagination, Show entries, template creation or sending, SMTP, and every other My Account page (My Profile, Billing, Card Setting, SMTP Settings are never opened).

| # | Test | Verifies |
|---|---|---|
| 1 | `test_email_templates_opens_from_my_account_menu` | **Navigation:** My Account sub-menu expanded, URL `/email-templates`, "Email Templates" heading, Email Templates link is the active one (`aria-current="page"`) |
| 2 | `test_page_header_elements_are_visible` | Heading, breadcrumb, + Add Template |
| 3 | `test_filters_and_controls_are_visible` | Name label and input, Status dropdown, Search, Reset, Show entries |
| 4 | `test_table_is_visible` | Email Templates table |
| 5–10 | `test_table_header_is_visible[<header>]` | S.No, Name, Subject, Channel, Status, Actions |
| 11 | `test_empty_state_is_visible_while_no_template_exists` | **Dynamic:** table and its first body row always visible; with no data – empty-state cell and "No email templates yet"; with data – no empty-state cell, and heading, + Add Template, Search and Reset still visible |

**Dynamic no-data handling:** nothing about the rows is hardcoded. The empty-state row is the one cell that spans every column (`td[colspan]`), so `data_rows` is the body rows without it. When templates exist later, test 11 checks the table and the page controls instead of the empty-state message, so it does not fail for a missing empty state.

Email Templates facts observed on 2026-09-23 (read-only inspection; only the "My Account" menu and its "Email Templates" link were clicked):
- The list request is `GET /api/v1/email-templates?page_no=1&no_of_rows=10`; the page object matches it on the path only, so the query string may change.
- The sortable column headers append a **sort glyph** (U+21C5), e.g. `Name⇅`, so `column_header()` matches the header name as a substring and never exactly. `S.No` and `Actions` are not sortable.
- The filter labels are unlinked `label` elements, so the Name input is the sibling after its label (its placeholder is "Search name"). Both selects do carry an `aria-label` – `Status` and `Entries per page` – and are addressed by it.
- The "+ Add Template" button starts with an **icon glyph** (`bi bi-plus-lg`), so its name is a substring match. Unlike Import Setting, the empty state holds **no** second Add button – only the envelope icon and the message.
- The breadcrumb navigation (Dashboard / My Account / Email Templates) is `nav[aria-label="breadcrumb"]`. Once templates exist, `main` may hold a second navigation (Pagination), so the breadcrumb is always addressed by its name.
- The account currently has **no email template**, so the table body is a single `td[colspan="6"]` holding "No email templates yet".

**Result:** Chromium, 2026-09-23: **11/11 passed** (1 min 51 s), first run, no fixes needed. The no-data branch of test 11 was the one exercised (the account is empty); the with-data branch is untested against real data. Not run on Firefox or WebKit. Nothing was created, edited, deleted or sent.

**Files:** created `framework/locators/email_templates_locators.py`, `framework/pages/email_templates_page.py`, `tests/ui/test_email_templates.py`. Modified: `README.md` (this section and a change-log row).

### Functional tests (create / filter / delete)

`tests/ui/test_email_templates_functional.py` – the behaviour of the page, using the same `EmailTemplatesPage` and `EmailTemplatesLocators`. Run with `pytest tests/ui/test_email_templates_functional.py`. The visibility file above is untouched and stays visibility-only. All 5 test items carry `regression`, `functional` and `destructive`, and use `authenticated_page`; `destructive` is what keeps them in the single Chromium data-writing CI job. **Exactly one template is created per run**, named `AUTO_EMAIL_TEMPLATE_<8 hex chars>` (28 of the 30 characters the field allows), and it is deleted again.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_add_template_modal_opens_with_its_fields` | **Flow 1:** + Add Template opens the modal – title, Name, Subject, Body (HTML), Channel store id, Save, Cancel; Cancel closes it |
| 2–4 | `test_save_creates_nothing_until_every_required_field_is_filled[nothing-filled\|name-only\|name-and-subject]` | **Required fields:** Save with the Body (and, in the first two cases, Subject and Name) empty sends **no** create request, leaves the modal open and enabled with the typed values intact, and the table holds no such template afterwards |
| 5 | `test_create_filter_and_delete_an_email_template` | **Flows 2–4:** creation, Name search, Status filter, combined filter, Reset and delete, in that order on one template (see below) |

**Test 5, step by step.** Create: Name + Subject + Body filled, Channel store id left empty, Save → `POST /api/v1/email-templates` is `2xx`, the modal closes, and the row appears with the expected Name and Subject. The row's Status badge is then **read**, never assumed, and drives the rest. Name search: the unique name + Search → exactly one row, the created one. Status filter: Reset, then the detected status → the created row is there and **every** returned row carries that status. Combined: unique name + its own status → exactly one row with both; then the *other* status with the same name → no row and "No results match your filters", which is how "unrelated rows are not returned" is checked. Reset: the Name input is empty, Status is back to its default (`value=""`), the created row is back and the table is not empty. Delete: the row's own Delete action → the "Delete template?" confirmation → Delete → `DELETE /api/v1/email-templates/<id>` is `2xx`, the dialog closes and a fresh search by the unique name returns nothing.

**Clean-up.** The `template_cleanup` fixture holds the names this test created and, in its teardown, opens the page, searches each name and deletes it if it is still there. A name is registered **before** Save, so a template created by a step that then failed is still removed. Only these `AUTO_EMAIL_TEMPLATE_*` names are ever deleted – no pre-existing template is touched. If a name survives, the teardown fails and names it; that failure is *added to* the test failure, so an original failure is never hidden.

Functional facts observed on 2026-09-23 (Add Template modal, filters and delete, all exercised against the live page):
- The modal is a Bootstrap `.modal.show` with **no** `role="dialog"` and no `aria-label`, so it is addressed by its own title heading – `Add Template` for the form, `Delete template?` for the confirmation. Its labels are unlinked as well, so Name, Subject and Channel store id are the sibling after their label; the Body label sits in a flex row next to "Preview", so its textarea is not a sibling and is addressed as the modal's only `textarea`.
- Name is capped at 30 characters and Subject at 60 (each with an `n/30`-style counter); Channel store id is `type="number"` and optional – creation succeeds with it empty.
- **Required-field validation is silent.** With Name, Subject or Body empty, Save is still enabled, the click sends **no** request, and the application shows *no* error message, no `is-invalid` field and no toast: the modal simply stays open. The tests therefore verify the authoritative outcomes (no `POST`, modal still open, values kept, no such row) instead of error text that does not exist. Worth raising with the team as a UX gap.
- **No success toast** either: a successful save is indicated only by the modal closing and the table reloading.
- The filters go into the list request as `search_name=` and `filter_status=`; Status is a plain `<select>` with `All statuses` (`""`), `Active` (`1`) and `Inactive` (`0`), so tests map a visible status label to its option value instead of hardcoding one.
- A filter that matches nothing renders a **different** empty state from the account-level one: "No results match your filters" plus a "Clear filters" button, not "No email templates yet".
- A new template is created **Active** (green badge); its Channel cell shows an em dash while no channel store id is given.
- The row actions are icon-only buttons with `aria-label="Edit"` / `"Delete"`. Delete opens a small confirmation naming the template ("Delete … ? This cannot be undone."); confirming deletes it and reloads the table **with the current filters still applied**.

**Result:** Chromium, 2026-09-23: **5/5 passed** (1 min 52 s), first run, no fixes needed. The 11 visibility tests were re-run afterwards and still pass (11/11), and the account was verified to hold **0 templates** at the end – no automation template left behind. Not run on Firefox or WebKit. Nothing was sent, no SMTP setting was touched, no pre-existing template was created, edited or deleted, and edit/update was not exercised.

**Files:** created `tests/ui/test_email_templates_functional.py`. Modified: `framework/locators/email_templates_locators.py` (modal, delete-dialog, row and status-option locators; `FILTERED_EMPTY_MESSAGE`, `DELETE_API_PATH`), `framework/pages/email_templates_page.py` (modal, search, reset and delete actions; create-request recording), `README.md` (this sub-section and a change-log row).

## My Account → SMTP Settings tests

`tests/ui/test_smtp_settings.py` – the SMTP Settings page, `/smtp-settings` (page object `SmtpSettingsPage`, locators `SmtpSettingsLocators`). Run with `pytest tests/ui/test_smtp_settings.py`. **Visibility only** – no button, control or table behaviour is exercised, nothing is created, edited, deleted or sent, and no SMTP connection is made. All 11 test items carry `regression` and `smoke` and use `authenticated_page`.

The `smtp_settings` fixture expands the **"My Account"** sidebar menu (only while collapsed), clicks **"SMTP Settings"**, waits for the table request `GET /api/v1/smtp/list` and the URL. Not tested: Add New, SMTP creation, connection, authentication or validation, Status, the row Action buttons (edit/delete), sorting, pagination, Show entries behaviour, email sending, and every other My Account page (My Profile, Billing, Card Setting, Email Templates are never opened).

| # | Test | Verifies |
|---|---|---|
| 1 | `test_smtp_settings_opens_from_my_account_menu` | **Navigation:** My Account sub-menu expanded, URL `/smtp-settings`, "SMTP Settings" heading, SMTP Settings stays the selected link (`aria-current="page"`) |
| 2 | `test_page_header_elements_are_visible` | Heading, breadcrumb, + Add New |
| 3 | `test_show_entries_control_is_visible` | Show entries dropdown |
| 4 | `test_table_is_visible` | SMTP Settings table |
| 5–10 | `test_table_header_is_visible[<header>]` | S.No, SMTP Host, SMTP Port, SMTP Username, Status, Action |
| 11 | `test_empty_state_is_visible_while_no_smtp_setting_exists` | **Dynamic:** table and its first body row always visible; with no data – empty-state cell and "No SMTP settings yet"; with data – no empty-state cell, and heading, + Add New and Show entries still visible |

**Dynamic no-data handling:** nothing about the rows is hardcoded. The empty-state row is the one cell that spans every column (`td[colspan]`), so `data_rows` is the body rows without it. When SMTP settings exist later, test 11 checks the table and the page controls instead of the empty-state message, so it does not fail for a missing empty state.

SMTP Settings facts observed on 2026-09-23 (read-only inspection; only the "My Account" menu and its "SMTP Settings" link were clicked):
- The list request is `GET /api/v1/smtp/list?page_no=1&no_of_rows=10`; the page object matches it on the path only, so the query string may change.
- The sortable column headers append a **sort glyph** (U+21C5), e.g. `SMTP Host⇅`, so `column_header()` matches the header name as a substring and never exactly. `S.No` and `Action` are not sortable. Note the header is `Action`, singular – unlike Email Templates' `Actions`.
- There is **no search/filter row** on this page: the only table control is the `Show <n> entries` select, which carries `aria-label="Entries per page"` (10 / 25 / 50 / 100).
- The "+ Add New" button starts with an **icon glyph** (`bi bi-plus-lg`), so its name is a substring match. The empty state holds **no** second Add button – only the envelope-gear icon and the message.
- The breadcrumb navigation (Dashboard / My Account / SMTP Settings) is `nav[aria-label="breadcrumb"]`. Once settings exist, `main` may hold a second navigation (Pagination), so the breadcrumb is always addressed by its name.
- The account currently has **no SMTP setting**, so the table body is a single `td[colspan="6"]` holding "No SMTP settings yet".

**Result:** Chromium, 2026-09-23: **11/11 passed** (2 min 26 s), first run, no fixes needed. The no-data branch of test 11 was the one exercised (the account is empty); the with-data branch is untested against real data. Not run on Firefox or WebKit. Nothing was created, edited, deleted or sent, and no SMTP connection was attempted.

**Files:** created `framework/locators/smtp_settings_locators.py`, `framework/pages/smtp_settings_page.py`, `tests/ui/test_smtp_settings.py`. Modified: `README.md` (this section and a change-log row).

### SMTP Settings – functional (create / edit / delete)

`tests/ui/test_smtp_settings_functional.py` – the **functional** counterpart; the 11 visibility tests above are unchanged. Run with `pytest tests/ui/test_smtp_settings_functional.py`. 8 test items, all `regression`, `functional` and `destructive`; they use `authenticated_page` and the same `SmtpSettingsPage` / `SmtpSettingsLocators`. At most **one** SMTP setting exists at a time, its SMTP Username is `AUTO_SMTP_<8 hex chars>`, and no pre-existing setting is ever touched: every action is addressed through that unique username.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_add_smtp_modal_opens_with_its_fields` | **Flow 1:** "+ Add New" opens the *Add SMTP Settings* modal; SMTP host, Port, Username, Password (`type="password"`), Encryption, From email, From name, Save and Cancel are visible; Cancel closes it |
| 2–7 | `test_save_creates_nothing_until_every_required_field_is_filled[nothing-filled / without-host / without-port / without-username / without-from-email / without-password]` | **Flow 1:** Save with one required field empty (and with nothing filled at all) sends **no** create request, keeps the modal open with the typed values, and creates no row. For `without-password` also: the field carries `is-invalid`, a visible message appears (read, never hardcoded) and Save is disabled |
| 8 | `test_create_edit_and_delete_an_smtp_setting` | **Flows 2–4:** creating one `AUTO_SMTP_*` setting (`POST /api/v1/smtp` → 200, modal closes, new row with the expected host / port / username, row count +1), editing it (values pre-loaded, host and From name changed, `PUT /api/v1/smtp/<id>` → 200, list and a reload show the new host, the modal re-opens with the new From name) and deleting it (confirmation "Delete SMTP settings?" naming the host, `DELETE /api/v1/smtp/<id>` → 200, row gone after a reload, row count back to its starting value) |

**Mandatory-field coverage:** SMTP host, Port, Username, Password and From email are each left empty once, plus the all-empty case. Asserted in every case: no create request was sent, the modal stayed open with what was typed, and no row with that username exists after a reload. The password case additionally asserts the invalid state, the visible message and the disabled Save.

**Clean-up strategy:** the `smtp_cleanup` fixture collects the usernames a test creates – each one is appended **before** Save, so a setting created by a step that later failed is still removed. In teardown it reloads the list, deletes every registered row that is still there and verifies it is gone. It refuses any username that does not start with the configured prefix (`AUTO_SMTP_`), so a manual setting can never be deleted. Anything it cannot remove fails the teardown by name; because that is a teardown error, it is **added to** the original test failure rather than replacing it. The create/edit/delete test also deletes its own record, so the fixture usually finds nothing left.

**Sensitive credential handling:** the SMTP values come from `framework.config.get_sandbox_smtp()` and are overridable through `SHP_TEST_SMTP_HOST`, `_PORT`, `_PASSWORD`, `_FROM_EMAIL`, `_FROM_NAME`, `_ENCRYPTION` and `_USERNAME_PREFIX` (see `.env.example`). Nothing here is a real mail credential: the defaults point at the non-routable host `smtp.automation.test`, and the password defaults to a fresh random string per run. The password is kept out of `repr()` on `SandboxSmtp`, is typed through `fill_secret` (the log line reads "value hidden"), and is never asserted on, printed, screenshotted or written to this file. The application never returns it – the Edit modal shows an empty *Password (leave blank to keep)* field – so the stored value is deliberately not verified. **No mail is ever sent and no mail server is contacted:** the tests only store and remove a configuration row.

SMTP Settings facts observed while building these tests on 2026-09-23:
- The modal titles are **"Add SMTP Settings"** and **"Edit SMTP Settings"**; there is no `role="dialog"`, so each modal is the shown `.modal.show` holding its own title. The delete confirmation is the same kind of modal, titled **"Delete SMTP settings?"**, and its body quotes the host ("Delete the SMTP config for "…"? This cannot be undone.").
- Modal labels are not linked to their controls, so every field is the sibling after its label; the **Password** sits inside an `input-group` next to a "Show password" toggle, so it is the input *inside* the label's following `div`. The label text differs between Add ("Password *") and Edit ("Password (leave blank to keep)"), so labels are matched from their start.
- **From name carries no asterisk** – the application treats it as optional although the reference screenshot lists it as required. **Encryption** is a select of `tls` / `ssl` / `none`, pre-selected as `tls`, so neither field can be left empty by a test.
- **Validation is incomplete:** a save with a missing host, port, username or From email is rejected **silently** – no request, no `is-invalid`, no message, and Save stays enabled. Only a missing **password** produces proper feedback: `is-invalid` on the field, "Password is required." under it, and Save disabled until it is filled. The tests assert the silent cases on what does hold (no request, no record) and log what the application showed, so they will not break once the missing validation is added.
- Requests: create is `POST /api/v1/smtp`, update `PUT /api/v1/smtp/<id>`, delete `DELETE /api/v1/smtp/<id>`; each is followed by the list request. There is **no success toast** – the modal closing and the refreshed row are the only indication. A new setting is created **Active**, which the tests read from the row rather than assume.
- The application **does not verify the SMTP connection on save**: the fake `.test` host is stored without any connection attempt, which is what makes these tests safe to run.
- Row actions are plain **Edit** and **Delete** buttons; the row columns are S.No, SMTP Host, SMTP Port, SMTP Username, Status, Action.

**Result:** Chromium, 2026-09-23: **8/8 passed** for `test_smtp_settings_functional.py`, and **19/19 passed** (5 min 29 s) re-run together with the 11 visibility tests. Two fixes were needed while writing them: Save turns disabled after an invalid save (so an early "Save stays enabled" assertion was wrong), and `to_have_class` had to become `to_contain_class`. The account was verified to hold **0 SMTP settings** afterwards – no automation record left behind. Not run on Firefox or WebKit. No mail was sent, no SMTP connection was made, and no pre-existing SMTP setting was created, edited or deleted.

**Files:** created `tests/ui/test_smtp_settings_functional.py`. Modified: `framework/locators/smtp_settings_locators.py` (modal, delete-dialog and row locators; `CREATE_API_PATH`, `RECORD_API_PATH`, the three titles), `framework/pages/smtp_settings_page.py` (modal, save, edit, delete and reload actions; create-request recording), `framework/config.py` (`SandboxSmtp`, `get_sandbox_smtp`), `.env.example` (the `SHP_TEST_SMTP_*` block), `README.md` (this sub-section and a change-log row).

## E2E tests

`tests/integration/test_e2e_login_to_logout.py` – one happy-path journey, `test_user_journey_from_login_to_logout`, from the login page to sign-out in **one browser session**. Markers: `e2e`, `regression` and `destructive`. `destructive` is needed because the journey creates and deletes data, so CI runs it only in the single Chromium `data_writing` job. Run with `pytest tests/integration/test_e2e_login_to_logout.py` or `pytest -m e2e`. This is the first test in `tests/integration/` (see the growth rule).

**Login to logout.** The test does **not** use `authenticated_page`. It opens `/login` in pytest-playwright's fresh context and signs in once through `LoginPage.login()`, so the sign-in safety stop applies. It then signs out through the real header control and makes no further sign-in.

| # | Step | Verified |
|---|---|---|
| 1 | Login | Login heading → sign-in confirmed by the server → URL `/dashboard`, "Notifications" button visible, login form gone |
| 2 | Dashboard | "Welcome Seller", profile button, Orders chart heading |
| 3 | Manage Channel | Opened from the sidebar. Connects `AUTOMATION TEST CHANNEL <hex>` through the sandbox (Step 8 flow): success banner and new row. The journey continues in the tab the sandbox returns to, and the stale starting tab is closed |
| 4 | Active Listing | The new channel is listed in the Active Listing sub-menu. The first channel's listing opens: URL `/active-listing/`, heading, table |
| 5 | My Account → My Profile | URL `/profile` and heading (viewed only) |
| 6 | Manage Order | The new channel is listed in the Manage Order sub-menu. All Orders opens: URL `/orders`, heading, table |
| 7 | My Account → Billing | Heading and table (viewed only) |
| 8 | Help Center | Raises `AUTOMATION TEST CASE <hex>`: "Case raised successfully." and one listed row, whose Case Id is read. Then deletes it with the prefix-guarded `delete_automation_case()`: "Case deleted successfully." and the row is gone |
| 9 | Training Videos | URL `/training-videos`, heading, first video card (no video is played) |
| 10 | Upgrade Plan | Heading, plan cards load, a current plan is marked (the plan is never changed) |
| 11 | Customer | Heading and table (viewed only) |
| 12 | Manage Channel | The automation channel is deleted through the three-stage delete; the popup closes and the row is gone |
| 13 | Sign out | Header profile button → "Sign out": URL `/login`, login heading visible, signed-in header gone. `/dashboard` is then requested in the same tab and redirects to `/login` |

Module order follows the sidebar accordion: expanding one menu collapses the others. My Profile and Billing both sit under My Account, so the Manage Order step comes between them. That way `open_from_sidebar()` always expands My Account instead of collapsing it.

**Reuse.** Every step uses the existing page objects and locators. Added for this test: `DashboardLocators.sign_out_button` (header `button` named "Sign out", matched as a substring because of its icon glyph) and `DashboardPage.sign_out()`.

**Clean-up and restoration.**
- Each record is registered in the `automation_records` fixture **before** it is submitted, and cleared once the journey has verified its deletion.
- When the test fails midway, the fixture teardown opens a new page in the same signed-in context. It deletes the leftover channel with `delete_channel()` and the leftover case with `delete_automation_case()`. Both calls refuse anything without the automation prefix.
- A record that cannot be deleted is reported as a teardown ERROR naming it, next to the test's own failure.
- Profile, password, plan, Auto-Pay and every existing channel and case are only viewed.
- **Expected end state:** nothing left behind. Known exceptions: a run that is killed (not merely failing) leaves its channel or case behind (delete by hand), and the Help Center Case Id counter advances.

Sign-out facts observed on 2026-09-16 (two read-only inspection scripts, four valid sign-ins, no wrong password):
- The profile button opens a dropdown (`.dropdown-menu.show`, no menu role) holding the account's email, "My Profile" and "Sign out" buttons.
- "Sign out" sends `POST /api/v1/auth/logout` (200) and lands on `/login`. Afterwards, `/dashboard` and `/profile` redirect to `/login`.
- Another session signed in separately stays signed in, so the E2E sign-out does not affect the stored `authenticated_page` session.
- **Observation, not asserted:** a copy of the session token taken before sign-out still loads `/dashboard` with API calls answering 200. The server does not appear to revoke the token on logout. This is a possible security finding for the product owner. The test checks only the signed-out browser session.

**Result:** Chromium, 2026-09-16: **1/1 passed** (27 s) on the first run. The log shows all 13 steps. The clean-up teardown was not needed, because the case (09161039211) and the channel were deleted inside the journey. No password in `reports/` or `test-results/`. Not run on Firefox or WebKit.

Limitations: the journey needs an enabled eBay sandbox connection (as tests 28–30), and at least one channel in the Active Listing sub-menu. It also relies on the accordion behaviour above. The marker table in [Test categories](#test-categories-markers) (19 `destructive` items) was not updated in this step: with this test, `-m destructive` selects 20 of 193 Chromium items.

**Files:** created `tests/integration/test_e2e_login_to_logout.py`. Modified: `framework/locators/dashboard_locators.py`, `framework/pages/dashboard_page.py`, `README.md` (this section only).

## Test categories (markers)

Registered in `pytest.ini`. Strict mode is on, so an unregistered or misspelled marker fails the run.

| Marker | Meaning |
|---|---|
| `smoke` | Critical checks that the application is up and usable |
| `sanity` | Quick focused checks of one area after a change |
| `regression` | Broad behavioural coverage, run before releases |
| `functional` | Verifies a feature against its expected behaviour |
| `api` | Exercises the backend API directly, without a browser |
| `integration` | Validates behaviour across layers (UI / API / DB) |
| `e2e` | Complete user workflow from start to finish |
| `authentication` | Login, logout and session handling |
| `permissions` | Role and access-control rules |
| `destructive` | Writes application data (create / edit / delete) and cleans it up again. CI runs these in **one chromium job only** (see [Continuous integration](#continuous-integration-github-actions)) |
| `shared_state` | Changes a setting of the shared automation account (profile field, password, plan) and restores it. A subset of `destructive`; two of these must never run at the same time |

**Which tests carry them** (25 items of 363 are `destructive`, 9 of them `shared_state`):

| Module | `destructive` tests | Also `shared_state` |
|---|---|---|
| `test_manage_channel.py` | Tests 28–30 (connect, delete, sidebar sub-menus) – each creates and deletes its own `AUTOMATION TEST CHANNEL <hex>` | – |
| `test_help_center.py` | Tests 15–24, 26, 27 – each run raises and deletes its own `AUTOMATION TEST CASE <hex>`. Test 25 (closed-case chat) is read-only and is **not** marked | – |
| `test_my_profile.py` | Tests 16, 20, 21 (numeric Full Name, Save Profile, Change Password) | All three |
| `test_upgrade_plan.py` | Test 15 (downgrade + upgrade back) | Yes |
| `test_card_setting.py` | Tests 3–7 – each run adds and removes its own sandbox test cards and restores the account's original default card. Tests 1 and 2 are read-only and are **not** marked | All five |

Selection: `pytest -m "not destructive"` (nothing is written), `pytest -m destructive` (the data-writing tests), `pytest -m shared_state` (the account-state tests only).

## Browser support

- Chromium, Firefox and WebKit, selected with `--browser` (default: Chromium). Headless by default; `--headed` to watch.
- Every UI test is written once; pytest-playwright runs it per selected browser, and the browser name is part of the test id (e.g. `test_x[firefox]`).
- Tests that do not use browser fixtures (e.g. API tests) are not repeated per browser.
- Per-test exceptions: `@pytest.mark.skip_browser("webkit")` / `@pytest.mark.only_browser("chromium")`.

## Failure evidence, logs and reports

| Output | Location | When |
|---|---|---|
| Full-page screenshot | `test-results/<test-folder>/test-failed-1.png` | Every failed UI test |
| Playwright trace | `test-results/<test-folder>/trace.zip` | Every failed UI test |
| Video | `test-results/<test-folder>/video.webm` | Only with `--video retain-on-failure` |
| Run log | `reports/pytest.log` | Every run |
| JUnit XML report | `reports/junit.xml` | Every run (for CI) |
| Terminal summary | console (`-ra`) | Every run: failed, errored and skipped tests with reasons |

- `<test-folder>` is the slugified test id including the browser, e.g. `tests/ui/test_login.py::test_register_link_is_visible[firefox]` → `tests-ui-test-login-py-test-register-link-is-visible-firefox`.
- `test-results/` is emptied by pytest-playwright at the start of each run; `reports/` is overwritten each run.
- Open a trace with: `python -m playwright show-trace test-results/<folder>/trace.zip`
- `reports/pytest.log` records, per test: `START`, then `PASSED` / `FAILED` (with the failure reason) / `SKIPPED` (with reason) / `ERROR in setup|teardown`, plus important framework actions (e.g. the base URL in use). Framework and page code logs through `logging.getLogger(__name__)`; no custom logging module is needed.

## GitHub repository

The project is ready to be pushed as-is. Nothing is pushed, committed or branched by the framework; that is done by hand.

**Committed:** `README.md` (this document), `requirements.txt`, `pytest.ini`, `.env.example`, `.gitignore`, `.github/workflows/automation-tests.yml`, and the source under `framework/` and `tests/`.

**Never committed** (`.gitignore`): `.env` and any other `.env.*` except `.env.example`, `.venv/` / `venv/` / `env/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/`, `.coverage`, `htmlcov/`, the generated `reports/`, `test-results/`, `playwright-report/`, `screenshots/`, `videos/`, `*.log`, and local IDE / OS files (`.vscode/`, `.idea/`, `*.code-workspace`, `.DS_Store`, `Thumbs.db`, `desktop.ini`).

No password, token or machine-specific path is in a committed file: credentials are read only through `framework/config.py` from the environment or the git-ignored `.env`, and no source file contains an absolute local path.

Suggested branches: `development` (day-to-day work) and `main` (release). Both trigger the pipeline automatically.

### GitHub Secrets

Add these three under **Settings → Secrets and variables → Actions → Repository secrets**. The names are exactly the environment variables the framework already reads, so no code changes for CI:

| Secret | Contents |
|---|---|
| `SHP_BASE_URL` | URL of the live SHP application, e.g. `http://<host>:8080` |
| `SHP_USERNAME` | Email address of the dedicated automation account |
| `SHP_PASSWORD` | Password of that account |

No other secret is required by any existing test (the eBay connect flow uses SHP's own sandbox and submits an empty form, D36).

Secrets are passed to the test step as environment variables only. GitHub masks them in the log, the framework keeps the password out of logs, traces, reports and failure screenshots (see [Keeping the password out of logs, traces and reports](#keeping-the-password-out-of-logs-traces-and-reports)), and no workflow step ever echoes a secret value. The reachability check prints only the HTTP status, not the URL.

## Continuous integration (GitHub Actions)

Workflow: `.github/workflows/automation-tests.yml`. Everything runs automatically; no test is manual-only and no test is excluded from CI because it writes data.

### Automatic triggers

| Trigger | What runs |
|---|---|
| `push` to `development` | Chromium: read-only tests, then the data-writing tests |
| `pull_request` to `development` or `main` | Chromium: read-only tests, then the data-writing tests |
| `push` / merge to `main` | Full suite: read-only tests on Chromium, Firefox and WebKit, then the data-writing tests on Chromium |
| `schedule` – nightly, 01:30 UTC | Same as `main`: full cross-browser regression |
| `workflow_dispatch` | Available for a manual re-run; never required |

### Execution flow

| Job | Runs | Command |
|---|---|---|
| `setup` | Checkout → Python 3.13 (pip cache) → `pip install -r requirements.txt` → `pytest --collect-only -q` (configuration and imports must be valid) → reachability check of `<SHP_BASE_URL>/login` (HTTP 2xx/3xx, 3 retries) → decide the browser scope | – |
| `read_only` (matrix per browser) | Installs that browser with `playwright install --with-deps` and runs every test that writes nothing | `pytest -m "not destructive" --browser <browser> --video retain-on-failure` |
| `data_writing` | **After every `read_only` job has finished**, Chromium only: the create / edit / delete and account-state tests, including their clean-up and restoration | `pytest -m destructive --browser chromium --video retain-on-failure` |
| `result` | Always runs: writes the PASS / FAIL summary and fails the run if any stage did not pass | – |

The same tests are reused through markers; nothing is duplicated per job.

### Concurrency protection

The suite runs against **one live account**, so conflicting runs are prevented at three levels:

1. **Workflow level** – `concurrency: group: shp-live-automation, cancel-in-progress: false`. A second run (any branch, PR or the schedule) **queues** until the running one is finished. It is never cancelled, so a run that is in the middle of restoring the password or the plan is always allowed to complete.
2. **Job level** – `data_writing` `needs` every `read_only` job, so the account-changing tests never run beside a job that is signing in with the `.env` password. (A read-only job signing in while the password test holds the temporary password would fail.)
3. **Inside a run** – tests run in one process, sequentially (no `pytest-xdist`), so no two tests touch the account at the same time. The `shared_state` tests run in the single Chromium `data_writing` job, never in a browser matrix.

### Cross-browser strategy

Chromium, Firefox and WebKit stay supported. On `main` and the nightly schedule the read-only tests run on all three in parallel, which is safe because they change nothing. The `destructive` tests run **once, on Chromium only**, so the same account-changing test can never run simultaneously in several browsers and corrupt the state. On `development` pushes and pull requests the scope is Chromium, for a fast feedback loop.

### Live test safety in CI

The rules the data-writing tests already follow, and which CI depends on:

- **Automation-owned data only.** Everything a test creates carries a unique identifiable name: `AUTOMATION TEST CHANNEL <8 hex>` (D33) and `AUTOMATION TEST CASE <8 hex>` / `Automation test case description <8 hex>`.
- **Never other people's data.** `ManageChannelPage.delete_channel()` and `HelpCenterPage.delete_automation_case()` raise for any name or description without the automation prefix, so no existing channel or case can be deleted by a test, a teardown or a future caller. The account's real `EBAY` channel is asserted to still exist after the channel tests.
- **Capture before change, restore after.** My Profile tests 16 and 20 read the original value first and save it back in a `finally` block; test 21 changes the password to a temporary one and changes it straight back to the `.env` password; the Upgrade Plan test captures the current plan and the Auto-Pay state, downgrades, validates and upgrades back, with a `finally` that reloads and changes back if the original plan is not current. Auto-Pay is set to match its original state before every confirmation, so it never changes.
- **Clean-up runs even when the test fails.** The `connected_channel` fixture deletes the channel in its teardown if the test did not; the module-scoped `created_cases` fixture deletes every case the module raised, in a fresh context, whether the tests passed or failed, and attempts every case even after one fails.
- **A failed clean-up fails the run and names what is left.** The Help Center teardown ends in `pytest.fail("Clean-up failed; automation cases left in the account: …")` listing each Case Id and description; the password test fails with `PASSWORD NOT RESTORED` and the server's message; the plan test fails with `RESTORE FAILED: '<plan>' is not the current plan`. These are reported **next to** the original test failure (a teardown problem is an ERROR, never a replacement for the FAILED test), so the real cause is never hidden.
- **Expected end state:** after a run the account holds no automation channel and no automation case, the profile fields, password and plan are as they were. Known exceptions: a run that is **killed** (not merely failing) skips the teardown and leaves its `AUTOMATION TEST CHANNEL <hex>` / `AUTOMATION TEST CASE <hex>` records behind, and every plan test adds rows to the Billing history.

### Reports and artifacts

Each test job uploads, whenever files exist (`if-no-files-found: ignore`, 14-day retention):

| Artifact | Contents |
|---|---|
| `read-only-<browser>` | `reports/` (`pytest.log`, `junit.xml`) and `test-results/` (failure screenshot, `trace.zip`, `video.webm`) |
| `data-writing-chromium` | The same for the data-writing job |

Videos are kept in CI (`--video retain-on-failure`) on top of the screenshots and traces that `pytest.ini` already keeps for every failure. Local runs are unchanged.

### PASS / FAIL

- Every test passed and every clean-up succeeded → the `result` job writes **PASS ✅** to the run summary and the workflow is green.
- Any failure, error (including a teardown that could not clean up or restore), or an unreachable site → **FAIL ❌**, the `result` job exits non-zero and the run is red, with the artifacts above attached.
- pytest exit codes map straight to the job status: `0` pass, `1` failures/errors, `2` interrupted (including the sign-in safety stop), `4` usage error, `5` no tests collected.
- Missing configuration is an **error**, not a skip (D7), so CI can never pass silently because a secret is not set.

## Architecture decisions

| # | Decision | Reason |
|---|---|---|
| D1 | Use **pytest-playwright** instead of custom browser fixtures | Cross-browser, headed/headless and failure artifacts are built in and maintained upstream |
| D2 | Screenshot (full page) + trace kept for failures by default; video opt-in | Evidence for every failure without slowing passing runs |
| D3 | Default run is headless Chromium; other browsers via `--browser` | Fast default; cross-browser on demand or in CI |
| D4 | Native pytest logging configured in `pytest.ini` + result hooks in `tests/conftest.py` | No extra logging framework or module |
| D5 | Native reporting only (terminal, JUnit XML, log file, artifacts) | No third-party reporting system until one is required and approved |
| D6 | API tests will use **Playwright's built-in HTTP client** (`APIRequestContext`) | No extra dependency; can reuse the browser's authenticated session for UI → API checks. HTTPX only if a limitation is found |
| D7 | Missing credentials cause an **error**, not a skip | CI must never pass silently because configuration is missing |
| D8 | Project-local `.venv` with pinned direct dependencies | Reproducible, isolated from globally installed packages |
| D9 | `--import-mode=importlib`, no `__init__.py` in test folders | Test files with the same name can exist in different layers |
| D10 | pytest `strict = true` | Misspelled markers, unknown config keys and similar mistakes fail immediately |
| D11 | `SHP_USERNAME` holds whatever the login form's user field expects – confirmed in Step 2 to be the account's **email address** | Name agreed at project start; the login page has an Email field only |
| D12 | Page Object Model with four layers: locators → page actions (`BasePage`) → page object → tests | Selectors change in one place; tests read as user intent; shared actions (navigation, logging) are written once |
| D13 | Locator classes build Playwright `Locator` objects from the `Page` instead of storing selector strings | Keeps Playwright's recommended role-based locators and auto-waiting; locators are lazy, so building them costs nothing |
| D14 | Assertions live in tests only, using `expect(...)` on locators exposed as `page_object.locators.<name>` | Web-first assertions retry until the page settles, avoiding flaky checks and fixed waits |
| D15 | Pages the login page leads to (Forgot Password, Register, Dashboard) are identified by URL + one element only, kept in `LoginLocators` | Confirms the navigation without automating those modules; they get their own locators/page objects when approved |
| D16 | A sign-in the server does not confirm raises `AuthenticationError`, which stops the whole run | Protects the test account from lockout; never retry with the same credentials |
| D17 | Validation tests abort all `/api/**` requests in the browser and assert none was sent | Proves "no authentication request" and guarantees nothing reaches the server |
| D18 | Signed-in tests reuse one sign-in per browser via in-memory storage state (`authenticated_page`) | Fewer real sign-ins, faster tests, still independent; SHP keeps its token in `localStorage` and allows parallel sessions |
| D19 | Tracing is stopped completely while credentials are typed and sent | Pausing a trace chunk still records network bodies, which contain the password |
| D20 | Signed-in check uses the header "Notifications" button, not the user-name button or "Welcome ..." text | Present on every signed-in page and independent of the account's name |
| D21 | Dashboard visibility checks are grouped into 3 tests by page area (sidebar, header, content), each asserting every element of its area | Three page loads per browser instead of one per element; a failure names the missing element's locator and the failure screenshot shows the whole page |
| D22 | `LoginPage.DASHBOARD_PATH` (sign-in landing route, used by `authenticated_page`) is kept alongside `DashboardPage.PATH` | Leaves the verified login code unchanged; both are `/dashboard` |
| D23 | A training video is identified by its **title**, taken from the page's own `Play <title>` button name and the player's `title`; cards with a repeated title are skipped when a test picks a video | Works without `data-testid`, ids or positions, and different cards can hold the same YouTube video, so the embed URL cannot identify a card |
| D24 | "Really playing" is read from the `video` element inside the YouTube embed (not paused **and** position advancing), not from the iframe's presence or YouTube's player CSS classes | Proves actual playback rather than a mounted player, and does not depend on YouTube's internal markup |
| D25 | The "Training videos" sidebar entry is declared again in `TrainingVideosLocators` instead of importing `DashboardLocators` | Each page's locators stay self-contained; the shared sidebar is one line per page that clicks it |
| D26 | Manage Channel tests widen the viewport to 1600×900 (`ManageChannelPage.FULL_TABLE_VIEWPORT`) before opening the page | The page removes its last two columns from the DOM below that width; testing them at the default 1280 px would need the "Show all columns" button, and the task is visibility without clicking |
| D27 | Each column header is its own parametrized test, unlike the grouped dashboard visibility tests (D21) | The eight headers are one list in the locators; a parametrized run names the missing header in the test id and still reports the other seven, without extra page loads (the fixture is per test, the sign-in is reused) |
| D28 | The current page indicator is located by the CSS class `li.active`, the single documented exception to the "no CSS classes" rule | SHP marks the current page with a class only – there is no `aria-current`, id or distinct accessible name to use instead |
| D29 | The "Add a new connection" popup is scoped by the CSS class `.modal.show`, the second documented exception to the "no CSS classes" rule | The modal has no `role="dialog"`, id or heading-based container to scope by; `.show` is on the open modal only, so the same locator also proves the popup is closed |
| D30 | Popup tests press Next **only** with an empty channel name, and always leave through Cancel | Proves the Next button and its validation without ever handing over to eBay, so the suite cannot create a channel while the connect flow is unautomatable |
| D31 | ~~The add-channel flow is split: the SHP-side popup is automated now, the eBay connect and delete steps wait for an eBay account~~ **Superseded in Step 8:** the connect step does not leave the application – it opens SHP's own local dev sandbox – so no eBay account is needed and the whole flow is automated | The assumption behind the split (a hand-over to eBay's real sign-in page) turned out to be wrong once the flow was inspected |
| D32 | `channel_row(name)` is the one locator that reads channel data, matching the name cell exactly | The delete flow (and the "nothing was created" check) must address exactly one row by name and must never match the real EBAY channel by accident |
| D33 | Every channel the framework creates is named `AUTOMATION TEST CHANNEL <8 random hex characters>`, and `ManageChannelPage.delete_channel()` **raises** for any name without that prefix | A unique name makes the created row addressable even if a run is repeated or several browsers run at once; the prefix check makes deleting a real channel impossible, in a test or in a clean-up |
| D34 | `authorize_in_sandbox()` returns a **new page object** bound to the tab the sandbox opened | The authorisation lands in that tab; the tab the connection started from is stale. Returning the page object makes the switch explicit instead of hiding a second page inside the old one |
| D35 | The final delete confirmation is located by the accessible name "Delete permanently" only – no explicit wait for the countdown | The button is named "Please wait *n*s" while it counts down, so the locator cannot match too early; Playwright's auto-waiting covers the delay, and the disabled countdown button is asserted separately |
| D36 | The sandbox sign-in form is submitted **empty** | It is SHP's own fake sign-in ("any credentials are accepted") and it accepts an empty form, so the framework holds no marketplace credentials at all – nothing to store, mask or leak |
| D37 | My Profile fields are located through their **label text** – `MyProfileLocators._field()` finds the `<label>` and takes the first following control of the wanted kind (`xpath=following::input\|select\|textarea[1]`). This is the one documented use of XPath, the third exception to the locator-strategy rules | The page's controls have no accessible name, `name`, `id` or `aria-label`, and its labels are not linked to them, so role-based locators cannot address them. The visible label is the only stable anchor; the alternatives (Bootstrap classes, `nth` positions) break on any layout change, while the label text is what the test is actually about. The Email and Mobile controls sit one level deeper than the rest, which the `following` axis covers, so all fields share one rule |

## Test data and CRUD safety

- Destructive operations (create / edit / delete of application data) are never run without explicit approval of the specific scope.
- Tests create and clean up their own clearly identifiable records; existing SHP data is never modified or deleted.
- Tests must be independent: no test relies on another test having run first.
- **Manage Channel is the first module that writes data** (approved in Step 8). The naming convention and the safety mechanism are D33: a created channel is always `AUTOMATION TEST CHANNEL <8 random hex characters>`, and `ManageChannelPage.delete_channel()` raises `ValueError` for anything else, so the account's real `EBAY` channel cannot be deleted by a test, a teardown or a future caller.
- Each of tests 28–29 creates exactly one channel and deletes it again; the `connected_channel` fixture's teardown deletes it if the test itself did not. A full cross-browser run therefore creates and removes 6 channels (2 per browser).
- **Every data-writing test carries the `destructive` marker, and those that change a shared account setting also carry `shared_state`** (added in Step 21 for CI; see [Test categories](#test-categories-markers)). CI runs `destructive` in a single Chromium job, after the read-only jobs, so no two of them ever run at the same time.
- The popup tests (14–27) still create nothing (see D30); the test channel name `AUTOMATION TEST CHANNEL` is only typed there, never submitted.

## Known limitations

- Only Login, Dashboard visibility, Training Videos, Manage Channel (visibility, the connection popup, connect and delete) and My Profile visibility are automated. Not covered: logout, the "Enter a valid email address" message, Forgot Password and Register flows, dashboard values/behaviour (counts, charts, date-range filter, card and menu navigation, search, notifications, profile menu), and every other sidebar module.
- My Profile: not covered – the photo upload, the Change Email / Change Phone OTP flows, the Billing sub-menu entry, the native date picker's calendar pop-up (Date of Birth is typed into the field, not picked from the calendar), wrong or invalid passwords (lockout risk), and saving any field other than Company Name. Other field rules are not tested beyond those listed. The functionality tests ran on **Chromium only**; they have not been run on Firefox or WebKit.
- My Profile tests 16, 20 and 21 **write to the account** and restore it themselves. If a run is killed between a change and its restore, the account keeps the test value: Company Name `SHP Automation Test Company`, or the **temporary password `tester1`** instead of the `.env` password. In that case, restore it by hand before the next run, or every sign-in will fail. Do not run these tests in parallel browsers or processes against the same account: a concurrent password change would break the other run's restore.
- Test 17 needs at least one of the first 10 other countries to have states, and one of the first 10 of its states to have cities. Test 19 needs the application to offer a postal-code example for the account's country (it does for the current one).
- My Profile fields are matched on their **label text** (D37), so an application copy change ("Full Name", "Pincode", "Date of Birth", …) breaks the affected locator; the failing test names the label. For the same reason a label whose text is a substring of another label's text would become ambiguous – the three password fields already are ("New Password" is inside "Confirm New Password"), which is why they are located by placeholder instead.
- The My Profile avatar is matched on `aria-label` containing "profile photo"; the automation account currently has **no** photo (`aria-label="No profile photo"`). If the application names the element differently once a photo exists, that locator must be re-checked against an account that has one.
- **Manage Channel – the connect/delete flow is automated against the sandbox only (no longer blocked).** The Step 7 blocker was based on a wrong assumption: the connect step never reaches eBay. The environment runs SHP's **local dev sandbox**, whose sign-in is served by SHP itself and accepts anything, including an empty form, so no eBay account, 2FA handling or credential storage is needed. **What this does not prove:** that a connection against the **real** eBay works. On an environment wired to `ebay.com` or `sandbox.ebay.com`, tests 28–29 would stop at eBay's own sign-in page (unknown DOM, possible 2FA/captcha) and fail. Re-inspecting and re-verifying the flow is required before pointing the suite at such an environment.
- Tests 28–29 depend on the popup offering eBay as an enabled platform and on the sandbox banner reading exactly "eBay channel connected successfully."; a copy change breaks them. The delete stages are matched on their headings ("Delete this channel?", "Checking before we continue…", "Confirm once more") and the button names ("Yes, delete", "Delete permanently") for the same reason.
- The delete countdown is currently 5 seconds; the test allows 20 s for the last stage to appear. A longer countdown would need that limit raised.
- The connect flow relies on the browser allowing SHP to open the sandbox tab. It is a user-gesture popup and works headless in Chromium, Firefox and WebKit; a stricter popup policy would break `authorize_in_sandbox()`.
- If a connect test is interrupted between the authorisation and the clean-up (e.g. the run is killed), the created `AUTOMATION TEST CHANNEL <hex>` channel stays in the account and must be removed by hand.
- Manage Channel: apart from the popup and the connect/delete journey, visibility only. Not covered – channel row content, filter behaviour (Search, Reset, Connection options), the "Show ... entries" and sorting behaviour, pagination behaviour, row expansion, the "Show all columns" button and the folded-column layout below 1600 px, the Help dialog, the popup's "×" close button, the delete modal's Cancel and "×" buttons (only the full three-stage delete is exercised), and the Edit / Re-auth / Product / Order actions. Connections for Shopify, Temu, Amazon and Walmart are not testable: the application disables them ("Coming soon"). The pagination tests assert that Previous, Next and the page indicator are **visible**, not enabled; with one page of channels Previous and Next are disabled.
- Tests 27, 28 and 29 expect the account's existing channel to be named exactly **EBAY** (they assert it is still present); if that channel is renamed or removed, `EXISTING_CHANNEL_NAME` must be updated.
- Manage Channel visibility depends on the account having at least one channel: with an empty table the page may render an empty state instead of the headers and pagination, which these tests would report as failures.
- Training Videos: video content (titles, descriptions, authors, dates, durations), unavailable-video cards, scrolling/pagination and player controls (pause, seek, fullscreen) are not covered. The playback tests depend on **youtube.com being reachable** from the machine running them, and on the page holding at least two playable videos with distinct titles; otherwise they fail (they do not skip).
- A dashboard test stops at its first missing element, so other missing elements in the same area are reported only once that one is fixed.
- "Welcome Seller" is checked as exact text; if SHP personalises the greeting per account or role, that locator must change.
- Wrong-password, invalid-credential and lockout scenarios are intentionally **not** tested (account lockout risk); they need a disposable account and explicit approval.
- `BasePage._untraced()` relies on Playwright's "Must start tracing" error message to detect whether tracing is on (there is no public flag). If a Playwright upgrade changes it, sign-in tests fail loudly (no silent leak); re-check after upgrading Playwright.
- The account's email address (not the password) appears in failure tracebacks (`Credentials(username=...)`) and in the failure screenshot of a sign-in test.
- Database validation is not available until database access details are provided.
- Role/permission testing needs one account per role; roles are not defined yet.
- Git is not installed on the development machine yet and the repository has not been initialised, so the project is GitHub-**ready** but not yet pushed. The push, the branches and the repository itself are done by hand.
- Verified on Windows 11 only so far; Linux/macOS/CI commands are documented but not yet exercised. The GitHub Actions workflow is syntactically validated and its pytest selections are verified locally (19 `destructive`, 173 other of 192 Chromium items), but it has not yet run on GitHub, so the Linux browser install and the first live CI run are still unproven.
- CI concurrency is protected per repository (`concurrency: shp-live-automation`). Two runs in **different** repositories or a local run started while CI runs would still meet on the same live account; avoid running the suite locally while a CI run is in progress.

## Next pending step

Awaiting instruction. Nothing further is started without approval.

**Step 21 (2026-09-16) is complete:** the project is GitHub-ready and the automatic GitHub Actions pipeline is in place. Outstanding for it: initialise the repository and push by hand, add the three repository secrets, and let the first CI run prove the Linux browser install and the live run.

My Profile functionality is complete (21/21 on Chromium, password restored). Outstanding: the My Profile functionality tests have not been run on Firefox or WebKit, the full suite has not been re-run since Step 10 (expected 74 on Chromium), and it has not been run cross-browser since Step 7.

## Change log

| Date | Change | Files |
|---|---|---|
| 2026-09-11 | Step 1 – Foundation: pinned dependencies, pytest configuration (strict mode, markers, logging, screenshots/traces on failure, JUnit report), environment-based configuration, shared fixtures (`base_url`, `credentials`) and result-logging hooks. Created `.venv` and installed Chromium, Firefox and WebKit. Verified: markers registered, config errors and password masking, base-URL override with relative navigation, failure screenshot + trace per browser, log file and JUnit report. | Created: `README.md`, `requirements.txt`, `pytest.ini`, `.env.example`, `.gitignore`, `framework/__init__.py`, `framework/config.py`, `tests/conftest.py` |
| 2026-09-11 | Step 2 – Login page UI: inspected the live login DOM (read-only), added the Page Object Model layers (locators, shared page actions, page object) and 10 login page tests (page load, heading, email/password fields, eye toggle, Forgot Password and Register links and their target pages, Sign in button). Verified: 10/10 passed on Chromium, Firefox and WebKit; `-m smoke` selects the 5 smoke tests; a deliberately failing login check produced `test-failed-1.png` + `trace.zip`; actions appear in `reports/pytest.log`. No credentials submitted, no application data changed. | Created: `framework/locators/__init__.py`, `framework/locators/login_locators.py`, `framework/pages/__init__.py`, `framework/pages/base_page.py`, `framework/pages/login_page.py`, `tests/ui/test_login.py`. Modified: `README.md` |
| 2026-09-11 | Step 3 – Login functionality: inspected the live page, front-end bundle and one valid sign-in (read-only). Added valid sign-in (button and Enter key), dashboard redirect, signed-in header check, session persistence after reload, client-side validation for empty email/password with all API requests blocked, input acceptance, password-not-logged check, and the reusable `authenticated_page` fixture. Added lockout safety (`AuthenticationError` stops the run) and password protection in logs, errors, traces and failure evidence. Merged the "link is visible" tests into the navigation tests and split masking into its own test (10 → 16 tests). Verified: 16/16 passed on Chromium, Firefox and WebKit; `-m smoke` selects 6 tests; secret scan of `test-results/` (tracing on) and `reports/` found no password; a simulated rejected sign-in (answered inside the browser, never sent to the server, temporary test file deleted afterwards) stopped the run with exit code 2 and produced a screenshot and trace without the password. Found and fixed during verification: pausing a trace chunk still recorded the sign-in request body. No wrong credentials were ever submitted; no application data changed. | Modified: `framework/pages/base_page.py`, `framework/pages/login_page.py`, `framework/locators/login_locators.py`, `tests/conftest.py`, `tests/ui/test_login.py`, `.env.example`, `README.md`. Created: none |
| 2026-09-12 | Step 5 – Training Videos: inspected the live page and its player implementation after one valid sign-in (read-only; only the "Training videos" sidebar entry was clicked). Added training-video locators, the `TrainingVideosPage` page object (sidebar navigation, picking playable videos, starting one, reading real playback state) and 5 tests covering the 7 requested cases: page opens, heading visible, cards visible, a video starts and really plays, and only one video plays at a time. Uses the existing `authenticated_page` fixture, logger and failure-evidence handling. Verified: 5/5 passed on Chromium, Firefox and WebKit; full suite 72/72 on all three browsers. No application data changed. | Created: `framework/locators/training_videos_locators.py`, `framework/pages/training_videos_page.py`, `tests/ui/test_training_videos.py`. Modified: `README.md` |
| 2026-09-12 | Step 6 – Manage Channel visibility: inspected the live page DOM after one valid sign-in (read-only; only the "Manage Channel" sidebar entry was clicked, nothing on the page itself). Added manage-channel locators, the `ManageChannelPage` page object (sidebar navigation, full-table viewport) and 13 visibility tests: page opens with its heading, page header area, filter bar, table and "Show ... entries" control, one parametrized test per column header (8), and the pagination area. Found during inspection: the page folds "Config Date" and "Cron Config Time Slot" out of the DOM below 1600 px, so the tests widen the viewport first. Uses the existing `authenticated_page` fixture, logger and failure-evidence handling. Verified: 13/13 passed on Chromium, Firefox and WebKit; full suite 111/111 on all three browsers. Nothing on the page was clicked and no application data changed. | Created: `framework/locators/manage_channel_locators.py`, `framework/pages/manage_channel_page.py`, `tests/ui/test_manage_channel.py`. Modified: `README.md` |
| 2026-09-12 | Step 7 – Manage Channel "Add a new connection" popup: inspected the popup's live DOM only (read-only; "+ Add New" clicked, a platform selected and Next pressed with an empty name – nothing submitted). Added popup locators (platform list, heading, Channel Name field and its validation message, Next / Cancel), a `channel_row(name)` locator, five page actions (`open_add_connection_popup`, `select_platform`, `enter_channel_name`, `continue_connection`, `cancel_connection_popup`) and 14 test items in 6 test functions: popup opens, 5 platform options visible, 4 disabled "Coming soon" platforms, eBay selectable (reveals the Channel Name field), the field keeps the test value, Next without a name is rejected, Cancel closes the popup leaving no new channel and the EBAY channel intact. Moved the `smoke` marker from the module to the 5 visibility tests so the popup tests are `functional` only (smoke count unchanged). Found during inspection: the popup is one step, not a wizard; it has no dialog role; only eBay is enabled. **Blocked:** steps 8–20 of the requested flow (continue → eBay sign-in → success message → new row → 3-stage delete) need an eBay account, which is not configured; nothing was created or deleted. Verified: 27/27 on Chromium, 81/81 across Chromium, Firefox and WebKit; full suite 153/153 (one transient network error re-run and passed). | Modified: `framework/locators/manage_channel_locators.py`, `framework/pages/manage_channel_page.py`, `tests/ui/test_manage_channel.py`, `README.md`. Created: none |
| 2026-09-12 | Step 8 – Manage Channel connect + delete: inspected the live connect and delete flows (four read-only inspection scripts run outside the suite; the one channel they created was deleted again, leaving only the account's `EBAY` channel). **Found: the connect step never leaves SHP** – it opens the application's own local dev sandbox, which accepts an empty sign-in form – so the Step 7 eBay blocker and D31 no longer apply and no credentials are involved. Added locators for the success banner, the row Delete button and the three delete stages, a `SandboxAuthorizationLocators` class for the sandbox tab, the `authorize_in_sandbox()` action (returns the page object of the tab the authorisation lands on), four delete actions including the prefix-guarded `delete_channel()`, and 2 tests behind a `connected_channel` fixture: the sandbox authorisation connects the channel and returns to `/channels` with the new row, and the three-stage delete removes only that channel. Unique channel names (`AUTOMATION TEST CHANNEL <hex>`) and a `ValueError` guard make deleting the real channel impossible. All 27 existing Manage Channel tests are unchanged. Verified: 29/29 on Chromium, 87/87 on Chromium, Firefox and WebKit. **The full suite was not re-run** – that run was stopped before it started. | Modified: `framework/locators/manage_channel_locators.py`, `framework/pages/manage_channel_page.py`, `tests/ui/test_manage_channel.py`, `README.md`. Created: none |
| 2026-09-12 | Step 9 – My Account → My Profile visibility: inspected the live page once (read-only; only the "My Account" sidebar menu and its "My Profile" entry were clicked, nothing on the page itself). Added my-profile locators, the `MyProfilePage` page object (sidebar navigation only) and 7 test items in 5 test functions: the page opens at `/profile` with its heading, one parametrized test per section heading (3), and one test per section for its fields – Personal & Contact Information (10 controls), Business & Address Information (10 controls) and Security (7 controls). Found during inspection: the page's form controls have **no accessible name, `name`, `id` or `aria-label`** and its labels are not linked to them, so fields are located through their label text (new decision D37, the one documented use of XPath); the three password fields use their placeholders instead. Uses the existing `authenticated_page` fixture, logger and failure-evidence handling; all existing tests are unchanged. Verified: 7/7 on Chromium, 21/21 on Chromium, Firefox and WebKit, full suite 60/60 on Chromium. Nothing was edited, uploaded, saved or submitted and no application data changed. | Created: `framework/locators/my_profile_locators.py`, `framework/pages/my_profile_page.py`, `tests/ui/test_my_profile.py`. Modified: `README.md` |
| 2026-09-14 | Step 10 – My Profile functionality: inspected only the needed live elements and the Profile page's front-end code (read-only; the one write was a Save with every value unchanged). Added message and option constants, State/City option lists, a Pincode error message and a toast locator; page actions for reload, reading and choosing dropdown options (returning the states or cities the application loaded), Save Profile, restoring a field, entering passwords, eye toggles, Change Password, and `handling_passwords()` (tracing off, password fields emptied). Added 14 functional test items in 10 functions: Username read-only; Full Name, Company Name, Address 1, Address 2 and Description accept text; numeric-only Full Name rejected (with restore); Gender, Timezone and Date of Birth; the Country → State → City dependency checked against the application's own state and city answers; Pincode with the application's postal example; Save Profile persists after a reload and is restored; password change to the temporary password with all three eye icons checked, then an immediate restore to the `.env` password. The 7 visibility tests are unchanged except that `smoke` moved from the module to those tests, so the functional tests are not smoke. Verified: 21/21 on Chromium; the sign-in of that run used the `.env` password (restored); no password in `reports/` or `test-results/`. Found and fixed during the first run: dropdown options load after the field renders. | Modified: `framework/locators/my_profile_locators.py`, `framework/pages/my_profile_page.py`, `tests/ui/test_my_profile.py`, `README.md`. Created: none |
| 2026-09-14 | Step 11 – My Account → Billing visibility: added billing locators, the `BillingPage` page object (sidebar navigation, full-table viewport) and 12 visibility test items in 5 functions: heading, Current Plan section (name, amount, status/date area), Show entries control and table, one parametrized test per column header (8), and the pagination area. Visibility only; no values checked and nothing clicked. **Not run and not verified against the live DOM** (see Billing tests). Existing tests unchanged. | Created: `framework/locators/billing_locators.py`, `framework/pages/billing_page.py`, `tests/ui/test_billing.py`. Modified: `README.md` |
| 2026-09-14 | Step 12 – Help Center visibility: added help-center locators, the `HelpCenterPage` page object (sidebar navigation, full-table viewport) and 14 visibility test items in 6 functions: heading, breadcrumb and Raise New Case, filter bar (7 controls), Show entries and table, one parametrized test per column header (9), and the entry count and pagination. The first run failed 2 tests (unnamed dropdowns, search placeholder); fixed from the failure snapshot. Verified: 14/14 on Chromium. Nothing clicked, no data checked or changed; existing tests unchanged. | Created: `framework/locators/help_center_locators.py`, `framework/pages/help_center_page.py`, `tests/ui/test_help_center.py`. Modified: `README.md` |
| 2026-09-16 | Step 21 – GitHub and CI/CD readiness: registered the `destructive` and `shared_state` markers and tagged the 19 data-writing test items (3 Manage Channel, 12 Help Center, 3 My Profile, 1 Upgrade Plan – the last 4 also `shared_state`); no test was rewritten, removed or made manual-only. Added the GitHub Actions pipeline `.github/workflows/automation-tests.yml`: automatic on pushes to `development` and `main`, on pull requests to both, and nightly at 01:30 UTC (plus `workflow_dispatch`), with `setup` (install, `--collect-only` configuration check, site reachability, browser scope) → `read_only` per browser (`-m "not destructive"`) → `data_writing` on Chromium (`-m destructive`, after every read-only job) → `result` (PASS/FAIL summary). Workflow-level `concurrency: shp-live-automation` with `cancel-in-progress: false` queues overlapping runs so the live account cannot be corrupted. Secrets `SHP_BASE_URL`, `SHP_USERNAME`, `SHP_PASSWORD` are passed as environment variables only and never printed. Artifacts (`reports/`, `test-results/` – logs, JUnit XML, screenshots, traces, videos) are uploaded per job for 14 days. Extended `.gitignore` (venv/env, egg-info, coverage, playwright-report, screenshots, videos, `*.log`, workspace and OS files) and noted the CI secret names in `.env.example`. Verified: YAML parses; `pytest --collect-only --strict-markers --strict-config` collects 192 items with no warning; `-m destructive` selects 19, `-m "not destructive"` 173, `-m shared_state` 4; every destructive test has a `finally` block or fixture teardown that restores or deletes and fails loudly when it cannot; no credential or local path in any committed file. Nothing was pushed, committed or branched, and no test was executed against the live site. | Created: `.github/workflows/automation-tests.yml`. Modified: `pytest.ini`, `.gitignore`, `.env.example`, `tests/ui/test_manage_channel.py`, `tests/ui/test_help_center.py`, `tests/ui/test_my_profile.py`, `tests/ui/test_upgrade_plan.py`, `README.md` |
| 2026-09-22 | Fix – Training Video playback in CI: YouTube shows a bot check to GitHub-hosted runner IPs, so the 2 playback tests now run in a new `video_playback` job on a self-hosted runner and are deselected from `read_only`. No test or framework code changed. Verified locally: 5/5 Training Video tests passed. | Modified: `.github/workflows/automation-tests.yml`, `README.md` |
| 2026-09-22 | CI – removed the `video_playback` job: there is no self-hosted runner, and YouTube's bot check makes the 2 playback tests fail on GitHub-hosted runners. The tests stay in the suite (local runs only) and are still deselected from `read_only`. The Result job no longer waits for it. | Modified: `.github/workflows/automation-tests.yml`, `README.md` |
| 2026-09-22 | Listing → Common Listing: navigation, visibility (header, 10 filter controls, table, 17 column headers) and filters (4 text, Channel, Status, By Published Date, combined, Reset); dynamic data only. Verified: 30/30 on Chromium (see Listing → Common Listing tests). | Created: `framework/locators/common_listing_locators.py`, `framework/pages/common_listing_page.py`, `tests/ui/test_common_listing.py`. Modified: `README.md` |
| 2026-09-22 | Listing → Common Listing → Create Listing → Single Listing: menu options, navigation, visibility (8 sections, 29 fields with required markers, checkboxes, editor, image controls, action buttons), 8 section buttons, empty-form validation for Save as Draft and Send to Live (write requests blocked; nothing created). Verified: 51/51 on Chromium (see Create Listing → Single Listing). | Created: `framework/locators/single_listing_locators.py`, `framework/pages/single_listing_page.py`, `tests/ui/test_single_listing.py`. Modified: `framework/locators/common_listing_locators.py`, `framework/pages/common_listing_page.py`, `README.md` |
| 2026-09-23 | Create Listing → Single Listing navigation fix: "Single Listing" is now a sub-menu (Manual / Generate Listing By AI); the automated path selects **Manual**. Added `test_single_listing_offers_manual_and_ai_options`; AI flow not covered. All existing Single Listing tests kept. Verified: 52/52 on Chromium. | Modified: `framework/locators/common_listing_locators.py`, `framework/pages/common_listing_page.py`, `framework/pages/single_listing_page.py`, `framework/locators/single_listing_locators.py`, `tests/ui/test_single_listing.py`, `README.md` |
| 2026-09-24 | Fix – Upgrade Plan `test_subscription_summary_is_visible`: the third summary label is not fixed – the application renders `Renews on:` with a renewal date and `Active until:` without one. It was hardcoded as "Active until:" (true when the tests were written, Auto-Pay Off) and broke once the account's subscription auto-renews. `SUBSCRIPTION_LABELS` now holds only the two fixed labels, the new `RENEWAL_LABELS` / `renewal_item()` match either, and the test asserts exactly one renewal item is rendered. No application defect; no other test changed. Verified: 14/14 non-destructive Upgrade Plan tests on Chromium (the plan-changing test was not run, so the account's plan is untouched). | Modified: `framework/locators/upgrade_plan_locators.py`, `tests/ui/test_upgrade_plan.py`, `README.md` |
| 2026-09-23 | Setup → Import Setting functional: the whole Add Setup workflow (step 1 Type & Name, step 2 Upload & Map), mandatory-field validation (3 combinations + the unmapped file), CSV and XLSX created end to end, all 4 Setup Types with their own mapping fields, the 4 filters + combined + Reset, edit of a saved mapping and delete with confirmation. 13 new test items, all `destructive`, each with a finalizer that deletes only the names it registered; a full run leaves **zero** automation import settings. The 12 visibility tests are unchanged. **Found: XLS cannot be used** – the backend cannot read a legacy `.xls` header (openpyxl), so test 9 pins that behaviour; also the View Linking modal is cached per record and the list is not refetched after an update. Verified: 13/13 and 25/25 with the visibility file on Chromium, twice (see Import Setting functional tests). | Created: `tests/ui/test_import_setting_functional.py`, `test_data/import_setting_sample.csv`, `test_data/import_setting_sample.xls`, `test_data/import_setting_sample.xlsx`. Modified: `framework/locators/import_setting_locators.py`, `framework/pages/import_setting_page.py`, `README.md` |
| 2026-09-23 | Setup → Import Setting visibility: navigation through the Setup sub-menu, page header, 8 filter controls, the table, 7 column headers and the dynamic no-data state (empty-state message, + Add Setup and Read the guide first). Visibility only; nothing clicked beyond the sidebar and the auto-opening guide dialog's ×. Verified: 12/12 on Chromium, both with an empty list and with import settings present (see Setup → Import Setting tests). | Created: `framework/locators/import_setting_locators.py`, `framework/pages/import_setting_page.py`, `tests/ui/test_import_setting.py`. Modified: `README.md` |
| 2026-09-16 | Fix – Help Center cross-browser failures: in a multi-browser run, pytest ran a test of another browser between one browser's Help Center tests. That switch tore down `created_cases`, whose clean-up deleted the shared automation case, but the `_automation_cases` cache kept pointing at it. The priority, status, date range, combined filter, reset and chat tests then failed on Firefox and WebKit. `_automation_cases` now depends on `created_cases`, so both are torn down together and the next test raises a fresh case. Diagnosed from `reports/pytest.log` and failure screenshots. Verified: `tests/ui/test_help_center.py` 81/81 passed on Chromium, Firefox and WebKit in one run (8 min 31 s). Tests of other browsers again ran in the middle of each browser's tests, and every clean-up finished without error. | Modified: `tests/ui/test_help_center.py`, `README.md`. Created: none |
| 2026-09-11 | Step 4 – Dashboard visibility: inspected the live dashboard DOM after one valid sign-in (read-only, nothing clicked). Added dashboard locators, the `DashboardPage` page object and 3 visibility tests (sidebar branding and menu, header, content sections) using the existing `authenticated_page` fixture. Verified: 3/3 passed on Chromium, Firefox and WebKit; `-m smoke` now selects 9 tests. No application data changed. | Created: `framework/locators/dashboard_locators.py`, `framework/pages/dashboard_page.py`, `tests/ui/test_dashboard.py`. Modified: `README.md` |
| 2026-09-23 | My Account → Card Setting: navigation and page visibility, the Add Card modal and its controls, adding a sandbox test card without "Set as default" (masked number only, not default), Set default moving the badge, the "Remove card?" confirmation and delete, and adding a second sandbox card **with** "Set as default" (default immediately). Card data comes from `SHP_TEST_CARD*` environment variables only (Stripe **test** mode, `pk_test_…`); numbers and CVCs are never hardcoded, logged, reported or traced, and no payment, charge or subscription change is triggered. Two-layer clean-up: the flow removes its own cards, and the module-scoped `card_state` fixture removes anything left and restores the original default, failing loudly and naming the card when it cannot. Verified: 7/7 on Chromium, twice, the second run with `--tracing on` and a secret scan of `reports/` and all 7 traces (no card number found); the account finished with its four original cards and its original default (see My Account → Card Setting tests). | Created: `framework/locators/card_setting_locators.py`, `framework/pages/card_setting_page.py`, `tests/ui/test_card_setting.py`. Modified: `framework/config.py`, `.env.example`, `README.md` |
| 2026-09-23 | My Account → Email Templates visibility: navigation through the My Account sub-menu, page header, 6 filter/table controls, the table, 6 column headers and the dynamic no-data state ("No email templates yet"). Visibility only; nothing clicked beyond the sidebar. Verified: 11/11 on Chromium against an empty list (see My Account → Email Templates tests). | Created: `framework/locators/email_templates_locators.py`, `framework/pages/email_templates_page.py`, `tests/ui/test_email_templates.py`. Modified: `README.md` |
| 2026-09-23 | My Account → Email Templates **functional**: the Add Template modal, required-field validation for Name / Subject / Body (HTML), creating one `AUTO_EMAIL_TEMPLATE_<id>` template, Name search, Status filter, combined Name+Status filter (including the non-matching status), Reset, and delete through the row action and its confirmation. One template per run, deleted by the flow and again by the `template_cleanup` finalizer, which only ever deletes `AUTO_EMAIL_TEMPLATE_*` names and reports any leftover by name. Found: required-field validation is silent (no request, no error, no invalid state) and there is no success toast. Verified: 5/5 on Chromium, first run; the 11 visibility tests still pass and the account ended with 0 templates (see My Account → Email Templates tests). | Created: `tests/ui/test_email_templates_functional.py`. Modified: `framework/locators/email_templates_locators.py`, `framework/pages/email_templates_page.py`, `README.md` |
| 2026-09-23 | My Account → SMTP Settings visibility: navigation through the My Account sub-menu (SMTP Settings stays the selected link), page header, Show entries control, the table, 6 column headers (S.No, SMTP Host, SMTP Port, SMTP Username, Status, Action) and the dynamic no-data state ("No SMTP settings yet"). Visibility only; nothing clicked beyond the sidebar, no SMTP created, tested or sent. Verified: 11/11 on Chromium against an empty list (see My Account → SMTP Settings tests). | Created: `framework/locators/smtp_settings_locators.py`, `framework/pages/smtp_settings_page.py`, `tests/ui/test_smtp_settings.py`. Modified: `README.md` |
| 2026-09-23 | My Account → SMTP Settings **functional**: the Add SMTP Settings modal, required-field validation for SMTP host / Port / Username / Password / From email (each left empty once, plus the all-empty case), creating one `AUTO_SMTP_<id>` setting, editing it (host and From name, verified after a reload) and deleting it through the row action and its "Delete SMTP settings?" confirmation. One record per run, deleted by the flow and again by the `smtp_cleanup` finalizer, which only ever deletes rows carrying the `AUTO_SMTP_` username prefix and reports any leftover by name. SMTP values come from `SHP_TEST_SMTP_*` environment variables with fake `.test` defaults and a per-run random password; the password is never logged, printed or asserted on, no mail is sent and no mail server is contacted. Found: only a missing password is flagged (`is-invalid`, "Password is required.", Save disabled) – a missing host, port, username or From email is rejected silently; there is no success toast; the application does not verify the SMTP connection on save. Verified: 8/8 on Chromium, and 19/19 together with the 11 visibility tests, which still pass; the account ended with 0 SMTP settings (see My Account → SMTP Settings tests). | Created: `tests/ui/test_smtp_settings_functional.py`. Modified: `framework/locators/smtp_settings_locators.py`, `framework/pages/smtp_settings_page.py`, `framework/config.py`, `.env.example`, `README.md` |
