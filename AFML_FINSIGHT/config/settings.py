"""Centralized configuration loader for FinSight."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


@dataclass
class Settings:
    google_api_key: str
    fred_api_key: str
    sec_user_agent: str
    serper_api_key: str


def get_settings() -> Settings:
    google_api_key = os.getenv("GOOGLE_API_KEY")
    fred_api_key = os.getenv("FRED_API_KEY")
    sec_user_agent = os.getenv("SEC_USER_AGENT")
    serper_api_key = os.getenv("SERPER_API_KEY")

    missing = [
        key
        for key, value in (
            ("GOOGLE_API_KEY", google_api_key),
            ("FRED_API_KEY", fred_api_key),
            ("SEC_USER_AGENT", sec_user_agent),
            ("SERPER_API_KEY", serper_api_key),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required environment variables for FinSight: " + ", ".join(missing)
        )

    return Settings(
        google_api_key=google_api_key,
        fred_api_key=fred_api_key,
        sec_user_agent=sec_user_agent,
        serper_api_key=serper_api_key,
    )
