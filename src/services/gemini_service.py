"""Gemini-backed intent detection and conversational response generation."""

from __future__ import annotations

import logging
import json
from pydantic import BaseModel

from google import genai
from google.genai import types

LOGGER = logging.getLogger(__name__)

VALID_INTENTS = {"WEATHER", "MECHANIC", "FUEL", "EMERGENCY", "GENERAL_CHAT"}


class IntentResponse(BaseModel):
    intents: list[str]


class GeminiService:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def detect_intents(self, user_message: str) -> list[str]:
        prompt = f"""
Analyze the user message and identify all relevant intents from the following list:
- WEATHER
- MECHANIC
- FUEL
- EMERGENCY
- GENERAL_CHAT

User message:
{user_message}
"""
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=IntentResponse,
                ),
            )
            if response.text:
                data = json.loads(response.text)
                raw_intents = data.get("intents", [])
                filtered = [
                    intent.strip().upper()
                    for intent in raw_intents
                    if intent.strip().upper() in VALID_INTENTS
                ]
                return filtered or ["GENERAL_CHAT"]
        except Exception as exc:
            LOGGER.exception("Gemini intent detection failed: %s", exc)

        return ["GENERAL_CHAT"]

    def get_ai_response(self, user_message: str) -> str:
        prompt = f"""
You are WaxWing, a highly intelligent motorcycle roadside assistant.
Speak like a warm, fluent human assistant.
Be practical, conversational, emotionally reassuring, and concise.
Use standard Telegram markdown for formatting (e.g. *bold* for emphasis, `code` for names/numbers).
Do not use nested markdown or HTML.

User message:
{user_message}
"""

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
        except Exception as exc:
            LOGGER.exception("Gemini response generation failed: %s", exc)
            return (
                "I am having trouble reaching the AI service right now. "
                "Please try again in a moment."
            )

        text = (response.text or "").strip()
        if not text:
            return "I could not generate a useful response. Please try rephrasing that."
        return text

