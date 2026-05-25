"""Application entrypoint for WAXWING."""

import os
from src.bot.app import create_app

app = create_app()


if __name__ == "__main__":
    mode = os.getenv("TELEGRAM_MODE", "webhook").strip().lower()
    if mode == "polling":
        # Start local long-polling runner for development.
        from src.bot.poller import run_polling

        run_polling()
    else:
        # Default behavior: run Flask webhook server for production/normal use.
        print("Running in WEBHOOK mode")
        app.run(host="0.0.0.0", port=app.config["PORT"])
