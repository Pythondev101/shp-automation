"""Single source of framework configuration.

Values come from real environment variables first, then from an optional
``.env`` file in the project root (git-ignored; see ``.env.example``).
Nothing else in the framework reads the environment directly.
"""

from __future__ import annotations

import os
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


def get_credentials() -> Credentials:
    """Login credentials of the dedicated automation account."""
    return Credentials(
        username=_require("SHP_USERNAME").strip(),
        password=_require("SHP_PASSWORD"),
    )
