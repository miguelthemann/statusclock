"""Terminal-based dashboard using ASCII art."""

from __future__ import annotations

import os
import shutil
import time
from collections.abc import Iterable
from datetime import datetime
from textwrap import wrap

from .dashboard import DashboardServices
from .i18n import get_qlocale

# Big ASCII art digits for the clock display
BIG_CLOCK_GLYPHS = {
    "0": [
        " ████ ",
        "██  ██",
        "██  ██",
        "██  ██",
        " ████ ",
    ],
    "1": [
        "  ██  ",
        "████  ",
        "  ██  ",
        "  ██  ",
        "██████",
    ],
    "2": [
        "█████ ",
        "    ██",
        " ████ ",
        "██    ",
        "██████",
    ],
    "3": [
        "█████ ",
        "    ██",
        " ████ ",
        "    ██",
        "█████ ",
    ],
    "4": [
        "██  ██",
        "██  ██",
        "██████",
        "    ██",
        "    ██",
    ],
    "5": [
        "██████",
        "██    ",
        "█████ ",
        "    ██",
        "█████ ",
    ],
    "6": [
        " ████ ",
        "██    ",
        "█████ ",
        "██  ██",
        " ████ ",
    ],
    "7": [
        "██████",
        "    ██",
        "   ██ ",
        "  ██  ",
        "  ██  ",
    ],
    "8": [
        " ████ ",
        "██  ██",
        " ████ ",
        "██  ██",
        " ████ ",
    ],
    "9": [
        " ████ ",
        "██  ██",
        " █████",
        "    ██",
        " ████ ",
    ],
    ":": [
        "      ",
        "  ██  ",
        "      ",
        "  ██  ",
        "      ",
    ],
}


def launch_cli(services: DashboardServices) -> int:
    """Run the CLI dashboard loop until interrupted."""
    i18n = services.i18n
    weather_text = i18n.t("loading")
    spotify_title = i18n.t("loading")
    spotify_artist = ""
    spotify_status = i18n.t("loading")
    calendar_lines = [i18n.t("loading")]
    last_weather_at = 0.0
    last_spotify_at = 0.0
    last_calendar_at = 0.0

    try:
        while True:
            now_ts = time.time()

            # Refresh weather every 10 minutes
            if services.enable_weather and (now_ts - last_weather_at >= 10 * 60 or last_weather_at == 0.0):
                try:
                    weather = services.weather.fetch()
                    weather_text = f"{weather.location_name} | {weather.temperature_c:.1f} °C | {weather.description}"
                except Exception as exc:
                    weather_text = f"{i18n.t('weather_unavailable')} | {exc}"
                last_weather_at = now_ts

            # Refresh Spotify every 5 seconds (reduced from 2 to save CPU/API calls)
            if services.enable_spotify and (now_ts - last_spotify_at >= 5 or last_spotify_at == 0.0):
                try:
                    spotify = services.spotify.fetch()
                    spotify_status = i18n.t("spotify_playing") if spotify.is_playing else i18n.t("spotify_not_playing")
                    spotify_title = spotify.title
                    spotify_artist = spotify.artist
                except Exception as exc:
                    spotify_status = i18n.t("spotify_unavailable")
                    spotify_title = str(exc)
                    spotify_artist = ""
                last_spotify_at = now_ts

            # Refresh calendar every 10 minutes
            if services.enable_calendar and (now_ts - last_calendar_at >= 10 * 60 or last_calendar_at == 0.0):
                try:
                    events = services.calendar.fetch_today()
                    if events:
                        calendar_lines = [f"{event.start_text}  {event.title}" for event in events[:8]]
                        if len(events) > 8:
                            calendar_lines.append(i18n.t("calendar_more_events", count=len(events) - 8))
                    else:
                        calendar_lines = [i18n.t("calendar_no_events")]
                except Exception as exc:
                    calendar_lines = [f"{i18n.t('calendar_unavailable')} | {exc}"]
                last_calendar_at = now_ts

            _render_cli(
                services=services,
                weather_text=weather_text,
                spotify_status=spotify_status,
                spotify_title=spotify_title,
                spotify_artist=spotify_artist,
                calendar_lines=calendar_lines,
            )
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


