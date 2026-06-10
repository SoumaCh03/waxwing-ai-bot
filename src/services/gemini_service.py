"""Gemini-backed intent detection and conversational response generation."""

from __future__ import annotations

import logging
import json
import random
import re
from datetime import datetime
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
            "police", "broke down", "broken down", "sos"
        }
        weather_keywords = {
            "weather", "rain", "temp", "temperature", "forecast", "hot",
            "cold", "wind", "humidity", "rainy", "sunny", "climate"
        }
        mechanic_keywords = {
            "mechanic", "garage", "fix", "repair", "breakdown", "flat tire",
            "puncture", "service center", "workshop", "bike shop", "spanner", "tool"
        }
        fuel_keywords = {
            "fuel", "gas", "petrol", "diesel", "pump", "refuel", "gas station",
            "petrol pump", "station"
        }

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
        """Local advanced conversational brain with warm, randomized responses."""
        message = user_message.lower().strip()
        words = set(re.findall(r"[a-z0-9']+", message))
        hour = datetime.now().hour

        # 1. TIME-AWARE GREETING MATCH
        morning_greetings = {"good morning", "morning", "g'morning"}
        afternoon_greetings = {"good afternoon", "afternoon"}
        evening_greetings = {"good evening", "evening"}
        night_greetings = {"good night", "goodnight", "night", "g'night"}
        standard_greetings = {"hi", "hello", "hey", "hallo", "greetings", "yo", "sup", "whats up", "what's up"}

        # Determine time period for dynamic context
        if 5 <= hour < 12:
            time_period = "morning"
        elif 12 <= hour < 17:
            time_period = "afternoon"
        elif 17 <= hour < 22:
            time_period = "evening"
        else:
            time_period = "night"

        is_greeting = (
            words.intersection(standard_greetings) or
            any(g in message for g in morning_greetings | afternoon_greetings | evening_greetings | night_greetings)
        )

        if is_greeting:
            # Check if user specified a time-greeting, otherwise use current time
            if any(g in message for g in morning_greetings):
                greeting_type = "morning"
            elif any(g in message for g in afternoon_greetings):
                greeting_type = "afternoon"
            elif any(g in message for g in evening_greetings):
                greeting_type = "evening"
            elif any(g in message for g in night_greetings):
                greeting_type = "night"
            else:
                greeting_type = time_period

            pools = {
                "morning": [
                    "Good morning, rider! 🌅 Early morning breeze is the best. Did you check your tire pressure before rolling out? How can I help you today?",
                    "Morning! ☀️ The roads are fresh and waiting. Where are we heading, or did something happen?",
                    "Rise and shine! 🏍️ Hope you've got a great route planned. How can I assist you on the road this morning?"
                ],
                "afternoon": [
                    "Good afternoon! ☀️ Stay hydrated out there, the sun is blazing. How's the ride going today?",
                    "Hey! Good afternoon. 🏍️ Cruising in the heat or took a break? What can I help you with?",
                    "Good afternoon, rider! Hope the roads are clear. What's on your mind?"
                ],
                "evening": [
                    "Good evening! 🌆 Sunset rides are pure magic. Watch out for dropping temperatures and changing light. How can I help you tonight?",
                    "Evening, rider! 🏍️ Heading home or heading out for a late run? What do you need assistance with?",
                    "Good evening! Wind is settling down. How's your bike behaving? Let me know what you need."
                ],
                "night": [
                    "Hello night rider! 🌌 Out for a late cruise? Stay safe, keep your visor clean, and watch out for high beams. What's on your mind?",
                    "Late night on the asphalt? 🌙 Make sure you're highly visible. I'm here if you need to find fuel, weather info, or a mechanic.",
                    "Good night, rider! 🏍️ Riding under the stars? Let me know how I can help you stay safe tonight."
                ]
            }
            return random.choice(pools[greeting_type])

        # 2. FAREWELL MATCH
        farewells = {"bye", "goodbye", "see you", "tata", "catch you later", "exit", "quit", "adios"}
        is_farewell = (
            words.intersection(farewells) or
            "see u" in message or
            "see you" in message or
            "catch you later" in message or
            "good night" in message or
            "goodnight" in message
        )
        if is_farewell:
            farewell_pool = [
                "Ride safe and keep the rubber side down! 🏍️ Catch you next time.",
                "Goodbye! Enjoy the wind in your face and watch out for traffic. ✌️",
                "Catch you later, rider! Keep your helmet strapped and stay safe on those curves.",
                "Safe travels! Keep the shiny side up and the dirty side down. 🏍️"
            ]
            return random.choice(farewell_pool)

        # 3. APPRECIATION / THANKS MATCH
        thanks = {"thanks", "ty", "cheers", "appreciate", "tysm", "great", "awesome", "perfect", "nice"}
        is_thanks = (
            words.intersection(thanks) or
            "thank you" in message or
            "thank u" in message or
            "appreciate it" in message or
            "good bot" in message
        )
        if is_thanks:
            thanks_pool = [
                "Anytime, rider! 👊 That's what a good co-pilot is for.",
                "You're very welcome! Keep riding safe out there.",
                "No worries at all! Just happy to help you keep rolling. Let me know if you need anything else.",
                "Glad to be of service! Have an awesome ride. 🏍️"
            ]
            return random.choice(thanks_pool)

        # 4. CHIT-CHAT (HOW ARE YOU) MATCH
        chitchat = {"sup", "whats up", "whatsup"}
        is_chitchat = (
            words.intersection(chitchat) or
            "how are you" in message or
            "how are u" in message or
            "how r u" in message or
            "how's it going" in message or
            "how is it going" in message or
            "how's you" in message or
            "how are you doing" in message or
            "what's up" in message
        )
        if is_chitchat:
            chitchat_pool = [
                "I'm operating on local fallback battery since my main AI connection is offline, but my spark plugs are firing perfectly! How are you doing?",
                "All systems nominal here in backup mode! 🛠️ Just keeping watch over the road for you. How's your ride going?",
                "Cruising along smoothly in local mode! 🏍️ Wishing you clear lanes and green lights. What's on your mind?"
            ]
            return random.choice(chitchat_pool)

        # 5. BOT IDENTITY MATCH
        identity = {"identity", "name"}
        is_identity = (
            words.intersection(identity) or
            "who are you" in message or
            "what is your name" in message or
            "who made you" in message or
            "who r u" in message or
            "your name" in message
        )
        if is_identity:
            identity_pool = [
                "I am *WaxWing*, your motorcycle roadside companion! I'm built to keep riders safe, informed, and moving forward.",
                "Name's *WaxWing*! 🏍️ Your backup assistant for live weather, fuel pumps, and mechanics. I was built to support the riding community."
            ]
            return random.choice(identity_pool)

        # 6. MOTORCYCLE ISSUES / DIAGNOSTICS MATCH
        diagnostics = {
            "engine", "noise", "start", "battery", "chain", "oil", "leak", "tire", "brake",
            "clutch", "gear", "flat", "puncture", "smoke", "overheat", "overheating", "fuel leak",
            "chain slack", "spark plug"
        }
        if words.intersection(diagnostics) or "won't start" in message or "wont start" in message:
            diag_responses = [
                "Bike acting up? 🛠️ Safely pull over off the road first. If it's a mechanical issue, type *mechanic* and share your location so we can find a workshop nearby.",
                "Engine or tire troubles? 🏍️ Check your oil level, chain tension, and tire visual condition if safe. If you need a professional, type *mechanic* and share your location.",
                "A broken down bike is no fun. 🔧 Make sure you are in a safe, visible spot. You can check nearby garage ratings by typing *mechanic* and sending your location."
            ]
            return random.choice(diag_responses)

        # 7. EMERGENCY MATCH
        intents = self._fallback_detect_intents(user_message)
        if "EMERGENCY" in intents:
            return (
                "⚠️ *EMERGENCY ASSISTANCE*\n\n"
                "Please make sure you are in a safe roadside position away from oncoming traffic.\n"
                "If anyone is injured, call local emergency services immediately.\n"
                "To locate nearby help, type *mechanic* or *emergency* and tap the location attachment button to share your coordinates."
            )

        if "WEATHER" in intents:
            return (
                "🌦️ *Live Weather Check*\n\n"
                "I can lookup current weather for your exact coordinates. "
                "Just tap the paperclip icon in Telegram and share your current location."
            )

        if "MECHANIC" in intents:
            return (
                "🔧 *Find a Mechanic*\n\n"
                "Need repairs or tools? Share your current location, and I'll search for nearby bike workshops."
            )

        if "FUEL" in intents:
            return (
                "⛽ *Find Fuel*\n\n"
                "Running dry? Share your location, and I will list nearby petrol pumps and gas stations."
            )

        # 8. HELP REQUEST
        help_words = {"help", "info", "features", "capabilities", "what can you do", "menu", "command", "commands"}
        if words.intersection(help_words) or ("what" in words and "do" in words):
            return (
                "🛠️ *WaxWing Bot Help (Backup Mode)*\n\n"
                "I am operating in backup mode because my AI brain is offline, but I can still perform local tasks:\n"
                "• *Weather*: Get live conditions (say 'weather')\n"
                "• *Mechanics*: Find nearby bike workshops (say 'mechanic')\n"
                "• *Fuel*: Find nearby petrol stations (say 'fuel')\n\n"
                "To get started, simply type one of the keywords above and share your location when prompted."
            )

        # 9. GENERAL FALLBACK DEFAULT
        fallback_pool = [
            "🤖 *WaxWing Local Brain*\n\nI am currently running in offline fallback mode because the AI assistant service is temporarily unreachable.\n\nHowever, my local tools are fully functional! You can search for *weather*, *fuel*, or a *mechanic* by mentioning them, or send a greeting to start a conversation.",
            "I'm keeping my gears turning in local mode while the AI service recovers! 🏍️ Try asking for *weather*, *fuel*, or a *mechanic*, or just say *hello* to chat."
        ]
        return random.choice(fallback_pool)



