from __future__ import annotations

from collections.abc import Sequence
from datetime import time
from pathlib import Path

from . import _wintask_backend
from .builder import build_daily_xml, build_monthly_xml, build_weekly_xml
from .triggers import DailyTrigger, Month, MonthlyTrigger, Weekday, WeeklyTrigger
from .validation import validate_task_name


class TaskScheduler:
    """Manage Python tasks registered with Windows Task Scheduler."""

    def create_daily(
        self,
        name: str,
        script_path: str | Path,
        at: time,
        wake_to_run: bool = False,
        interval: int = 1,
        arguments: Sequence[str] = (),
        working_directory: str | Path | None = None,
        enabled: bool = True,
        description: str | None = None,
    ) -> None:
        """Register or update a task that runs a Python script daily."""
        name = validate_task_name(name)
        trigger = DailyTrigger(at, interval=interval)
        xml = build_daily_xml(
            script_path,
            trigger,
            wake_to_run=wake_to_run,
            arguments=arguments,
            working_directory=working_directory,
            enabled=enabled,
            description=description,
        )
        _wintask_backend.register_xml(name, xml)

    def delete(self, name: str) -> None:
        """Delete a task from the root Task Scheduler folder."""
        name = validate_task_name(name)
        _wintask_backend.delete_task(name)

    def run(self, name: str) -> None:
        """Start a registered task immediately."""
        name = validate_task_name(name)
        _wintask_backend.run_task(name)

    def create_weekly(
        self,
        name: str,
        script_path: str | Path,
        at: time,
        days: tuple[Weekday, ...],
        wake_to_run: bool = False,
        arguments: Sequence[str] = (),
        working_directory: str | Path | None = None,
        enabled: bool = True,
        description: str | None = None,
    ) -> None:
        """Register or update a task that runs on selected weekdays."""
        name = validate_task_name(name)
        trigger = WeeklyTrigger(at, days=days)
        xml = build_weekly_xml(
            script_path,
            trigger,
            wake_to_run=wake_to_run,
            arguments=arguments,
            working_directory=working_directory,
            enabled=enabled,
            description=description,
        )
        _wintask_backend.register_xml(name, xml)

    def create_monthly(
        self,
        name: str,
        script_path: str | Path,
        at: time,
        day: int,
        months: tuple[Month, ...],
        wake_to_run: bool = False,
        arguments: Sequence[str] = (),
        working_directory: str | Path | None = None,
        enabled: bool = True,
        description: str | None = None,
    ) -> None:
        """Register or update a task that runs on selected month days."""
        name = validate_task_name(name)
        trigger = MonthlyTrigger(at, day=day, months=months)
        xml = build_monthly_xml(
            script_path,
            trigger,
            wake_to_run=wake_to_run,
            arguments=arguments,
            working_directory=working_directory,
            enabled=enabled,
            description=description,
        )
        _wintask_backend.register_xml(name, xml)