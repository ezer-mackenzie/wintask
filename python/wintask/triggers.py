from dataclasses import dataclass
from datetime import time
from enum import Enum


class Weekday(str, Enum):
    """Weekday names accepted by Windows Task Scheduler XML."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


@dataclass(frozen=True)
class DailyTrigger:
    """Describe a recurring local-time daily trigger."""

    at: time
    interval: int = 1

    def __post_init__(self) -> None:
        if self.interval < 1:
            raise ValueError("interval must be greater than zero")
        if self.at.tzinfo is not None:
            raise ValueError("at must be a naive local time")


@dataclass(frozen=True)
class WeeklyTrigger:
    """Describe a recurring trigger on one or more local weekdays."""

    at: time
    days: tuple[Weekday, ...]

    def __post_init__(self) -> None:
        if not self.days:
            raise ValueError("days must contain at least one weekday")
        if len(set(self.days)) != len(self.days):
            raise ValueError("days must not contain duplicates")
        if any(not isinstance(day, Weekday) for day in self.days):
            raise TypeError("days must contain Weekday values")
        if self.at.tzinfo is not None:
            raise ValueError("at must be a naive local time")