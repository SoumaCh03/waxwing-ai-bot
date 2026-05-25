#!/usr/bin/env sh
set -eu

python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill in your real credentials before running."
fi

echo "Setup complete. Run: python -m src.main"

