"""User state storage with Firestore and local fallback implementations."""

from __future__ import annotations

import logging
import json
import sqlite3
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


class SQLiteUserStore(UserStore):
    def __init__(self, db_path: str = "state.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_state (
                        chat_id TEXT PRIMARY KEY,
                        state_json TEXT
                    )
                    """
                )
                conn.commit()
        except Exception as exc:
            LOGGER.exception("Failed to initialize SQLite database: %s", exc)

    def save(self, chat_id: int | str, key: str, value: Any) -> None:
        chat_id_str = str(chat_id)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT state_json FROM user_state WHERE chat_id = ?", (chat_id_str,))
                row = cursor.fetchone()
                data = json.loads(row[0]) if row else {}
                
                data[key] = value
                
                conn.execute(
                    "INSERT INTO user_state (chat_id, state_json) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET state_json = ?",
                    (chat_id_str, json.dumps(data), json.dumps(data))
                )
                conn.commit()
        except Exception as exc:
            LOGGER.exception("Failed to save user state in SQLite for chat_id=%s: %s", chat_id, exc)

    def get(self, chat_id: int | str, key: str) -> Any:
        chat_id_str = str(chat_id)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT state_json FROM user_state WHERE chat_id = ?", (chat_id_str,))
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    return data.get(key)
        except Exception as exc:
            LOGGER.exception("Failed to read user state in SQLite for chat_id=%s: %s", chat_id, exc)
        return None


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
        LOGGER.warning("Firestore disabled; using SQLite user store.")
        try:
            return SQLiteUserStore()
        except Exception as exc:
            LOGGER.warning("SQLite unavailable; using in-memory user store. reason=%s", exc)
            return InMemoryUserStore()

    try:
        return FirestoreUserStore(collection_name)
    except Exception as exc:  # Firestore can fail before emitting GoogleAPIError.
        LOGGER.warning(
            "Firestore unavailable; using SQLite user store. reason=%s",
            exc,
        )
        try:
            return SQLiteUserStore()
        except Exception as sqlite_exc:
            LOGGER.warning("SQLite fallback failed; using in-memory user store. reason=%s", sqlite_exc)
            return InMemoryUserStore()


