"""Configuration for Power Automate email automation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Hier Flow URL eintragen.
FLOW_URL = (
    "https://prod-00.westeurope.logic.azure.com:443/workflows/"
    "00000000000000000000000000000000/triggers/manual/paths/invoke"
    "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0"
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Power Automate integration."""

    flow_secret: str


def load_settings() -> Settings:
    """Load settings from the local .env file."""
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    load_dotenv(env_path)
    flow_secret = os.environ.get("FLOW_SECRET", "").strip()
    if not flow_secret:
        raise ValueError("FLOW_SECRET is missing. Set it in the .env file.")
    return Settings(flow_secret=flow_secret)
