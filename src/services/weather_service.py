"""OpenWeather integration."""

from __future__ import annotations

import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


class WeatherService:
    def __init__(
        self,
        api_key: str | None,
        timeout_seconds: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def get_live_weather(self, latitude: float, longitude: float) -> str:
        if not self._api_key:
            return "Weather lookup is not configured yet."

        try:
            response = self._session.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self._api_key,
                    "units": "metric",
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        except requests.RequestException as exc:
            LOGGER.exception("OpenWeather request failed: %s", exc)
            return "Unable to fetch live weather right now."
        except ValueError as exc:
            LOGGER.exception("OpenWeather returned invalid JSON: %s", exc)
            return "Unable to read the weather response right now."

        try:
            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            condition = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]
        except (KeyError, IndexError, TypeError) as exc:
            LOGGER.exception("OpenWeather response missing expected fields: %s", exc)
            return "Weather data is incomplete right now."

        return (
            "Live Weather Update\n\n"
            f"Temp: {temperature} C\n"
            f"Feels like: {feels_like} C\n"
            f"Condition: {condition}\n"
            f"Wind: {wind_speed} m/s\n\n"
            "Ride carefully if roads are wet."
        )

