"""Telegram message routing for WaxWing."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from src.bot.telegram import TelegramClient
from src.services.gemini_service import GeminiService
from src.services.places_service import PlacesService
from src.services.user_store import UserStore
from src.services.weather_service import WeatherService

LOGGER = logging.getLogger(__name__)


class MessageRouter:
    def __init__(
        self,
        telegram: TelegramClient,
        gemini: GeminiService,
        weather: WeatherService,
        places: PlacesService,
        user_store: UserStore,
    ) -> None:
        self._telegram = telegram
        self._gemini = gemini
        self._weather = weather
        self._places = places
        self._user_store = user_store

    def handle_update(self, update: dict[str, Any]) -> None:
        message = update.get("message")
        if not isinstance(message, dict):
            LOGGER.info("Ignoring update without message payload.")
            return

        chat = message.get("chat", {})
        chat_id = chat.get("id")
        if chat_id is None:
            LOGGER.warning("Ignoring message without chat id.")
            return

        if "text" in message:
            self.handle_text(chat_id, str(message["text"]))
            return

        if "location" in message:
            location = message["location"]
            self.handle_location(
                chat_id,
                float(location["latitude"]),
                float(location["longitude"]),
            )
            return

        self._telegram.send_message(
            chat_id,
            "I can help with text messages and shared locations.",
        )

    def handle_text(self, chat_id: int | str, text: str) -> None:
        message = text.lower().strip()
        if not message:
            self._telegram.send_message(chat_id, "Please send a message I can read.")
            return

        if message == "/start":
            self._telegram.send_message(
                chat_id,
                "Welcome to WaxWing.\n"
                "Your AI roadside riding assistant.\n"
                "How can I help you today?",
            )
            return

        if self._is_greeting(message):
            self._telegram.send_message(
                chat_id,
                f"{self._get_time_based_greeting()}, rider.\n"
                "I am WaxWing.\n"
                "Tell me what happened.",
            )
            return

        intents = self._gemini.detect_intents(text)
        if "EMERGENCY" in intents:
            self._telegram.send_message(
                chat_id,
                "I am with you.\n"
                "Please move yourself and the bike to a safe roadside position first.",
            )

        tools: list[str] = []
        if "WEATHER" in intents:
            tools.append("weather")
        if "MECHANIC" in intents:
            tools.append("mechanic")
        if "FUEL" in intents:
            tools.append("fuel")

        if tools:
            self._user_store.save(chat_id, "pending_tools", tools)
            self._send_location_request(chat_id)
            return

        self._telegram.send_message(chat_id, self._gemini.get_ai_response(text), parse_mode="Markdown")

    def handle_location(self, chat_id: int | str, latitude: float, longitude: float) -> None:
        pending_tools = self._user_store.get(chat_id, "pending_tools")
        if not pending_tools:
            self._telegram.send_message(
                chat_id,
                "Location received. Tell me what you need nearby: weather, fuel, or mechanic.",
            )
            return

        responses: list[str] = []
        if "weather" in pending_tools:
            responses.append(self._weather.get_live_weather(latitude, longitude))

        if "fuel" in pending_tools:
            fuel = self._places.search_nearby_places(latitude, longitude, "fuel pump")
            responses.append(self._places.format_places("Nearby Fuel Pumps", fuel))

        if "mechanic" in pending_tools:
            mechanics = self._places.search_nearby_places(
                latitude,
                longitude,
                "bike mechanic",
            )
            responses.append(self._places.format_places("Nearby Mechanics", mechanics))

        if responses:
            self._telegram.send_message(chat_id, "\n\n".join(responses))
        else:
            self._telegram.send_message(chat_id, "I could not match that location to a tool.")

        self._user_store.save(chat_id, "pending_tools", None)

    @staticmethod
    def _get_time_based_greeting() -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        if 12 <= hour < 17:
            return "Good afternoon"
        if 17 <= hour < 22:
            return "Good evening"
        return "Hello night rider"

    @staticmethod
    def _is_greeting(message: str) -> bool:
        normalized = re.sub(r"\s+", " ", message).strip()
        if normalized in {"good morning", "good afternoon", "good evening"}:
            return True

        words = set(re.findall(r"[a-z]+", normalized))
        return bool(words.intersection({"hi", "hello", "hallo", "hey"}))

    def _send_location_request(self, chat_id: int | str) -> None:
        keyboard = {
            "keyboard": [
                [
                    {
                        "text": "Send Current Location",
                        "request_location": True,
                    }
                ]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }

        self._telegram.send_message(
            chat_id,
            "Please share your location so I can assist further.",
            keyboard,
        )
