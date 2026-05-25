# WAXWING AI Bot

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Webhook%20API-black.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

WAXWING is a production-ready Telegram AI assistant for motorcycle roadside support. It combines Gemini-powered conversation, intent detection, live weather, nearby fuel search, and nearby mechanic discovery behind a clean Flask webhook service.

The project is structured for real deployment, portfolio review, and future scaling: secrets are environment-driven, external integrations are isolated behind services, Docker support is included, and runtime failures are logged without crashing the webhook.

## Features

- Telegram webhook bot built with Flask and Gunicorn.
- Gemini intent detection for weather, fuel, mechanic, emergency, and general chat requests.
- Gemini conversational replies for rider assistance.
- OpenWeather integration for location-based live weather.
- Google Places integration for nearby fuel pumps and motorcycle mechanics.
- Firestore-backed user state with an in-memory fallback for local development.
- Optional Telegram webhook secret validation.
- Structured production logging and graceful API failure handling.
- Docker and Docker Compose support.

## Screenshots

Add production screenshots here after connecting the bot to Telegram:

| Start flow | Location request | Nearby assistance |
| --- | --- | --- |
| `docs/screenshots/start.png` | `docs/screenshots/location.png` | `docs/screenshots/results.png` |

## Architecture

```text
waxwing-ai-bot/
|-- src/
|   |-- main.py                 # Runtime entrypoint
|   |-- bot/
|   |   |-- app.py              # Flask app factory and webhook route
|   |   `-- telegram.py         # Telegram Bot API client
|   |-- config/
|   |   `-- settings.py         # Environment-based configuration
|   |-- handlers/
|   |   `-- message_router.py   # Text and location conversation flow
|   |-- services/
|   |   |-- gemini_service.py   # Gemini intent and chat calls
|   |   |-- places_service.py   # Google Places integration
|   |   |-- user_store.py       # Firestore/in-memory state
|   |   `-- weather_service.py  # OpenWeather integration
|   `-- utils/
|       `-- logging.py          # Logging setup
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- LICENSE
`-- README.md
```

## Bot Flow

1. Telegram sends webhook updates to `POST /`.
2. `/start` and greeting messages receive direct onboarding responses.
3. Other text messages are classified by Gemini.
4. Emergency messages receive an immediate safety-first response.
5. Weather, fuel, and mechanic intents store pending tools and ask for location.
6. Shared locations trigger OpenWeather and/or Google Places lookups.
7. General chat messages receive a concise Gemini response.

## Environment Variables

Copy `.env.example` to `.env` and fill in real values.

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token from BotFather. |
| `GEMINI_API_KEY` | Yes | Gemini API key for intent detection and chat. |
| `OPENWEATHER_API_KEY` | For weather | OpenWeather API key. |
| `GOOGLE_MAPS_API_KEY` | For places | Google Maps/Places API key. |
| `ENABLE_FIRESTORE` | No | Set `false` for local in-memory state. Defaults to `true`. |
| `FIRESTORE_COLLECTION` | No | Firestore collection for user state. Defaults to `users`. |
| `GOOGLE_APPLICATION_CREDENTIALS` | For Firestore | Path to Google service account JSON. |
| `GEMINI_MODEL` | No | Gemini model name. Defaults to `gemini-2.5-flash`. |
| `TELEGRAM_WEBHOOK_SECRET` | No | Secret header expected from Telegram webhook requests. |
| `REQUEST_TIMEOUT_SECONDS` | No | HTTP timeout for external APIs. Defaults to `10`. |
| `PORT` | No | HTTP port. Defaults to `8080`. |
| `LOG_LEVEL` | No | Python logging level. Defaults to `INFO`. |

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`, then run:

```bash
python -m src.main
```

For Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m src.main
```

The health endpoint is available at:

```text
GET http://localhost:8080/
```

## Docker

Build and run directly:

```bash
docker build -t waxwing-ai-bot .
docker run --env-file .env -p 8080:8080 waxwing-ai-bot
```

Or use Docker Compose:

```bash
docker compose up --build
```

## Telegram Webhook

After deploying the service to a public HTTPS URL, register the webhook:

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://your-domain.example/" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

If `TELEGRAM_WEBHOOK_SECRET` is not set, the app accepts webhook requests without header validation.

## Deployment Notes

- Use a managed container runtime, VM, or PaaS that supports public HTTPS.
- Store secrets in the platform secret manager, not in Git.
- For Firestore, mount or inject Google credentials and set `GOOGLE_APPLICATION_CREDENTIALS`.
- Ensure Google Places, OpenWeather, and Gemini quotas are monitored.
- Keep Telegram webhook traffic behind HTTPS.

## Technologies

- Python 3.13
- Flask
- Gunicorn
- Gemini API via `google-genai`
- Google Cloud Firestore
- OpenWeather API
- Google Places API
- Docker

## Roadmap

- Add automated tests for routing and service formatting.
- Add CI checks for formatting, import validation, and secret scanning.
- Add webhook setup scripts for deployment environments.
- Add persistent conversation history with retention controls.
- Add screenshots from the live Telegram bot.

## Contributing

Contributions are welcome. Keep changes focused, avoid committing secrets, and document any new environment variables in `.env.example` and this README.

Recommended workflow:

```bash
git checkout -b feature/your-change
python -m compileall src
docker build -t waxwing-ai-bot .
git commit -m "Describe your change"
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

