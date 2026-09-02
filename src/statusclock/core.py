"""Core dashboard abstractions used by the status clock application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .i18n import I18N
from .services.calendar_service import GoogleCalendarService
from .services.spotify import SpotifyService
from .services.weather import WeatherService


@dataclass
class DashboardServices:
    """Container for all service instances used by the dashboard."""

    i18n: I18N
    enable_weather: bool
    enable_spotify: bool
    enable_calendar: bool
    weather_factory: Callable[[], WeatherService] | None
    spotify_factory: Callable[[], SpotifyService] | None
    calendar_factory: Callable[[], GoogleCalendarService] | None

    def __post_init__(self) -> None:
        self._weather: WeatherService | None = None
        self._spotify: SpotifyService | None = None
        self._calendar: GoogleCalendarService | None = None

    @property
    def weather(self) -> WeatherService:
        """Lazy-loaded weather service."""
        if self._weather is None:
            if self.weather_factory is None:
                raise RuntimeError("Weather service is not configured")
            self._weather = self.weather_factory()
        return self._weather

    @property
    def spotify(self) -> SpotifyService:
        """Lazy-loaded Spotify service."""
        if self._spotify is None:
            if self.spotify_factory is None:
                raise RuntimeError("Spotify service is not configured")
            self._spotify = self.spotify_factory()
        return self._spotify

    @property
    def calendar(self) -> GoogleCalendarService:
        """Lazy-loaded calendar service."""
        if self._calendar is None:
            if self.calendar_factory is None:
                raise RuntimeError("Calendar service is not configured")
            self._calendar = self.calendar_factory()
        return self._calendar
