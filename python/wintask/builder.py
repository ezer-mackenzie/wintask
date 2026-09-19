from __future__ import annotations

import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from subprocess import list2cmdline
from xml.etree.ElementTree import Element, SubElement, tostring

from .triggers import DailyTrigger, MonthlyTrigger, WeeklyTrigger

# COM receives Unicode XML as a BSTR; omit a conflicting byte-encoding declaration.
NAMESPACE = "http://schemas.microsoft.com/windows/2004/02/mit/task"


def build_daily_xml(
    script_path: str | Path,
    trigger: DailyTrigger,
    *,
    wake_to_run: bool = False,
    arguments: Sequence[str] = (),
    working_directory: str | Path | None = None,
    enabled: bool = True,
    description: str | None = None,
) -> str:
    """Serialize a daily Python script task to Task Scheduler XML."""
    script = Path(script_path).expanduser().resolve()
    if not script.is_file():
        raise FileNotFoundError(script)

    task = _build_task(
        script,
        wake_to_run=wake_to_run,
        arguments=arguments,
        working_directory=working_directory,
        enabled=enabled,
        description=description,
    )
    triggers = task.find("Triggers")
    if triggers is None:
        raise RuntimeError("task XML is missing its trigger container")
    daily = SubElement(triggers, "CalendarTrigger")
    local_date = datetime.now(timezone.utc).astimezone().date()
    start = datetime.combine(local_date, trigger.at).replace(microsecond=0)
    SubElement(daily, "StartBoundary").text = start.isoformat()
    SubElement(daily, "Enabled").text = "true"
    repetition = SubElement(daily, "ScheduleByDay")
    SubElement(repetition, "DaysInterval").text = str(trigger.interval)

    return tostring(task, encoding="unicode", xml_declaration=False)


def build_weekly_xml(
    script_path: str | Path,
    trigger: WeeklyTrigger,
    *,
    wake_to_run: bool = False,
    arguments: Sequence[str] = (),
    working_directory: str | Path | None = None,
    enabled: bool = True,
    description: str | None = None,
) -> str:
    """Serialize a weekly Python script task to Task Scheduler XML."""
    script = Path(script_path).expanduser().resolve()
    if not script.is_file():
        raise FileNotFoundError(script)

    task = _build_task(
        script,
        wake_to_run=wake_to_run,
        arguments=arguments,
        working_directory=working_directory,
        enabled=enabled,
        description=description,
    )
    daily = task.find("Triggers")
    if daily is None:
        raise RuntimeError("task XML is missing its trigger container")
    weekly = SubElement(daily, "CalendarTrigger")
    local_date = datetime.now(timezone.utc).astimezone().date()
    start = datetime.combine(local_date, trigger.at).replace(microsecond=0)
    SubElement(weekly, "StartBoundary").text = start.isoformat()
    SubElement(weekly, "Enabled").text = "true"
    schedule = SubElement(weekly, "ScheduleByWeek")
    SubElement(schedule, "WeeksInterval").text = "1"
    weekdays = SubElement(schedule, "DaysOfWeek")
    for day in trigger.days:
        SubElement(weekdays, day.value)

    return tostring(task, encoding="unicode", xml_declaration=False)


def build_monthly_xml(
    script_path: str | Path,
    trigger: MonthlyTrigger,
    *,
    wake_to_run: bool = False,
    arguments: Sequence[str] = (),
    working_directory: str | Path | None = None,
    enabled: bool = True,
    description: str | None = None,
) -> str:
    """Serialize a monthly Python script task to Task Scheduler XML."""
    script = Path(script_path).expanduser().resolve()
    if not script.is_file():
        raise FileNotFoundError(script)

    task = _build_task(
        script,
        wake_to_run=wake_to_run,
        arguments=arguments,
        working_directory=working_directory,
        enabled=enabled,
        description=description,
    )
    triggers = task.find("Triggers")
    if triggers is None:
        raise RuntimeError("task XML is missing its trigger container")
    monthly = SubElement(triggers, "CalendarTrigger")
    local_date = datetime.now(timezone.utc).astimezone().date()
    start = datetime.combine(local_date, trigger.at).replace(microsecond=0)
    SubElement(monthly, "StartBoundary").text = start.isoformat()
    SubElement(monthly, "Enabled").text = "true"
    schedule = SubElement(monthly, "ScheduleByMonth")
    days = SubElement(schedule, "DaysOfMonth")
    SubElement(days, "Day").text = str(trigger.day)
    months = SubElement(schedule, "Months")
    for month in trigger.months:
        SubElement(months, month.value)

    return tostring(task, encoding="unicode", xml_declaration=False)


def _build_task(
    script: Path,
    *,
    wake_to_run: bool = False,
    arguments: Sequence[str] = (),
    working_directory: str | Path | None = None,
    enabled: bool = True,
    description: str | None = None,
) -> Element:
    directory = (
        Path(working_directory).expanduser().resolve()
        if working_directory is not None
        else script.parent
    )
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    task = Element("Task", {"xmlns": NAMESPACE, "version": "1.4"})
    registration = SubElement(task, "RegistrationInfo")
    if description is not None:
        if not description.strip():
            raise ValueError("description must not be empty")
        SubElement(registration, "Description").text = description
    settings = SubElement(task, "Settings")
    SubElement(settings, "MultipleInstancesPolicy").text = "IgnoreNew"
    SubElement(settings, "DisallowStartIfOnBatteries").text = "false"
    SubElement(settings, "StopIfGoingOnBatteries").text = "false"
    SubElement(settings, "WakeToRun").text = str(wake_to_run).lower()
    SubElement(settings, "Enabled").text = str(enabled).lower()
    SubElement(task, "Triggers")
    actions = SubElement(task, "Actions", {"Context": "Author"})
    exec_action = SubElement(actions, "Exec")
    SubElement(exec_action, "Command").text = sys.executable
    command_arguments = list2cmdline([str(script), *arguments])
    SubElement(exec_action, "Arguments").text = command_arguments
    SubElement(exec_action, "WorkingDirectory").text = str(directory)
    return task