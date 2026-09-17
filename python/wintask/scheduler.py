from __future__ import annotations

from datetime import time
from pathlib import Path

from . import _wintask_backend
from .builder import build_daily_xml, build_weekly_xml
from .triggers import DailyTrigger, Weekday, WeeklyTrigger


class TaskScheduler:
    """Manage Python tasks registered with Windows Task Scheduler."""

    def create_daily(
        self,
        name: str,
        script_path: str | Path,
        at: time,
        wake_to_run: bool = False,
        interval: int = 1,
    ) -> None:
        """Register or update a task that runs a Python script daily."""
        trigger = DailyTrigger(at, interval=interval)
        xml = build_daily_xml(script_path, trigger, wake_to_run=wake_to_run)
        _wintask_backend.register_xml(name, xml)

    def delete(self, name: str) -> None:
        """Delete a task from the root Task Scheduler folder."""
        _wintask_backend.delete_task(name)

    def run(self, name: str) -> None:
        """Start a registered task immediately."""
        _wintask_backend.run_task(name)

    def create_weekly(
        self,
        name: str,
        script_path: str | Path,
        at: time,
        days: tuple[Weekday, ...],
        wake_to_run: bool = False,
    ) -> None:
        """Register or update a task that runs on selected weekdays."""
        trigger = WeeklyTrigger(at, days=days)
        xml = build_weekly_xml(script_path, trigger, wake_to_run=wake_to_run)
        _wintask_backend.register_xml(name, xml)