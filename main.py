"""Backward-compatible entrypoint for existing Gunicorn deployments."""

from src.main import app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"])

