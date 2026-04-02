from __future__ import annotations

from dataclasses import dataclass

import requests

from ..i18n import I18N


USER_AGENT = "statusclock/1.0"


@dataclass(slots=True)
class WeatherSnapshot:
    location_name: str
    temperature_c: float
    description: str


class WeatherService:
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
        return bool(self.location_name) or (
            self.latitude is not None and self.longitude is not None
        )

    def fetch(self) -> WeatherSnapshot:
        if not self.is_configured():
            raise RuntimeError("Define WEATHER_LOCATION or WEATHER_LAT/WEATHER_LON.")

        latitude, longitude, resolved_name = self._resolve_location()
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current", {})

        return WeatherSnapshot(
            location_name=resolved_name,
            temperature_c=float(current["temperature_2m"]),
            description=weather_code_to_text(int(current["weather_code"]), self.i18n),
        )

    def _resolve_location(self) -> tuple[float, float, str]:
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
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            raise RuntimeError(self.i18n.t("weather_not_found", location=self.location_name))

        first = results[0]
        name = ", ".join(
            part for part in [first.get("name"), first.get("country")] if part
        )
        return float(first["latitude"]), float(first["longitude"]), name


def weather_code_to_text(code: int, i18n: I18N) -> str:
    mapping = {
        0: i18n.t("weather_clear"),
        1: i18n.t("weather_mainly_clear"),
        2: i18n.t("weather_partly_cloudy"),
        3: i18n.t("weather_overcast"),
        45: i18n.t("weather_fog"),
        48: i18n.t("weather_rime_fog"),
        51: i18n.t("weather_light_drizzle"),
        53: i18n.t("weather_drizzle"),
        55: i18n.t("weather_dense_drizzle"),
        56: i18n.t("weather_light_freezing_drizzle"),
        57: i18n.t("weather_dense_freezing_drizzle"),
        61: i18n.t("weather_light_rain"),
        63: i18n.t("weather_rain"),
        65: i18n.t("weather_heavy_rain"),
        66: i18n.t("weather_light_freezing_rain"),
        67: i18n.t("weather_heavy_freezing_rain"),
        71: i18n.t("weather_light_snow"),
        73: i18n.t("weather_snow"),
        75: i18n.t("weather_heavy_snow"),
        77: i18n.t("weather_snow_grains"),
        80: i18n.t("weather_light_showers"),
        81: i18n.t("weather_showers"),
        82: i18n.t("weather_heavy_showers"),
        85: i18n.t("weather_light_snow_showers"),
        86: i18n.t("weather_heavy_snow_showers"),
        95: i18n.t("weather_thunderstorm"),
        96: i18n.t("weather_thunderstorm_hail_light"),
        99: i18n.t("weather_thunderstorm_hail_heavy"),
    }
    return mapping.get(code, i18n.t("weather_unknown"))
