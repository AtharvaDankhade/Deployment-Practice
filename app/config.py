"""Configuration from environment variables (12-factor style).

Everything the container needs at runtime is injected via env vars so the same
image can run locally, in staging and in production without a rebuild.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    env: str
    log_level: str
    version: str


settings = Settings(
    env=_get("APP_ENV", "local"),
    log_level=_get("LOG_LEVEL", "INFO").upper(),
    version=_get("APP_VERSION", "1.0.0"),
)
