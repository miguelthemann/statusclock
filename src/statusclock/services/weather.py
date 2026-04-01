from __future__ import annotations

from dataclasses import dataclass

import requests


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
        timeout: float = 8.0,
    ) -> None:
        self.location_name = location_name
        self.latitude = latitude
        self.longitude = longitude
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
            description=weather_code_to_text(int(current["weather_code"])),
        )

    def _resolve_location(self) -> tuple[float, float, str]:
        if self.latitude is not None and self.longitude is not None:
            return self.latitude, self.longitude, self.location_name or "Localiza\u00e7\u00e3o"

        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": self.location_name, "count": 1, "language": "pt"},
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            raise RuntimeError(f"N\u00e3o foi poss\u00edvel encontrar '{self.location_name}'.")

        first = results[0]
        name = ", ".join(
            part for part in [first.get("name"), first.get("country")] if part
        )
        return float(first["latitude"]), float(first["longitude"]), name


def weather_code_to_text(code: int) -> str:
    mapping = {
        0: "C\u00e9u limpo",
        1: "Pouco nublado",
        2: "Parcialmente nublado",
        3: "Muito nublado",
        45: "Nevoeiro",
        48: "Nevoeiro gelado",
        51: "Chuvisco fraco",
        53: "Chuvisco",
        55: "Chuvisco forte",
        56: "Chuvisco gelado fraco",
        57: "Chuvisco gelado forte",
        61: "Chuva fraca",
        63: "Chuva",
        65: "Chuva forte",
        66: "Chuva gelada fraca",
        67: "Chuva gelada forte",
        71: "Neve fraca",
        73: "Neve",
        75: "Neve forte",
        77: "Gr\u00e3os de neve",
        80: "Aguaceiros fracos",
        81: "Aguaceiros",
        82: "Aguaceiros fortes",
        85: "Aguaceiros de neve fracos",
        86: "Aguaceiros de neve fortes",
        95: "Trovoada",
        96: "Trovoada com granizo fraco",
        99: "Trovoada com granizo forte",
    }
    return mapping.get(code, "Estado desconhecido")
