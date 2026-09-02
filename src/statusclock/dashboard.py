"""Compatibility wrapper for the old dashboard module location."""

from .ui import StatusClockWindow, launch_dashboard
from .core import DashboardServices

__all__ = ["DashboardServices", "StatusClockWindow", "launch_dashboard"]
