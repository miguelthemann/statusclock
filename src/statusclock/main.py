"""Entry point for Status Clock application."""

from __future__ import annotations

from .config import AppConfig
from .cli import launch_cli
from .dashboard import DashboardServices, launch_dashboard
from .i18n import I18N
from .services.calendar_service import GoogleCalendarService
from .services.spotify import SpotifyService
from .services.weather import WeatherService


def build_services(config: AppConfig) -> DashboardServices:
    """Wire up all service instances from configuration."""
    i18n = I18N(config.language)
    return DashboardServices(
        i18n=i18n,
        enable_weather=config.enable_weather,
        enable_spotify=config.enable_spotify,
        enable_calendar=config.enable_google_calendar,
        weather=WeatherService(
            location_name=config.weather_location,
            latitude=config.weather_lat,
            longitude=config.weather_lon,
            i18n=i18n,
        ),
        spotify=SpotifyService(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret,
            redirect_uri=config.spotify_redirect_uri,
            cache_path=config.spotify_cache_path,
            i18n=i18n,
        ),
        calendar=GoogleCalendarService(
            credentials_path=config.google_credentials_path,
            token_path=config.google_token_path,
            calendar_id=config.google_calendar_id,
            i18n=i18n,
        ),
    )


def main() -> int:
    """Load config, build services, and launch the appropriate interface."""
    config = AppConfig.from_env()
    services = build_services(config)
    if config.app_mode == "cli":
        return launch_cli(services)
    return launch_dashboard(services)


if __name__ == "__main__":
    raise SystemExit(main())
