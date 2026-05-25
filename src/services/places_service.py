"""Google Places integration."""

from __future__ import annotations

import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


class PlacesService:
    def __init__(
        self,
        api_key: str | None,
        timeout_seconds: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def search_nearby_places(
        self,
        latitude: float,
        longitude: float,
        keyword: str,
    ) -> list[dict[str, Any]]:
        if not self._api_key:
            LOGGER.warning("Google Places lookup requested without GOOGLE_MAPS_API_KEY.")
            return []

        try:
            response = self._session.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "location": f"{latitude},{longitude}",
                    "radius": 3000,
                    "keyword": keyword,
                    "key": self._api_key,
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            LOGGER.exception("Google Places request failed: %s", exc)
            return []
        except ValueError as exc:
            LOGGER.exception("Google Places returned invalid JSON: %s", exc)
            return []

        results = data.get("results", [])
        return results if isinstance(results, list) else []

    @staticmethod
    def format_places(title: str, places: list[dict[str, Any]]) -> str:
        if not places:
            return f"{title}\nNo nearby results found."

        lines = [title, ""]
        for index, place in enumerate(places[:3], start=1):
            name = place.get("name", "Unknown")
            address = place.get("vicinity", "Address unavailable")
            rating = place.get("rating", "N/A")
            lines.extend(
                [
                    f"{index}. {name}",
                    f"Rating: {rating}",
                    f"Location: {address}",
                    "",
                ]
            )

        return "\n".join(lines).strip()

