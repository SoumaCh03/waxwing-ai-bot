# WAXWING Project Audit

Date: 2026-05-25

## Original Architecture

The original project contained three files:

- `main.py`: Flask app, Telegram webhook route, configuration, Firestore client, Gemini client, weather lookup, Google Places lookup, and message routing in one module.
- `requirements.txt`: unpinned runtime dependencies.
- `Dockerfile`: minimal Python image that copied the full repository and ran Gunicorn.

The deployed behavior was a Telegram webhook bot that handled `/start`, greetings, Gemini-backed intent detection, emergency safety responses, location requests, weather lookup, fuel search, mechanic search, and general Gemini chat responses.

## Dependencies

Original dependencies:

- Flask
- requests
- gunicorn
- google-cloud-firestore
- google-genai

Modernized dependencies:

- Version-bounded runtime dependencies.
- `python-dotenv` for local environment loading.

## Security Findings

High severity issues found:

- Telegram bot token was hardcoded in source code.
- OpenWeather API key was hardcoded in source code.
- Google Maps API key was hardcoded in source code.
- Gemini API key was hardcoded in source code.
- `.env.example` did not exist.
- `.gitignore` did not exist, so local secrets could be committed accidentally.
- Webhook requests had no optional secret header validation.

Resolution:

- Removed all hardcoded credentials from source code.
- Added environment-based configuration.
- Added `.env.example` with placeholders only.
- Added `.gitignore` and `.dockerignore`.
- Added optional `TELEGRAM_WEBHOOK_SECRET` validation.

## Code Quality Findings

Issues found:

- All responsibilities lived in one file.
- External clients were initialized at import time.
- Firestore errors could crash startup.
- API calls had no explicit timeout.
- Telegram send failures were ignored.
- Gemini errors were returned directly to users.
- Weather/Places response parsing assumed every field existed.
- No typed boundaries between routing and services.
- No health endpoint.
- No structured logging.

Resolution:

- Split the code into config, bot, handlers, services, and utilities.
- Added explicit request timeouts.
- Added structured logging.
- Added graceful user-facing fallback responses.
- Added health check endpoint.
- Added Firestore fallback for local development.
- Added type hints and small service classes.

## Deployment Findings

Issues found:

- Docker image ran as root.
- Dockerfile installed dependencies after copying the entire project, reducing layer cache usefulness.
- No Docker Compose file.
- No `.dockerignore`.
- Gunicorn targeted the old root module only.

Resolution:

- Docker now runs as a non-root user.
- Dependency install is cached before copying app source.
- Added `.dockerignore`.
- Added `docker-compose.yml`.
- Gunicorn now targets `src.main:app`.
- Root `main.py` remains as a compatibility wrapper.

## Scalability Concerns

Remaining considerations:

- In-memory state is only for local fallback and is not suitable for multi-instance production.
- External API quota, retry, and backoff policies should be monitored in production.
- Telegram webhook delivery should run behind public HTTPS.
- Future conversation history should include retention and privacy controls.

## Final Status

The repository is now safe to prepare for public GitHub usage after real secrets are placed only in local or platform-managed environment variables. The code preserves the original bot behavior while making the system easier to review, deploy, debug, and extend.

