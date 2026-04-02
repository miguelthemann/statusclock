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
    QVBoxLayout,
    QWidget,
)

from .i18n import I18N, get_qlocale
from .services.calendar_service import GoogleCalendarService
from .services.spotify import SpotifyService, SpotifySnapshot
from .services.weather import WeatherService, WeatherSnapshot


CLOCK_FORMAT = "%H:%M:%S"
CALENDAR_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="8" y="10" width="48" height="46" rx="10" fill="#ffffff"/>
  <rect x="8" y="10" width="48" height="14" rx="10" fill="#ea4335"/>
  <rect x="14" y="4" width="6" height="16" rx="3" fill="#4285f4"/>
  <rect x="44" y="4" width="6" height="16" rx="3" fill="#34a853"/>
  <rect x="18" y="30" width="10" height="10" rx="2" fill="#fbbc05"/>
  <rect x="34" y="30" width="12" height="12" rx="3" fill="#4285f4"/>
  <rect x="18" y="44" width="28" height="4" rx="2" fill="#dadce0"/>
</svg>
""".strip()


class WorkerSignals(QObject):
    success = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    def __init__(self, func: Callable[[], object]) -> None:
        super().__init__()
        self.func = func
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.func()
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(str(exc))
        else:
            self.signals.success.emit(result)


class MarqueeLabel(QLabel):
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

    def setText(self, text: str) -> None:  # type: ignore[override]
        super().setText(text)
        self._offset = 0
        self._pause_ticks = self._pause_duration
        self.update()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        new_width = event.size().width()
        if new_width != self._last_width:
            self._offset = 0
            self._pause_ticks = self._pause_duration
            self._last_width = new_width
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setFont(self.font())
        painter.setPen(self.palette().windowText().color())

        text = self.text()
        if not text:
            return

        rect = self.contentsRect()
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        baseline = rect.y() + metrics.ascent() + max(0, (rect.height() - metrics.height()) // 2)

        if text_width <= rect.width():
            painter.drawText(rect, int(self.alignment()), text)
            return

        x = rect.x() - self._offset
        painter.setClipRect(rect)
        painter.drawText(x, baseline, text)
        painter.drawText(x + text_width + self._gap_px, baseline, text)

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
    i18n: I18N
    weather: WeatherService
    spotify: SpotifyService
    calendar: GoogleCalendarService


@dataclass(slots=True)
class _CardRefs:
    frame: QFrame
    subtitle: QLabel
    body: QLabel
    text_column: QWidget | None = None
    secondary: QLabel | None = None
    media: QLabel | None = None


@dataclass(slots=True)
class _RefreshState:
    weather_busy: bool = False
    spotify_busy: bool = False
    calendar_busy: bool = False
    weather_loaded: bool = False
    spotify_loaded: bool = False
    calendar_loaded: bool = False


class StatusClockWindow(QMainWindow):
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
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        shell = QVBoxLayout(root)
        shell.setContentsMargins(26, 20, 26, 16)
        shell.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        shell.addLayout(top_row)

        self.weather_card = self._create_card(self.i18n.t("weather_title"))
        self.weather_card.body.setText(self.i18n.t("weather_setup"))
        self.weather_card.frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.weather_card.frame.setMaximumWidth(360)

        self.spotify_card = self._create_card(self.i18n.t("spotify_title"), with_media=True)
        self.spotify_card.body.setText(self.i18n.t("spotify_setup_title"))
        if self.spotify_card.secondary is not None:
            self.spotify_card.secondary.setText(self.i18n.t("spotify_setup_subtitle"))
        self.spotify_card.frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.spotify_card.frame.setMinimumWidth(480)
        self.spotify_card.frame.setMaximumWidth(480)
        if self.spotify_card.text_column is not None:
            self.spotify_card.text_column.setFixedWidth(300)

        top_row.addWidget(self.weather_card.frame, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_row.addStretch(1)
        top_row.addWidget(self.spotify_card.frame, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

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
        self.clock_label.setMinimumWidth(
            self.clock_label.fontMetrics().horizontalAdvance("88:88:88") + 24
        )
        center_layout.addWidget(self.clock_label)

        self.date_label = QLabel(self.i18n.t("date_loading"))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setObjectName("dateLabel")
        self.date_label.setFont(QFont("Segoe UI Semibold", 22))
        center_layout.addWidget(self.date_label)

        self.calendar_card = self._create_card(self.i18n.t("calendar_title"), title_icon_svg=CALENDAR_ICON_SVG)
        self.calendar_card.body.setText(self.i18n.t("calendar_setup"))
        self.calendar_card.frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.calendar_card.frame.setMinimumWidth(420)
        self._set_calendar_card_height(2)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addStretch(1)
        bottom_row.addWidget(
            self.calendar_card.frame,
            0,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
        )
        bottom_row.addStretch(1)
        shell.addLayout(bottom_row)

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.addStretch(1)
        self.easter_egg_label = QLabel(self.i18n.t("easter_egg"))
        self.easter_egg_label.setObjectName("easterEggLabel")
        footer_row.addWidget(self.easter_egg_label, 0, Qt.AlignmentFlag.AlignRight)
        shell.addLayout(footer_row)

        self._apply_styles()

    def _build_shortcuts(self) -> None:
        exit_action = QAction(self)
        exit_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        exit_action.triggered.connect(self.close)
        self.addAction(exit_action)

        fullscreen_action = QAction(self)
        fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        self.addAction(fullscreen_action)

    def _start_timers(self) -> None:
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._refresh_clock)
        self.clock_timer.start(1000)

        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.refresh_weather)
        self.weather_timer.start(10 * 60 * 1000)

        self.spotify_timer = QTimer(self)
        self.spotify_timer.timeout.connect(self.refresh_spotify)
        self.spotify_timer.start(2 * 1000)

        self.calendar_timer = QTimer(self)
        self.calendar_timer.timeout.connect(self.refresh_calendar)
        self.calendar_timer.start(10 * 60 * 1000)

    def _refresh_clock(self) -> None:
        now = datetime.now().astimezone()
        self.clock_label.setText(now.strftime(CLOCK_FORMAT))
        self.date_label.setText(self.locale.toString(now, "dddd, d MMMM yyyy"))

    def refresh_all(self) -> None:
        self.refresh_weather()
        self.refresh_spotify()
        self.refresh_calendar()

    def refresh_weather(self) -> None:
        if self.refresh_state.weather_busy or self._closing:
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
        if self.refresh_state.spotify_busy or self._closing:
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
        if self.refresh_state.calendar_busy or self._closing:
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
        weather: WeatherSnapshot = snapshot
        self.refresh_state.weather_loaded = True
        self._set_label_text(self.weather_card.subtitle, weather.location_name)
        self._set_label_text(
            self.weather_card.body, f"{weather.temperature_c:.1f} \u00b0C\n{weather.description}"
        )
        self.weather_card.frame.adjustSize()

    def _show_weather_error(self, message: str) -> None:
        self._set_label_text(self.weather_card.subtitle, self.i18n.t("weather_unavailable"))
        if not self.refresh_state.weather_loaded:
            self._set_label_text(self.weather_card.body, message)

    def _show_spotify(self, snapshot: object) -> None:
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
        self._set_label_text(self.spotify_card.subtitle, self.i18n.t("spotify_unavailable"))
        if not self.refresh_state.spotify_loaded:
            self._set_label_text(self.spotify_card.body, message)
            if self.spotify_card.secondary is not None:
                self._set_label_text(self.spotify_card.secondary, "")

    def _show_calendar(self, events: object) -> None:
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
        self._set_label_text(self.calendar_card.subtitle, self.i18n.t("calendar_unavailable"))
        if not self.refresh_state.calendar_loaded:
            self._set_label_text(self.calendar_card.body, message)
            self._set_calendar_card_height(2)
            self._set_calendar_card_width(480)

    def _update_album_art(self, url: str | None) -> None:
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
            pixmap.scaled(
                108,
                108,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _run_async(
        self,
        func: Callable[[], object],
        *,
        on_success: Callable[[object], None],
        on_error: Callable[[str], None],
        on_finish: Callable[[], None],
    ) -> None:
        worker = Worker(func)
        self._active_workers.add(worker)
        worker.signals.success.connect(on_success)
        worker.signals.error.connect(on_error)
        worker.signals.success.connect(lambda _result, w=worker: self._finish_worker(w, on_finish))
        worker.signals.error.connect(lambda _message, w=worker: self._finish_worker(w, on_finish))
        self.thread_pool.start(worker)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._closing = True
        for timer in (self.clock_timer, self.weather_timer, self.spotify_timer, self.calendar_timer):
            timer.stop()
        self.thread_pool.clear()
        self.thread_pool.waitForDone(3000)
        QApplication.instance().quit()
        event.accept()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #0b1220,
                    stop: 0.45 #111a2f,
                    stop: 1 #1f3b57
                );
                color: #f5f7fb;
            }
            QFrame[card="true"] {
                background-color: rgba(8, 14, 27, 0.68);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 24px;
            }
            QLabel[cardTitle="true"] {
                color: #9fc4ff;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.12em;
            }
            QLabel[cardSubtitle="true"] {
                color: rgba(159, 196, 255, 0.75);
                font-size: 13px;
                font-weight: 600;
            }
            QLabel[cardBody="true"] {
                color: #f4f7fb;
                font-size: 19px;
                font-weight: 600;
            }
            QLabel[cardSecondary="true"] {
                color: rgba(244, 247, 251, 0.76);
                font-size: 16px;
                font-weight: 500;
            }
            QLabel[media="true"] {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 18px;
                color: rgba(244, 247, 251, 0.55);
                font-size: 14px;
                font-weight: 600;
            }
            QLabel[iconLabel="true"] {
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }
            QLabel#clockLabel {
                color: #ffffff;
            }
            QLabel#dateLabel {
                color: rgba(244, 247, 251, 0.86);
            }
            QLabel#easterEggLabel {
                color: rgba(244, 247, 251, 0.42);
                font-size: 11px;
                font-style: italic;
                letter-spacing: 0.04em;
            }
            """
        )

    def _create_card(
        self, title: str, with_media: bool = False, title_icon_svg: str | None = None
    ) -> _CardRefs:
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
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer = QSvgRenderer(svg_text.encode("utf-8"))
        renderer.render(painter)
        painter.end()
        return pixmap

    def _set_calendar_card_height(self, line_count: int) -> None:
        lines = max(1, min(line_count, 7))
        metrics = self.calendar_card.body.fontMetrics()
        line_height = metrics.lineSpacing()
        body_height = (line_height * lines) + 8
        total_height = body_height + 78
        self.calendar_card.frame.setMinimumHeight(total_height)
        self.calendar_card.frame.setMaximumHeight(total_height)
        self.calendar_card.frame.adjustSize()

    def _set_calendar_card_width(self, width: int) -> None:
        target_width = max(420, min(width, 920))
        self.calendar_card.frame.setMinimumWidth(target_width)
        self.calendar_card.frame.setMaximumWidth(target_width)
        self.calendar_card.frame.adjustSize()

    def _finish_worker(self, worker: Worker, on_finish: Callable[[], None]) -> None:
        self._active_workers.discard(worker)
        on_finish()

    @staticmethod
    def _set_label_text(label: QLabel, text: str) -> None:
        if label.text() != text:
            label.setText(text)


def launch_dashboard(services: DashboardServices) -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(services.i18n.t("app_title"))
    window = StatusClockWindow(services)
    app.aboutToQuit.connect(window.deleteLater)
    window.showFullScreen()
    return app.exec()