def _render_cli(
    *,
    services: DashboardServices,
    weather_text: str,
    spotify_status: str,
    spotify_title: str,
    spotify_artist: str,
    calendar_lines: list[str],
) -> None:
    """Render the full CLI dashboard to stdout."""
    i18n = services.i18n
    now = datetime.now().astimezone()
    date_text = get_qlocale(i18n.language).toString(now, "dddd, d MMMM yyyy")
    terminal_width = max(80, shutil.get_terminal_size(fallback=(120, 30)).columns)
    content_width = min(terminal_width, 140)
    top_gap = 4
    weather_width = min(34, max(26, content_width // 4))
    spotify_width = min(52, max(34, content_width // 3))
    calendar_width = min(90, max(46, content_width - 20))

    _clear_screen()
    weather_box = _make_box(i18n.t("weather_title"), [weather_text], weather_width)
    spotify_lines = [spotify_status, spotify_title]
    if spotify_artist:
        spotify_lines.append(spotify_artist)
    spotify_box = _make_box(i18n.t("spotify_title"), spotify_lines, spotify_width)

    if services.enable_weather and services.enable_spotify:
        for line in _merge_rows(weather_box, spotify_box, content_width):
            print(_center_text(line, terminal_width))
    elif services.enable_weather:
        for line in weather_box:
            print(_center_text(line, terminal_width))
    elif services.enable_spotify:
        for line in spotify_box:
            print(_center_text(line, terminal_width))

    print("\n" * top_gap, end="")
    for line in _render_big_clock(now.strftime("%H:%M:%S")):
        print(_center_text(line, terminal_width))
    print("\n", end="")
    print(_center_text(date_text, terminal_width))
    print("\n" * 3, end="")

    if services.enable_calendar:
        calendar_box = _make_box(i18n.t("calendar_title"), calendar_lines, calendar_width)
        for line in calendar_box:
            print(_center_text(line, terminal_width))


def _clear_screen() -> None:
    """Clear the terminal screen."""
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


def _center_text(text: str, width: int) -> str:
    """Center text within given width."""
    return text.center(max(len(text), width))


def _make_box(title: str, lines: Iterable[str], width: int) -> list[str]:
    """Create a bordered box with title and wrapped content."""
    inner_width = max(16, width - 4)
    wrapped_lines = _normalize_lines(lines, inner_width)
    title_text = f" {title} "
    title_fill = max(0, width - len(title_text) - 2)
    top = f".{title_text}{'-' * title_fill}."
    body = [f"| {line.ljust(inner_width)} |" for line in wrapped_lines]
    bottom = f"'{'-' * (width - 2)}'"
    return [top, *body, bottom]


def _normalize_lines(lines: Iterable[str], width: int) -> list[str]:
    """Wrap long lines to fit within width."""
    normalized: list[str] = []
    for line in lines:
        chunks = wrap(line, width=width, break_long_words=False, break_on_hyphens=False)
        normalized.extend(chunks or [""])
    return normalized or [""]


def _merge_rows(left_box: list[str], right_box: list[str], total_width: int) -> list[str]:
    """Merge two boxes side by side with spacing."""
    left_width = len(left_box[0])
    right_width = len(right_box[0])
    gap = max(4, total_width - left_width - right_width)
    line_count = max(len(left_box), len(right_box))
    left_pad = " " * left_width
    right_pad = " " * right_width
    merged: list[str] = []
    for index in range(line_count):
        left = left_box[index] if index < len(left_box) else left_pad
        right = right_box[index] if index < len(right_box) else right_pad
        merged.append(f"{left}{' ' * gap}{right}")
    return merged


def _render_big_clock(value: str) -> list[str]:
    """Render time string as big ASCII art digits."""
    rows = [""] * 5
    for char in value:
        glyph = BIG_CLOCK_GLYPHS.get(char, BIG_CLOCK_GLYPHS["0"])
        for index, segment in enumerate(glyph):
            rows[index] += segment + "  "
    trimmed_rows = [row.rstrip() for row in rows]
    max_width = max((len(row) for row in trimmed_rows), default=0)
    return [row.ljust(max_width) for row in trimmed_rows]
