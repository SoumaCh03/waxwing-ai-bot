"""User state storage with Firestore and local fallback implementations."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from google.api_core.exceptions import GoogleAPIError
from google.cloud import firestore

LOGGER = logging.getLogger(__name__)


class UserStore:
    def save(self, chat_id: int | str, key: str, value: Any) -> None:
        raise NotImplementedError

    def get(self, chat_id: int | str, key: str) -> Any:
        raise NotImplementedError


class InMemoryUserStore(UserStore):
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = defaultdict(dict)

    def save(self, chat_id: int | str, key: str, value: Any) -> None:
        self._data[str(chat_id)][key] = value

    def get(self, chat_id: int | str, key: str) -> Any:
        return self._data[str(chat_id)].get(key)


class FirestoreUserStore(UserStore):
    def __init__(self, collection_name: str) -> None:
        self._client = firestore.Client()
        self._collection = self._client.collection(collection_name)

    def save(self, chat_id: int | str, key: str, value: Any) -> None:
        try:
            self._collection.document(str(chat_id)).set({key: value}, merge=True)
        except GoogleAPIError as exc:
            LOGGER.exception("Failed to save user state for chat_id=%s: %s", chat_id, exc)

    def get(self, chat_id: int | str, key: str) -> Any:
        try:
            document = self._collection.document(str(chat_id)).get()
        except GoogleAPIError as exc:
            LOGGER.exception("Failed to read user state for chat_id=%s: %s", chat_id, exc)
            return None

        if document.exists:
            return document.to_dict().get(key)
        return None


def build_user_store(collection_name: str, enable_firestore: bool = True) -> UserStore:
    if not enable_firestore:
        LOGGER.warning("Firestore disabled; using in-memory user store.")
        return InMemoryUserStore()

    try:
        return FirestoreUserStore(collection_name)
    except Exception as exc:  # Firestore can fail before emitting GoogleAPIError.
        LOGGER.warning(
            "Firestore unavailable; using in-memory user store. reason=%s",
            exc,
        )
        return InMemoryUserStore()

