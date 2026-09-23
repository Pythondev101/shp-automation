"""Single source of framework configuration.

Values come from real environment variables first, then from an optional
``.env`` file in the project root (git-ignored; see ``.env.example``).
Nothing else in the framework reads the environment directly.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# override=False: variables already set in the environment (e.g. in CI) win over .env.
load_dotenv(PROJECT_ROOT / ".env", override=False)


class ConfigError(RuntimeError):
    """Raised when a required configuration value is missing."""


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str = field(repr=False)  # keeps the password out of logs and tracebacks


def _require(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise ConfigError(
            f"Required environment variable {name} is not set. "
            "Add it to the .env file (copy .env.example) or set it in the environment."
        )
    return value


def get_base_url() -> str:
    """Base URL of the SHP application, without a trailing slash."""
    return _require("SHP_BASE_URL").strip().rstrip("/")


@dataclass(frozen=True)
class SandboxCard:
    """A payment-provider **test** card read from configuration.

    Never a real card: the application under test uses Stripe in test mode, and only
    Stripe's published test card numbers belong in the configuration. ``number`` and
    ``cvc`` are kept out of ``repr()``, so they never reach a log line, a pytest
    traceback or a report; ``str()`` shows the brand, the last four digits and the
    expiry, which is exactly what the application itself displays.
    """

    number: str = field(repr=False)
    expiry: str
    """Expiry as it is typed into the card form, ``MM/YY``."""
    cvc: str = field(repr=False)
    brand: str
    """Brand the application displays for this number, e.g. ``Visa``."""

    @property
    def last_four(self) -> str:
        return self.number[-4:]

    @property
    def expiry_label(self) -> str:
        """The expiry the way the application displays it, e.g. ``11/2030`` for ``11/30``."""
        month, _, year = self.expiry.partition("/")
        return f"{month}/20{year}" if len(year) == 2 else f"{month}/{year}"

    def __str__(self) -> str:
        return f"{self.brand} ****{self.last_four} exp {self.expiry_label}"


def get_sandbox_cards() -> tuple[SandboxCard, SandboxCard]:
    """The two sandbox test cards the Card Setting tests add and delete again.

    Raises ``ConfigError`` when they are not configured, so the tests skip instead of
    inventing card data. No card number is ever hardcoded in the framework.
    """
    cvc = _require("SHP_TEST_CARD_CVC").strip()
    return (
        SandboxCard(
            number=_require("SHP_TEST_CARD_NUMBER").strip().replace(" ", ""),
            expiry=_require("SHP_TEST_CARD_EXPIRY").strip(),
            cvc=cvc,
            brand=_require("SHP_TEST_CARD_BRAND").strip(),
        ),
        SandboxCard(
            number=_require("SHP_TEST_CARD_2_NUMBER").strip().replace(" ", ""),
            expiry=_require("SHP_TEST_CARD_2_EXPIRY").strip(),
            cvc=cvc,
            brand=_require("SHP_TEST_CARD_2_BRAND").strip(),
        ),
    )


@dataclass(frozen=True)
class SandboxSmtp:
    """SMTP settings the SMTP Settings tests save, read from configuration.

    Never a production mail account: the tests only store a configuration row and never
    connect to a mail server or send anything, so the defaults below point at a
    non-routable ``.test`` host. ``password`` is kept out of ``repr()``, so it never
    reaches a log line, a pytest traceback or a report.
    """

    host: str
    port: str
    password: str = field(repr=False)
    from_email: str
    from_name: str
    encryption: str
    """Value of the Encryption option, one of ``tls``, ``ssl``, ``none``."""
    username_prefix: str
    """Prefix of the unique username each test builds, e.g. ``AUTO_SMTP_``."""

    def __str__(self) -> str:
        return f"{self.host}:{self.port} ({self.encryption}, from {self.from_email})"


def _optional(name: str, default: str) -> str:
    value = os.environ.get(name, "")
    return value.strip() if value.strip() else default


def get_sandbox_smtp() -> SandboxSmtp:
    """The sandbox SMTP values the My Account → SMTP Settings tests create and delete again.

    Every value can be overridden through an environment variable (see ``.env.example``);
    the defaults are deliberately fake, so no real mail credential is ever needed or
    hardcoded. The password defaults to a freshly generated random string - it is never
    logged, printed or written to a report.
    """
    return SandboxSmtp(
        host=_optional("SHP_TEST_SMTP_HOST", "smtp.automation.test"),
        port=_optional("SHP_TEST_SMTP_PORT", "2525"),
        password=os.environ.get("SHP_TEST_SMTP_PASSWORD", "") or secrets.token_urlsafe(16),
        from_email=_optional("SHP_TEST_SMTP_FROM_EMAIL", "automation@example.test"),
        from_name=_optional("SHP_TEST_SMTP_FROM_NAME", "SHP Automation"),
        encryption=_optional("SHP_TEST_SMTP_ENCRYPTION", "tls"),
        username_prefix=_optional("SHP_TEST_SMTP_USERNAME_PREFIX", "AUTO_SMTP_"),
    )


def get_credentials() -> Credentials:
    """Login credentials of the dedicated automation account."""
    return Credentials(
        username=_require("SHP_USERNAME").strip(),
        password=_require("SHP_PASSWORD"),
    )
