from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .i18n import DEFAULT_LANGUAGE, normalize_language


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(slots=True)
class AppConfig:
    language: str
    weather_location: str | None
    weather_lat: float | None
    weather_lon: float | None
    spotify_client_id: str | None
    spotify_client_secret: str | None
    spotify_redirect_uri: str | None
    spotify_cache_path: Path
    google_calendar_id: str
    google_credentials_path: Path
    google_token_path: Path

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            language=normalize_language(os.getenv("APP_LANGUAGE", DEFAULT_LANGUAGE)),
            weather_location=os.getenv("WEATHER_LOCATION"),
            weather_lat=_optional_float(os.getenv("WEATHER_LAT")),
            weather_lon=_optional_float(os.getenv("WEATHER_LON")),
            spotify_client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            spotify_client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            spotify_redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            spotify_cache_path=_resolve_path(
                os.getenv("SPOTIPY_CACHE_PATH"), PROJECT_ROOT / ".cache" / "spotify_token.json"
            ),
            google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
            google_credentials_path=_resolve_path(
                os.getenv("GOOGLE_CREDENTIALS_FILE"), PROJECT_ROOT / "credentials.json"
            ),
            google_token_path=_resolve_path(
                os.getenv("GOOGLE_TOKEN_FILE"), PROJECT_ROOT / "token.json"
            ),
        )


def _optional_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default

    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate
