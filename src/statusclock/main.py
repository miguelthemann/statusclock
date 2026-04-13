"""Entry point for Status Clock application."""

from __future__ import annotations

import time
from typing import Callable

from .config import AppConfig
from .cli import launch_cli
from .dashboard import DashboardServices, launch_dashboard
from .i18n import I18N
from .services.calendar_service import GoogleCalendarService
from .services.spotify import SpotifyService
from .services.weather import WeatherService


def build_services(config: AppConfig) -> DashboardServices:
    """Wire up all service instances from configuration with lazy initialization."""
    i18n = I18N(config.language)
    
    # Create factory functions for lazy initialization
    def weather_factory() -> WeatherService:
        return WeatherService(
            location_name=config.weather_location,
            latitude=config.weather_lat,
            longitude=config.weather_lon,
            i18n=i18n,
        )
    
    def spotify_factory() -> SpotifyService:
        return SpotifyService(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret,
            redirect_uri=config.spotify_redirect_uri,
            cache_path=config.spotify_cache_path,
            i18n=i18n,
        )
    
    def calendar_factory() -> GoogleCalendarService:
        return GoogleCalendarService(
            credentials_path=config.google_credentials_path,
            token_path=config.google_token_path,
            calendar_id=config.google_calendar_id,
            i18n=i18n,
        )
    
    return DashboardServices(
        i18n=i18n,
        enable_weather=config.enable_weather,
        enable_spotify=config.enable_spotify,
        enable_calendar=config.enable_google_calendar,
        weather_factory=weather_factory if config.enable_weather else None,
        spotify_factory=spotify_factory if config.enable_spotify else None,
        calendar_factory=calendar_factory if config.enable_google_calendar else None,
    )


def main() -> int:
    """Load config, build services, and launch the appropriate interface."""
    start_time = time.time()
    
    config = AppConfig.from_env()
    services = build_services(config)
    
    if config.app_mode == "cli":
        return launch_cli(services)
    
    # For GUI mode, we can show window faster by deferring some initialization
    return launch_dashboard(services)


if __name__ == "__main__":
    raise SystemExit(main())
