from __future__ import annotations

from .errors import TaskNameError


def validate_task_name(name: str) -> str:
    """Validate and return a task name suitable for the root task folder."""
    if type(name) is not str:
        raise TaskNameError("task name must be a string")
    if not name or not name.strip():
        raise TaskNameError("task name must not be empty")
    if "\\" in name:
        raise TaskNameError("task name must not contain backslashes")
    if any(ord(character) < 32 for character in name):
        raise TaskNameError("task name must not contain control characters")
    return name