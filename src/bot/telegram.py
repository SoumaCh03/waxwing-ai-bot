"""Small Telegram Bot API client."""

from __future__ import annotations

import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, bot_token: str, timeout_seconds: float = 10.0) -> None:
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._timeout_seconds = timeout_seconds
        self._session = requests.Session()

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            response = self._session.post(
                f"{self._base_url}/sendMessage",
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            LOGGER.exception("Telegram sendMessage failed for chat_id=%s: %s", chat_id, exc)
            return False

    def get_updates(self, offset: int | None = None, timeout_seconds: int = 20) -> list[dict[str, Any]]:
        """Fetch updates from Telegram using getUpdates (supports offset and long polling).

        Returns a list of update dicts or an empty list on error.
        """
        params: dict[str, Any] = {"timeout": timeout_seconds}
        if offset is not None:
            params["offset"] = offset

        try:
            # Allow a slightly larger client timeout than the long-poll timeout.
            client_timeout = max(self._timeout_seconds, timeout_seconds + 5)
            response = self._session.get(
                f"{self._base_url}/getUpdates",
                params=params,
                timeout=client_timeout,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                LOGGER.warning("Unexpected getUpdates response: %s", data)
                return []
            return data.get("result", []) or []
        except requests.RequestException as exc:
            LOGGER.exception("Telegram getUpdates failed: %s", exc)
            return []
