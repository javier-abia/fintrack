"""Create or update apps/api/.env with a SECRET_KEY and a password hash.

Usage (from repo root or apps/api):
    uv run python apps/api/scripts/init_env.py
"""

from __future__ import annotations

import getpass
import secrets
import sys
from pathlib import Path

import bcrypt

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
ENV_EXAMPLE_PATH = ENV_PATH.parent / ".env.example"


def read_existing_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    values: dict[str, str] = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def prompt_password() -> str:
    while True:
        password = getpass.getpass("Choose a login password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters.", file=sys.stderr)
            continue
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords didn't match, try again.", file=sys.stderr)
            continue
        return password


def main() -> None:
    existing = read_existing_env()

    if existing.get("SINGLE_USER_PASSWORD_HASH"):
        answer = input(f"{ENV_PATH} already has a password set. Overwrite it? [y/N] ")
        if answer.strip().lower() != "y":
            print("Aborted, existing .env left untouched.")
            return

    password = prompt_password()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    secret_key = existing.get("SECRET_KEY") or secrets.token_hex(32)

    values = {
        "DATABASE_URL": existing.get(
            "DATABASE_URL", "sqlite+aiosqlite:///./data/fintrack.db"
        ),
        "SECRET_KEY": secret_key,
        "SINGLE_USER_PASSWORD_HASH": password_hash,
        "DEBUG": existing.get("DEBUG", "false"),
    }

    ENV_PATH.write_text("".join(f"{key}={value}\n" for key, value in values.items()))
    print(f"Wrote {ENV_PATH}")


if __name__ == "__main__":
    main()
