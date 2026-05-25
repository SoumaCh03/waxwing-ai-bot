"""Gemini-backed intent detection and conversational response generation."""

from __future__ import annotations

import logging

from google import genai

LOGGER = logging.getLogger(__name__)

VALID_INTENTS = {"WEATHER", "MECHANIC", "FUEL", "EMERGENCY", "GENERAL_CHAT"}


class GeminiService:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def detect_intents(self, user_message: str) -> list[str]:
        prompt = f"""
Analyze the user message and return ALL relevant intents as comma-separated
labels from this list:

WEATHER
MECHANIC
FUEL
EMERGENCY
GENERAL_CHAT

Examples:
bike stalled in rain = EMERGENCY,WEATHER,MECHANIC
need fuel = FUEL
hello = GENERAL_CHAT

Return only labels separated by commas.

User message:
{user_message}
"""

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
        except Exception as exc:
            LOGGER.exception("Gemini intent detection failed: %s", exc)
            return ["GENERAL_CHAT"]

        raw_text = (response.text or "").strip().upper()
        intents = [intent.strip() for intent in raw_text.split(",") if intent.strip()]
        filtered = [intent for intent in intents if intent in VALID_INTENTS]
        return filtered or ["GENERAL_CHAT"]

    def get_ai_response(self, user_message: str) -> str:
        prompt = f"""
You are WaxWing, a highly intelligent motorcycle roadside assistant.
Speak like a warm, fluent human assistant.
Be practical, conversational, emotionally reassuring, and concise.

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

