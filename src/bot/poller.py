"""Long-polling runner for local development (Telegram getUpdates).

This module implements a simple polling loop that fetches updates using
Telegram getUpdates and forwards them to the existing MessageRouter.
It intentionally reuses the same services and client instances as the
webhook app to avoid duplicating business logic.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.bot.telegram import TelegramClient
from src.config.settings import Settings, get_settings
from src.handlers.message_router import MessageRouter
from src.services.gemini_service import GeminiService
from src.services.places_service import PlacesService
from src.services.user_store import build_user_store
from src.services.weather_service import WeatherService
from src.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def run_polling(settings: Settings | None = None) -> None:
    """Start continuous polling and forward updates to MessageRouter."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    telegram = TelegramClient(
        settings.telegram_bot_token,
        timeout_seconds=settings.request_timeout_seconds,
    )
    router = MessageRouter(
        telegram=telegram,
        gemini=GeminiService(settings.gemini_api_key, settings.gemini_model),
        weather=WeatherService(
            settings.openweather_api_key,
            timeout_seconds=settings.request_timeout_seconds,
        ),
        places=PlacesService(
            settings.google_maps_api_key,
            timeout_seconds=settings.request_timeout_seconds,
        ),
        user_store=build_user_store(
            settings.firestore_collection,
            enable_firestore=settings.enable_firestore,
        ),
    )

    print("Running in POLLING mode")

    offset: int | None = None
    long_poll_timeout = 20

    while True:
        try:
            updates: list[dict[str, Any]] = telegram.get_updates(offset=offset, timeout_seconds=long_poll_timeout)
            if not updates:
                # No updates returned; loop again (getUpdates will block server-side up to long_poll_timeout)
                continue

            for update in updates:
                try:
                    router.handle_update(update)
                except Exception:
                    LOGGER.exception("Unhandled polling update error.")

                # update_id is required by Telegram API, but be defensive
                try:
                    update_id = int(update.get("update_id", 0))
                except Exception:
                    update_id = None

                if update_id is not None:
                    offset = update_id + 1

        except Exception:
            LOGGER.exception("Unhandled polling error; sleeping briefly before retrying.")
            time.sleep(5)
