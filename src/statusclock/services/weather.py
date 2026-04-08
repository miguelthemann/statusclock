"""Weather service using Open-Meteo API."""

from __future__ import annotations

from dataclasses import dataclass

import requests

from ..i18n import I18N

USER_AGENT = "statusclock/1.0"

# Maps Open-Meteo weather codes to translation keys
WEATHER_CODE_MAP = {
    0: "weather_clear",
    1: "weather_mainly_clear",
    2: "weather_partly_cloudy",
    3: "weather_overcast",
    45: "weather_fog",
    48: "weather_rime_fog",
    51: "weather_light_drizzle",
    53: "weather_drizzle",
    55: "weather_dense_drizzle",
    56: "weather_light_freezing_drizzle",
    57: "weather_dense_freezing_drizzle",
    61: "weather_light_rain",
    63: "weather_rain",
    65: "weather_heavy_rain",
    66: "weather_light_freezing_rain",
    67: "weather_heavy_freezing_rain",
    71: "weather_light_snow",
    73: "weather_snow",
    75: "weather_heavy_snow",
    77: "weather_snow_grains",
    80: "weather_light_showers",
    81: "weather_showers",
    82: "weather_heavy_showers",
    85: "weather_light_snow_showers",
    86: "weather_heavy_snow_showers",
    95: "weather_thunderstorm",
    96: "weather_thunderstorm_hail_light",
    99: "weather_thunderstorm_hail_heavy",
}


@dataclass(slots=True)
class WeatherSnapshot:
    """Current weather conditions for a location."""

    location_name: str
    temperature_c: float
    description: str


class WeatherService:
    """Fetches current weather from Open-Meteo."""

    def __init__(
        self,
        *,
        location_name: str | None,
        latitude: float | None,
        longitude: float | None,
        i18n: I18N,
        timeout: float = 8.0,
    ) -> None:
        self.location_name = location_name
        self.latitude = latitude
        self.longitude = longitude
        self.i18n = i18n
        self.timeout = timeout

    def is_configured(self) -> bool:
        """Check if location is set via name or coordinates."""
        return bool(self.location_name) or (self.latitude is not None and self.longitude is not None)

    def fetch(self) -> WeatherSnapshot:
        """Fetch current weather for the configured location."""
        if not self.is_configured():
            raise RuntimeError("Define WEATHER_LOCATION or WEATHER_LAT/WEATHER_LON.")

        try:
            lat, lon, name = self._resolve_location()
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weather_code",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout,
            )
            response.raise_for_status()
            current = response.json().get("current", {})
        except requests.RequestException as exc:
            raise RuntimeError(self.i18n.t("weather_request_error")) from exc

        return WeatherSnapshot(
            location_name=name,
            temperature_c=float(current["temperature_2m"]),
            description=self._code_to_text(int(current["weather_code"])),
        )

    def _resolve_location(self) -> tuple[float, float, str]:
        """Resolve location name to coordinates using geocoding API."""
        if self.latitude is not None and self.longitude is not None:
            return (
                self.latitude,
                self.longitude,
                self.location_name or self.i18n.t("weather_default_location"),
            )

        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": self.location_name, "count": 1, "language": self.i18n.language},
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            raise RuntimeError(self.i18n.t("weather_not_found", location=self.location_name))

        first = results[0]
        name = ", ".join(part for part in [first.get("name"), first.get("country")] if part)
        return float(first["latitude"]), float(first["longitude"]), name

    def _code_to_text(self, code: int) -> str:
        """Convert Open-Meteo weather code to localized description."""
        key = WEATHER_CODE_MAP.get(code, "weather_unknown")
        return self.i18n.t(key)
