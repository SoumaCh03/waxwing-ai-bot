"""Environment-driven application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is present in normal installs.
    load_dotenv = None


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


def _load_dotenv() -> None:
    if load_dotenv:
        load_dotenv()


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer.") from exc


def _get_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number.") from exc


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gemini_api_key: str
    openweather_api_key: str | None
    google_maps_api_key: str | None
    telegram_webhook_secret: str | None
    gemini_model: str
    firestore_collection: str
    request_timeout_seconds: float
    port: int
    log_level: str
    enable_firestore: bool

    def validate(self) -> None:
        missing = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")

        if missing:
            names = ", ".join(missing)
            raise ConfigError(f"Missing required environment variable(s): {names}.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_dotenv()

    settings = Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip() or None,
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", "").strip() or None,
        telegram_webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
        or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        firestore_collection=os.getenv("FIRESTORE_COLLECTION", "users").strip(),
        request_timeout_seconds=_get_float("REQUEST_TIMEOUT_SECONDS", 10.0),
        port=_get_int("PORT", 8080),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        enable_firestore=_get_bool("ENABLE_FIRESTORE", True),
    )
    settings.validate()
    return settings

