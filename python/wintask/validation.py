from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from datetime import time

from .errors import TaskNameError

MAX_TASK_NAME_LENGTH = 200  # Library limit in UTF-16 code units, including root-folder headroom.


def validate_task_name(name: str) -> str:
    """Validate a single root-folder task name without changing it."""
    if not isinstance(name, str):
        raise TaskNameError("task name must be a string")
    if not name or name != name.strip():
        raise TaskNameError("task name must be non-empty without surrounding whitespace")
    if name in (".", "..") or name.endswith("."):
        raise TaskNameError("task name must not be a dot path or end with a dot")
    if any(character in '<>:"/\\|?*' for character in name):
        raise TaskNameError("task name contains a reserved path character")
    if any(unicodedata.category(character) in ("Cc", "Cs") for character in name):
        raise TaskNameError("task name must not contain control characters or surrogates")
    if len(name.encode("utf-16-le")) // 2 > MAX_TASK_NAME_LENGTH:
        raise TaskNameError(f"task name must not exceed {MAX_TASK_NAME_LENGTH} UTF-16 code units")
    return name


def validate_time(at: time) -> None:
    if not isinstance(at, time):
        raise TypeError("at must be a datetime.time")
    if at.tzinfo is not None:
        raise ValueError("at must be a naive local time")
    if at.microsecond:
        raise ValueError("at must have whole-second precision")
    if at.fold:
        raise ValueError("at must not select a DST fold; Windows controls local-time transitions")

def validate_integer(value: int, name: str, minimum: int, maximum: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not a boolean")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")


def validate_xml_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if any(
        not (character in "\t\n\r" or 0x20 <= ord(character) <= 0xD7FF
             or 0xE000 <= ord(character) <= 0xFFFD
             or 0x10000 <= ord(character) <= 0x10FFFF)
        for character in value
    ):
        raise ValueError(f"{name} contains a character not allowed in XML 1.0")
    return value


def validate_arguments(arguments: Sequence[str]) -> tuple[str, ...]:
    if isinstance(arguments, (str, bytes)) or not isinstance(arguments, Sequence):
        raise TypeError("arguments must be a sequence of strings, not a string or bytes")
    return tuple(validate_xml_text(argument, "argument") for argument in arguments)
