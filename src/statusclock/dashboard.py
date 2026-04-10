"""PySide6 GUI dashboard for Status Clock."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import requests
from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QKeySequence, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStyle,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)

from .i18n import I18N, get_qlocale
from .services.calendar_service import GoogleCalendarService
from .services.spotify import SpotifyService, SpotifySnapshot
from .services.weather import WeatherService, WeatherSnapshot

CLOCK_FORMAT = "%H:%M:%S"

CALENDAR_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/>
    <line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
</svg>
""".strip()


class WorkerSignals(QObject):
    """Signals emitted by background workers."""

    success = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    """Runs a callable in the thread pool and emits signals on completion."""

    def __init__(self, func: Callable[[], object]) -> None:
        super().__init__()
        self.func = func
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.func()
        except Exception as exc:
            self.signals.error.emit(str(exc))
        else:
            self.signals.success.emit(result)


class MarqueeLabel(QLabel):
    """Label that scrolls text horizontally when it overflows."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._offset = 0
        self._pause_ticks = 0
        self._last_width = 0
        self._step_px = 2
        self._gap_px = 48
        self._pause_duration = 30
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def setText(self, text: str) -> None:
        super().setText(text)
        self._offset = 0
        self._pause_ticks = self._pause_duration
        self.update()

    def resizeEvent(self, event) -> None:
        new_width = event.size().width()
        if new_width != self._last_width:
            self._offset = 0
            self._pause_ticks = self._pause_duration
            self._last_width = new_width
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        option = QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, option, painter, self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setFont(self.font())
        painter.setPen(self.palette().windowText().color())

        text = self.text()
        if not text:
            return

        rect = self.contentsRect()
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        baseline = rect.top() + metrics.ascent() + max(0, (rect.height() - metrics.height()) // 2)

        if text_width <= rect.width():
            painter.drawText(rect, int(self.alignment()), text)
            return

        painter.setClipRect(rect)
        element = rect.left() - self._offset
        painter.drawText(element, baseline, text)
        painter.drawText(element + text_width + self._gap_px, baseline, text)

    def _tick(self) -> None:
        text = self.text()
        if not text:
            return

        text_width = self.fontMetrics().horizontalAdvance(text)
        available_width = self.contentsRect().width()
        if text_width <= available_width:
            if self._offset != 0:
                self._offset = 0
                self.update()
            return

        if self._pause_ticks > 0:
            self._pause_ticks -= 1
            return

        self._offset += self._step_px
        if self._offset >= text_width + self._gap_px:
            self._offset = 0
            self._pause_ticks = self._pause_duration
        self.update()


@dataclass(slots=True)
class DashboardServices:
    """Container for all service instances used by the dashboard."""

    i18n: I18N
    enable_weather: bool
    enable_spotify: bool
    enable_calendar: bool
    weather: WeatherService
    spotify: SpotifyService
    calendar: GoogleCalendarService


@dataclass(slots=True)
class _CardRefs:
    """References to widgets within a dashboard card."""

    frame: QFrame
    subtitle: QLabel
    body: QLabel
    text_column: QWidget | None = None
    secondary: QLabel | None = None
    media: QLabel | None = None


@dataclass(slots=True)
class _RefreshState:
    """Tracks which services are currently loading."""

    weather_busy: bool = False
    spotify_busy: bool = False
    calendar_busy: bool = False
    weather_loaded: bool = False
    spotify_loaded: bool = False
    calendar_loaded: bool = False


class StatusClockWindow(QMainWindow):
    """Main application window showing clock, weather, Spotify, and calendar."""

    def __init__(self, services: DashboardServices) -> None:
        super().__init__()
        self.services = services
        self.i18n = services.i18n
        self.thread_pool = QThreadPool(self)
        self.locale = get_qlocale(self.i18n.language)
        self.refresh_state = _RefreshState()
        self._closing = False
        self._album_art_url: str | None = None
        self._active_workers: set[Worker] = set()

        self.setWindowTitle(self.i18n.t("app_title"))
        self.setMinimumSize(1280, 720)
        self._build_ui()
        self._build_shortcuts()
        self._start_timers()
        self._refresh_clock()
        self.refresh_all()

    def _build_ui(self) -> None:
        """Construct the main window layout."""
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        shell = QVBoxLayout(root)
        shell.setContentsMargins(26, 20, 26, 16)
        shell.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        shell.addLayout(top_row)

        # Weather card
        self.weather_card = self._create_card(self.i18n.t("weather_title"))
        self.weather_card.body.setText(self.i18n.t("weather_setup"))
        self.weather_card.frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.weather_card.frame.setMaximumWidth(360)

        # Spotify card
        self.spotify_card = self._create_card(self.i18n.t("spotify_title"), with_media=True)
        self.spotify_card.body.setText(self.i18n.t("spotify_setup_title"))
        if self.spotify_card.secondary is not None:
            self.spotify_card.secondary.setText(self.i18n.t("spotify_setup_subtitle"))
        self.spotify_card.frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.spotify_card.frame.setMinimumWidth(480)
        self.spotify_card.frame.setMaximumWidth(480)
        if self.spotify_card.text_column is not None:
            self.spotify_card.text_column.setFixedWidth(300)

        if self.services.enable_weather:
            top_row.addWidget(self.weather_card.frame, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        else:
            self.weather_card.frame.hide()
            top_row.addStretch(1)

        if self.services.enable_spotify:
            top_row.addWidget(self.spotify_card.frame, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        else:
            self.spotify_card.frame.hide()

        # Center clock area
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shell.addWidget(center, 1)

        self.clock_label = QLabel("--:--:--")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setFont(QFont("Segoe UI", 82, QFont.Weight.Bold))
        self.clock_label.setMinimumWidth(self.clock_label.fontMetrics().horizontalAdvance("88:88:88") + 24)
        center_layout.addWidget(self.clock_label)

        self.date_label = QLabel(self.i18n.t("date_loading"))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setObjectName("dateLabel")
        self.date_label.setFont(QFont("Segoe UI Semibold", 22))
        center_layout.addWidget(self.date_label)

        # Calendar card
        self.calendar_card = self._create_card(self.i18n.t("calendar_title"), title_icon_svg=CALENDAR_ICON_SVG)
        self.calendar_card.body.setText(self.i18n.t("calendar_setup"))
        self.calendar_card.frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.calendar_card.frame.setMinimumWidth(420)
        self._set_calendar_card_height(2)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addStretch(1)
        if self.services.enable_calendar:
            bottom_row.addWidget(self.calendar_card.frame, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        else:
            self.calendar_card.frame.hide()
        bottom_row.addStretch(1)
        shell.addLayout(bottom_row)

        # Footer with easter egg
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.addStretch(1)
        self.easter_egg_label = QLabel(self.i18n.t("easter_egg"))
        self.easter_egg_label.setObjectName("easterEggLabel")
        footer_row.addWidget(self.easter_egg_label, 0, Qt.AlignmentFlag.AlignRight)
        shell.addLayout(footer_row)

        self._apply_styles()

    def _build_shortcuts(self) -> None:
        """Register keyboard shortcuts."""
        exit_action = QAction(self)
        exit_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        exit_action.triggered.connect(self.close)
        self.addAction(exit_action)

        fullscreen_action = QAction(self)
        fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        self.addAction(fullscreen_action)

    def _start_timers(self) -> None:
        """Set up periodic refresh timers for each service."""
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._refresh_clock)
        self.clock_timer.start(1000)

        self.weather_timer: QTimer | None = None
        if self.services.enable_weather:
            self.weather_timer = QTimer(self)
            self.weather_timer.timeout.connect(self.refresh_weather)
            self.weather_timer.start(10 * 60 * 1000)

        self.spotify_timer: QTimer | None = None
        if self.services.enable_spotify:
            self.spotify_timer = QTimer(self)
            self.spotify_timer.timeout.connect(self.refresh_spotify)
            self.spotify_timer.start(2 * 1000)

        self.calendar_timer: QTimer | None = None
        if self.services.enable_calendar:
            self.calendar_timer = QTimer(self)
            self.calendar_timer.timeout.connect(self.refresh_calendar)
            self.calendar_timer.start(10 * 60 * 1000)

    def _refresh_clock(self) -> None:
        """Update the clock and date labels."""
        now = datetime.now().astimezone()
        self.clock_label.setText(now.strftime(CLOCK_FORMAT))
        self.date_label.setText(self.locale.toString(now, "dddd, d MMMM yyyy"))

    def refresh_all(self) -> None:
        """Trigger refresh for all enabled services."""
        if self.services.enable_weather:
            self.refresh_weather()
        if self.services.enable_spotify:
            self.refresh_spotify()
        if self.services.enable_calendar:
            self.refresh_calendar()

    def refresh_weather(self) -> None:
        """Fetch weather data in background."""
        if not self.services.enable_weather or self.refresh_state.weather_busy or self._closing:
            return
        self.refresh_state.weather_busy = True
        if not self.refresh_state.weather_loaded:
            self.weather_card.subtitle.setText(self.i18n.t("loading"))
        self._run_async(
            self.services.weather.fetch,
            on_success=self._show_weather,
            on_error=self._show_weather_error,
            on_finish=lambda: setattr(self.refresh_state, "weather_busy", False),
        )

    def refresh_spotify(self) -> None:
        """Fetch Spotify playback in background."""
        if not self.services.enable_spotify or self.refresh_state.spotify_busy or self._closing:
            return
        self.refresh_state.spotify_busy = True
        if not self.refresh_state.spotify_loaded:
            self.spotify_card.subtitle.setText(self.i18n.t("spotify_connecting"))
        self._run_async(
            self.services.spotify.fetch,
            on_success=self._show_spotify,
            on_error=self._show_spotify_error,
            on_finish=lambda: setattr(self.refresh_state, "spotify_busy", False),
        )

    def refresh_calendar(self) -> None:
        """Fetch calendar events in background."""
        if not self.services.enable_calendar or self.refresh_state.calendar_busy or self._closing:
            return
        self.refresh_state.calendar_busy = True
        if not self.refresh_state.calendar_loaded:
            self.calendar_card.subtitle.setText(self.i18n.t("loading"))
        self._run_async(
            self.services.calendar.fetch_today,
            on_success=self._show_calendar,
            on_error=self._show_calendar_error,
            on_finish=lambda: setattr(self.refresh_state, "calendar_busy", False),
        )

    def _show_weather(self, snapshot: object) -> None:
        """Update weather card with fetched data."""
        weather: WeatherSnapshot = snapshot
        self.refresh_state.weather_loaded = True
        self._set_label_text(self.weather_card.subtitle, weather.location_name)
        self._set_label_text(self.weather_card.body, f"{weather.temperature_c:.1f} °C — {weather.description}")
        self.weather_card.frame.adjustSize()

    def _show_weather_error(self, message: str) -> None:
        """Show error message in weather card."""
        self._set_label_text(self.weather_card.subtitle, self.i18n.t("weather_unavailable"))
        if not self.refresh_state.weather_loaded:
            self._set_label_text(self.weather_card.body, message)

    def _show_spotify(self, snapshot: object) -> None:
        """Update Spotify card with fetched data."""
        spotify: SpotifySnapshot = snapshot
        self.refresh_state.spotify_loaded = True
        self._set_label_text(
            self.spotify_card.subtitle,
            self.i18n.t("spotify_playing") if spotify.is_playing else self.i18n.t("spotify_not_playing"),
        )
        self._set_label_text(self.spotify_card.body, spotify.title)
        if self.spotify_card.secondary is not None:
            self._set_label_text(self.spotify_card.secondary, spotify.artist)
        self._update_album_art(spotify.album_art_url)

    def _show_spotify_error(self, message: str) -> None:
        """Show error message in Spotify card."""
        self._set_label_text(self.spotify_card.subtitle, self.i18n.t("spotify_unavailable"))
        if not self.refresh_state.spotify_loaded:
            self._set_label_text(self.spotify_card.body, message)
        if self.spotify_card.secondary is not None:
            self._set_label_text(self.spotify_card.secondary, "")

    def _show_calendar(self, events: object) -> None:
        """Update calendar card with fetched events."""
        today_events = events
        self.refresh_state.calendar_loaded = True
        self._set_label_text(self.calendar_card.subtitle, self.i18n.t("calendar_today"))
        if not today_events:
            self._set_label_text(self.calendar_card.body, self.i18n.t("calendar_no_events"))
            self._set_calendar_card_height(1)
            self._set_calendar_card_width(420)
            return

        lines = [f"{event.start_text}  {event.title}" for event in today_events[:6]]
        if len(today_events) > 6:
            lines.append(self.i18n.t("calendar_more_events", count=len(today_events) - 6))
        self._set_label_text(self.calendar_card.body, "\n".join(lines))
        self._set_calendar_card_height(len(lines))
        longest_line = max((len(line) for line in lines), default=24)
        self._set_calendar_card_width(min(920, max(420, 180 + (longest_line * 8))))

    def _show_calendar_error(self, message: str) -> None:
        """Show error message in calendar card."""
        self._set_label_text(self.calendar_card.subtitle, self.i18n.t("calendar_unavailable"))
        if not self.refresh_state.calendar_loaded:
            self._set_label_text(self.calendar_card.body, message)
        self._set_calendar_card_height(2)
        self._set_calendar_card_width(480)

    def _update_album_art(self, url: str | None) -> None:
        """Download and display album artwork."""
        if self.spotify_card.media is None:
            return
        if not url:
            self.spotify_card.media.clear()
            self.spotify_card.media.setText(self.i18n.t("album_missing"))
            self._album_art_url = None
            return
        if url == self._album_art_url:
            return

        self._album_art_url = url
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
        except requests.RequestException:
            self.spotify_card.media.clear()
            self.spotify_card.media.setText(self.i18n.t("album_unavailable"))
            return

        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        if pixmap.isNull():
            self.spotify_card.media.clear()
            self.spotify_card.media.setText(self.i18n.t("album_unavailable"))
            return

        self.spotify_card.media.setPixmap(
            pixmap.scaled(108, 108, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        )

    def _run_async(
        self,
        func: Callable[[], object],
        *,
        on_success: Callable[[object], None],
        on_error: Callable[[str], None],
        on_finish: Callable[[], None],
    ) -> None:
        """Run a function in the thread pool with callbacks."""
        worker = Worker(func)
        self._active_workers.add(worker)
        worker.signals.success.connect(on_success)
        worker.signals.error.connect(on_error)
        worker.signals.success.connect(lambda _result, w=worker: self._finish_worker(w, on_finish))
        worker.signals.error.connect(lambda _message, w=worker: self._finish_worker(w, on_finish))
        self.thread_pool.start(worker)

    def _toggle_fullscreen(self) -> None:
        """Toggle between fullscreen and normal window mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event) -> None:
        """Clean up timers and threads before closing."""
        self._closing = True
        for timer in (self.clock_timer, self.weather_timer, self.spotify_timer, self.calendar_timer):
            if timer is not None:
                timer.stop()
        self.thread_pool.clear()
        self.thread_pool.waitForDone(3000)
        QApplication.instance().quit()
        event.accept()

    def _apply_styles(self) -> None:
        """10/04/26 - Change to the black bg stylesheet."""
        self.setStyleSheet(
            """
            QWidget#root {
                background: #000000;
            }
            QFrame[card="true"] {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
            }
            QLabel[cardTitle="true"] {
                color: rgba(255, 255, 255, 0.92);
                font-size: 15px;
                font-weight: 600;
            }
            QLabel[cardSubtitle="true"] {
                color: rgba(255, 255, 255, 0.55);
                font-size: 12px;
            }
            QLabel[cardBody="true"] {
                color: rgba(255, 255, 255, 0.88);
                font-size: 14px;
            }
            QLabel[cardSecondary="true"] {
                color: rgba(255, 255, 255, 0.60);
                font-size: 13px;
            }
            QLabel[media="true"] {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.40);
                font-size: 11px;
            }
            QLabel[iconLabel="true"] {
                background: transparent;
            }
            QLabel#clockLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 82px;
                font-weight: 700;
                letter-spacing: 4px;
            }
            QLabel#dateLabel {
                color: rgba(255, 255, 255, 0.70);
                font-size: 22px;
                font-weight: 600;
            }
            QLabel#easterEggLabel {
                color: rgba(255, 255, 255, 0.25);
                font-size: 11px;
                font-style: italic;
            }
            """
        )

    def _create_card(
        self, title: str, with_media: bool = False, title_icon_svg: str | None = None
    ) -> _CardRefs:
        """Create a styled card widget with title, subtitle, and body."""
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        if title_icon_svg:
            icon_label = QLabel()
            icon_label.setProperty("iconLabel", True)
            icon_label.setPixmap(self._svg_to_pixmap(title_icon_svg, 28, 28))
            header_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        title_column = QWidget()
        title_layout = QVBoxLayout(title_column)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setProperty("cardTitle", True)
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("")
        subtitle_label.setProperty("cardSubtitle", True)
        title_layout.addWidget(subtitle_label)
        header_layout.addWidget(title_column, 1)

        layout.addWidget(header)

        body_row = QWidget()
        body_layout = QHBoxLayout(body_row)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)

        body_label = MarqueeLabel(self.i18n.t("loading")) if with_media else QLabel(self.i18n.t("loading"))
        body_label.setProperty("cardBody", True)
        body_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if with_media:
            body_label.setFixedWidth(300)
            body_label.setFixedHeight(body_label.fontMetrics().lineSpacing() + 8)
        else:
            body_label.setWordWrap(True)

        text_column = QWidget()
        text_layout = QVBoxLayout(text_column)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(10)
        text_layout.addWidget(body_label)

        secondary_label: QLabel | None = None
        if with_media:
            secondary_label = MarqueeLabel("")
            secondary_label.setProperty("cardSecondary", True)
            secondary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            secondary_label.setFixedWidth(300)
            secondary_label.setFixedHeight(secondary_label.fontMetrics().lineSpacing() + 6)
            text_layout.addWidget(secondary_label)

        body_layout.addWidget(text_column, 1)

        media_label: QLabel | None = None
        if with_media:
            media_label = QLabel(self.i18n.t("album_missing"))
            media_label.setProperty("media", True)
            media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            media_label.setFixedSize(108, 108)
            media_label.setScaledContents(True)
            body_layout.addWidget(media_label, 0, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(body_row)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 90))
        frame.setGraphicsEffect(shadow)

        return _CardRefs(
            frame=frame,
            subtitle=subtitle_label,
            body=body_label,
            text_column=text_column,
            secondary=secondary_label,
            media=media_label,
        )

    def _svg_to_pixmap(self, svg_text: str, width: int, height: int) -> QPixmap:
        """Render SVG string to a QPixmap."""
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer = QSvgRenderer(svg_text.encode("utf-8"))
        renderer.render(painter)
        painter.end()
        return pixmap

    def _set_calendar_card_height(self, line_count: int) -> None:
        """Adjust calendar card height based on content lines."""
        lines = max(1, min(line_count, 7))
        metrics = self.calendar_card.body.fontMetrics()
        line_height = metrics.lineSpacing()
        body_height = (line_height * lines) + 8
        total_height = body_height + 78
        self.calendar_card.frame.setMinimumHeight(total_height)
        self.calendar_card.frame.setMaximumHeight(total_height)
        self.calendar_card.frame.adjustSize()

    def _set_calendar_card_width(self, width: int) -> None:
        """Adjust calendar card width, clamped to reasonable bounds."""
        target_width = max(420, min(width, 920))
        self.calendar_card.frame.setMinimumWidth(target_width)
        self.calendar_card.frame.setMaximumWidth(target_width)
        self.calendar_card.frame.adjustSize()

    def _finish_worker(self, worker: Worker, on_finish: Callable[[], None]) -> None:
        """Clean up a completed worker and run its finish callback."""
        self._active_workers.discard(worker)
        on_finish()

    @staticmethod
    def _set_label_text(label: QLabel, text: str) -> None:
        """Update label text only if it changed (avoids unnecessary redraws)."""
        if label.text() != text:
            label.setText(text)


def launch_dashboard(services: DashboardServices) -> int:
    """Create and show the main dashboard window."""
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(services.i18n.t("app_title"))
    window = StatusClockWindow(services)
    app.aboutToQuit.connect(window.deleteLater)
    window.showFullScreen()
    return app.exec()
