"""Reusable widgets and worker helpers for the dashboard UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QTimer, Qt, Signal
from PySide6.QtGui import QPainter, QStyle, QStyleOption
from PySide6.QtWidgets import QFrame, QLabel, QWidget


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
