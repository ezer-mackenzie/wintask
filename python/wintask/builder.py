from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from .triggers import DailyTrigger

NAMESPACE = "http://schemas.microsoft.com/windows/2004/02/mit/task"


def build_daily_xml(
    script_path:str | Path,
    trigger: DailyTrigger,
    *,
    wake_to_run: bool = False,
) -> str:
    """Serialize a daily Python script task to Task Scheduler XML."""
    script = Path(script_path).expanduser().resolve()
    if not script.is_file():
        raise FileNotFoundError(script)

    task = Element("Task", {"xmlns": NAMESPACE, "version": "1.4"})
    SubElement(task, "RegistrationInfo")
    settings = SubElement(task, "Settings")
    SubElement(settings, "MultipleInstancesPolicy").text = "IgnoreNew"
    SubElement(settings, "DisallowStartIfOnBatteries").text = "false"
    SubElement(settings, "StopIfGoingOnBatteries").text = "false"
    SubElement(settings, "WakeToRun").text = str(wake_to_run).lower()
    SubElement(settings, "Enabled").text = "true"

    triggers = SubElement(task, "Triggers")
    daily = SubElement(triggers, "CalendarTrigger")
    local_date = datetime.now(timezone.utc).astimezone().date()
    start = datetime.combine(local_date, trigger.at).replace(microsecond=0)
    SubElement(daily, "StartBoundary").text = start.isoformat()
    SubElement(daily, "Enabled").text = "true"
    repetition = SubElement(daily, "ScheduleByDay")
    SubElement(repetition, "DaysInterval").text = str(trigger.interval)

    actions = SubElement(task, "Actions", {"Context": "Author"})
    exec_action = SubElement(actions, "Exec")
    SubElement(exec_action, "Command").text = sys.executable
    SubElement(exec_action, "Arguments").text = f'"{script}"'
    SubElement(exec_action, "WorkingDirectory").text = str(script.parent)

    return tostring(task, encoding="unicode", xml_declaration=True)