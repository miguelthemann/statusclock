from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    package_root = Path(__file__).resolve().parents[2]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from src.statusclock.config import AppConfig
    from src.statusclock.dashboard import DashboardServices, launch_dashboard
    from src.statusclock.services.calendar_service import GoogleCalendarService
    from src.statusclock.services.spotify import SpotifyService
    from src.statusclock.services.weather import WeatherService
else:
    from .config import AppConfig
    from .dashboard import DashboardServices, launch_dashboard
    from .services.calendar_service import GoogleCalendarService
    from .services.spotify import SpotifyService
    from .services.weather import WeatherService


def build_services(config: AppConfig) -> DashboardServices:
    return DashboardServices(
        weather=WeatherService(
            location_name=config.weather_location,
            latitude=config.weather_lat,
            longitude=config.weather_lon,
        ),
        spotify=SpotifyService(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret,
            redirect_uri=config.spotify_redirect_uri,
            cache_path=config.spotify_cache_path,
        ),
        calendar=GoogleCalendarService(
            credentials_path=config.google_credentials_path,
            token_path=config.google_token_path,
            calendar_id=config.google_calendar_id,
        ),
    )


def main() -> int:
    config = AppConfig.from_env()
    services = build_services(config)
    return launch_dashboard(services)


if __name__ == "__main__":
    raise SystemExit(main())
