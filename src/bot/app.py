"""Flask application factory for the Telegram webhook."""

from __future__ import annotations

import logging
import hmac
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request

from src.bot.telegram import TelegramClient
from src.config.settings import Settings, get_settings
from src.handlers.message_router import MessageRouter
from src.services.gemini_service import GeminiService
from src.services.places_service import PlacesService
from src.services.user_store import build_user_store
from src.services.weather_service import WeatherService
from src.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = Flask(__name__)
    app.config["PORT"] = settings.port

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

    executor = ThreadPoolExecutor(max_workers=4)

    def process_async(upd: dict) -> None:
        try:
            router.handle_update(upd)
        except Exception:
            LOGGER.exception("Unhandled async webhook processing error.")

    @app.get("/")
    def health_check():
        return jsonify({"service": "waxwing-ai-bot", "status": "ok"})

    @app.post("/")
    def telegram_webhook():
        if settings.telegram_webhook_secret:
            received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if not received_secret or not hmac.compare_digest(received_secret, settings.telegram_webhook_secret):
                LOGGER.warning("Rejected webhook request with invalid secret header.")
                return jsonify({"error": "unauthorized"}), 401

        update = request.get_json(silent=True)
        if not isinstance(update, dict):
            LOGGER.warning("Rejected webhook request with invalid JSON payload.")
            return jsonify({"error": "invalid payload"}), 400

        # Offload update processing to the background thread pool
        executor.submit(process_async, update)

        return "ok", 200

    return app

