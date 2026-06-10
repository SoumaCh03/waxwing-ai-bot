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
            LOGGER.exception("Gemini intent detection failed: %s. Falling back to local brain.", exc)
            return self._fallback_detect_intents(user_message)

        return self._fallback_detect_intents(user_message)

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
            text = (response.text or "").strip()
            if not text:
                return self._fallback_get_ai_response(user_message)
            return text
        except Exception as exc:
            LOGGER.exception("Gemini response generation failed: %s. Falling back to local brain.", exc)
            return self._fallback_get_ai_response(user_message)

    def _fallback_detect_intents(self, user_message: str) -> list[str]:
        """Local keyword-based intent detection fallback."""
        message = user_message.lower().strip()
        intents = []

        emergency_keywords = {
            "emergency", "accident", "crash", "injured", "hurt", "ambulance",
            "police", "broke down", "broken down", "help", "sos"
        }
        weather_keywords = {
            "weather", "rain", "temp", "temperature", "forecast", "hot",
            "cold", "wind", "humidity", "rainy", "sunny", "climate"
        }
        mechanic_keywords = {
            "mechanic", "garage", "fix", "repair", "breakdown", "flat tire",
            "puncture", "service center", "workshop", "bike shop"
        }
        fuel_keywords = {
            "fuel", "gas", "petrol", "diesel", "pump", "refuel", "gas station",
            "petrol pump", "station"
        }

        import re
        words = set(re.findall(r"[a-z0-9']+", message))

        # Check multi-word phrases first
        if "broke down" in message or "broken down" in message:
            intents.append("EMERGENCY")
        if "service center" in message or "bike shop" in message:
            intents.append("MECHANIC")
        if "gas station" in message or "petrol pump" in message:
            intents.append("FUEL")

        # Check individual words
        if words.intersection(emergency_keywords) and "EMERGENCY" not in intents:
            intents.append("EMERGENCY")
        if words.intersection(weather_keywords) and "WEATHER" not in intents:
            intents.append("WEATHER")
        if words.intersection(mechanic_keywords) and "MECHANIC" not in intents:
            intents.append("MECHANIC")
        if words.intersection(fuel_keywords) and "FUEL" not in intents:
            intents.append("FUEL")

        if not intents:
            intents.append("GENERAL_CHAT")

        return intents

    def _fallback_get_ai_response(self, user_message: str) -> str:
        """Local template-based response generator fallback."""
        message = user_message.lower().strip()
        intents = self._fallback_detect_intents(user_message)

        import re
        words = set(re.findall(r"[a-z0-9']+", message))

        # Direct greeting check
        greetings = {"hi", "hello", "hey", "hallo", "greetings", "yo"}
        if words.intersection(greetings):
            return (
                "Hello rider! 🏍️\n\n"
                "I am *WaxWing*, your motorcycle roadside assistant.\n"
                "I'm currently running in local backup mode, but I can still help you with standard tasks! "
                "How can I help you today?"
            )

        if "EMERGENCY" in intents:
            return (
                "⚠️ *EMERGENCY RESPONSE*\n\n"
                "Please move yourself and your motorcycle to a safe roadside position first.\n"
                "Once you are safe, share your current location so I can try to find nearby emergency contacts or help."
            )

        if "WEATHER" in intents:
            return (
                "🌦️ *Weather Check*\n\n"
                "I can fetch live weather conditions for you. "
                "Please share your current location using the Telegram attachment button."
            )

        if "MECHANIC" in intents:
            return (
                "🔧 *Find a Mechanic*\n\n"
                "Need assistance or repairs? "
                "Please share your current location so I can search for nearby motorcycle mechanics and workshops."
            )

        if "FUEL" in intents:
            return (
                "⛽ *Find Fuel*\n\n"
                "Running low? "
                "Please share your current location so I can find the nearest fuel pumps and gas stations."
            )

        # Help request
        help_words = {"help", "info", "features", "capabilities", "what can you do"}
        if words.intersection(help_words) or ("what" in words and "do" in words):
            return (
                "🛠️ *WaxWing Bot Help (Backup Mode)*\n\n"
                "I am operating in backup mode because my AI brain is offline, but I can still perform local tasks:\n"
                "• *Weather*: Live weather conditions (say 'weather')\n"
                "• *Mechanics*: Find nearby bike workshops (say 'mechanic')\n"
                "• *Fuel*: Find nearby petrol stations (say 'fuel')\n\n"
                "To get started, simply type one of the keywords above and share your location when prompted."
            )

        return (
            "🤖 *WaxWing (Backup Mode)*\n\n"
            "I am currently operating in offline fallback mode because the AI assistant service is temporarily unreachable.\n\n"
            "However, my local tools are fully functional! You can search for *weather*, *fuel*, or a *mechanic* by mentioning them, or send a greeting to start a conversation."
        )


