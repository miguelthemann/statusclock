from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .i18n import DEFAULT_LANGUAGE, normalize_language


SUPPORTED_APP_MODES = {"gui", "cli"}
DEFAULT_APP_MODE = "gui"


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(slots=True)
class AppConfig:
    app_mode: str
    language: str
    enable_weather: bool
    enable_spotify: bool
    enable_google_calendar: bool
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
            app_mode=_normalize_app_mode(os.getenv("APP_MODE", DEFAULT_APP_MODE)),
            language=normalize_language(os.getenv("APP_LANGUAGE", DEFAULT_LANGUAGE)),
            enable_weather=_parse_bool_env(os.getenv("ENABLE_WEATHER"), True),
            enable_spotify=_parse_bool_env(os.getenv("ENABLE_SPOTIFY"), True),
            enable_google_calendar=_parse_bool_env(
                os.getenv("ENABLE_GOOGLE_CALENDAR"), True
            ),
            weather_location=os.getenv("WEATHER_LOCATION"),
            weather_lat=_optional_float(os.getenv("WEATHER_LAT")),
            weather_lon=_optional_float(os.getenv("WEATHER_LON")),
            spotify_client_id=_env_with_legacy("SPOTIFY_CLIENT_ID", "SPOTIPY_CLIENT_ID"),
            spotify_client_secret=_env_with_legacy("SPOTIFY_CLIENT_SECRET", "SPOTIPY_CLIENT_SECRET"),
            spotify_redirect_uri=_env_with_legacy("SPOTIFY_REDIRECT_URI", "SPOTIPY_REDIRECT_URI"),
            spotify_cache_path=_resolve_path(
                _env_with_legacy("SPOTIFY_CACHE_PATH", "SPOTIPY_CACHE_PATH"),
                PROJECT_ROOT / ".cache" / "spotify_token.json",
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


def _parse_bool_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default

    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def _env_with_legacy(primary: str, legacy: str) -> str | None:
    return os.getenv(primary) or os.getenv(legacy)


def _normalize_app_mode(value: str | None) -> str:
    if not value:
        return DEFAULT_APP_MODE
    normalized = value.strip().lower()
    return normalized if normalized in SUPPORTED_APP_MODES else DEFAULT_APP_MODE
