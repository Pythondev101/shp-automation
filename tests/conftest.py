"""Shared fixtures and hooks for every test layer.

Browser, context and page fixtures, cross-browser runs and failure evidence
(screenshots, traces, videos) come from pytest-playwright; see pytest.ini.
"""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import Page, StorageState
from pytest_playwright.pytest_playwright import CreateContextCallback

from framework.config import Credentials, get_base_url, get_credentials
from framework.pages.login_page import AuthenticationError, LoginPage

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    """Target URL: ``--base-url`` for a one-off run, otherwise SHP_BASE_URL.

    Overrides pytest-base-url's fixture; pytest-playwright passes it to every
    browser context, so pages can navigate with relative paths.
    """
    url = pytestconfig.getoption("base_url") or get_base_url()
    logger.info("Base URL: %s", url)
    return url


@pytest.fixture(scope="session")
def credentials() -> Credentials:
    """Automation account credentials; errors clearly if they are not configured."""
    return get_credentials()


@pytest.fixture(scope="session")
def _signed_in_storage() -> dict[str, StorageState]:
    """Browser storage after sign-in, per browser, kept in memory only (never written to disk)."""
    return {}


@pytest.fixture
def authenticated_page(
    new_context: CreateContextCallback,
    browser_name: str,
    credentials: Credentials,
    _signed_in_storage: dict[str, StorageState],
) -> Page:
    """A page signed in with the automation account, open on the dashboard.

    The first test that needs it signs in through the login form; later tests reuse
    that browser storage (SHP keeps its token in localStorage) in their own fresh
    context. Result: one sign-in per browser per run, and independent tests.
    """
    storage = _signed_in_storage.get(browser_name)
    if storage is None:
        page = new_context().new_page()
        login_page = LoginPage(page)
        login_page.open()
        login_page.login(credentials)
        _signed_in_storage[browser_name] = page.context.storage_state()
        return page
    page = new_context(storage_state=storage).new_page()
    logger.info("Reuse the signed-in session; open %s", LoginPage.DASHBOARD_PATH)
    page.goto(LoginPage.DASHBOARD_PATH)
    return page


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> None:
    """Stop the whole run after a sign-in the server did not confirm.

    SHP may deactivate an account after repeated failed sign-ins, so no further
    test may try again with the same credentials.
    """
    if call.excinfo is not None and call.excinfo.errisinstance(AuthenticationError):
        reason = (
            "Sign-in was not confirmed; run stopped so no further attempt can lock the account. "
            "Check SHP_USERNAME / SHP_PASSWORD before running again."
        )
        logger.error("STOPPED %s | %s", item.nodeid, reason)
        item.session.shouldstop = reason


def pytest_runtest_logstart(nodeid: str) -> None:
    logger.info("START   %s", nodeid)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Log one result line per test, plus any setup/teardown problem."""
    if report.when != "call" and report.passed:
        return
    if report.failed:
        # Like pytest, a failure outside the test body (setup/teardown) is an ERROR.
        status = "FAILED " if report.when == "call" else f"ERROR in {report.when}"
        crash = getattr(report.longrepr, "reprcrash", None)
        reason = crash.message.splitlines()[0] if crash else ""
        logger.error("%s %s | %s", status, report.nodeid, reason)
    elif report.skipped:
        reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else ""
        logger.info("SKIPPED %s | %s", report.nodeid, reason)
    else:
        logger.info("PASSED  %s", report.nodeid)
