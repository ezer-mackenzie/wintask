from dataclasses import dataclass
from datetime import time
from enum import Enum

from .validation import validate_integer, validate_time


class Weekday(str, Enum):
    """Weekday names accepted by Windows Task Scheduler XML."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class Month(str, Enum):
    """Month names accepted by Windows Task Scheduler XML."""

    JANUARY = "January"
    FEBRUARY = "February"
    MARCH = "March"
    APRIL = "April"
    MAY = "May"
    JUNE = "June"
    JULY = "July"
    AUGUST = "August"
    SEPTEMBER = "September"
    OCTOBER = "October"
    NOVEMBER = "November"
    DECEMBER = "December"


@dataclass(frozen=True)
class DailyTrigger:
    """Describe a recurring local-time daily trigger."""

    at: time
    interval: int = 1

    def __post_init__(self) -> None:
        validate_integer(self.interval, "interval", 1, 365)
        validate_time(self.at)


@dataclass(frozen=True)
class WeeklyTrigger:
    """Describe a recurring trigger on one or more local weekdays."""

    at: time
    days: tuple[Weekday, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.days, tuple):
            raise TypeError("days must be a tuple of Weekday values")
        if not self.days:
            raise ValueError("days must contain at least one weekday")
        if any(type(value) is not Weekday for value in self.days):
            raise TypeError("days must contain Weekday values")
        if len(set(self.days)) != len(self.days):
            raise ValueError("days must not contain duplicates")
        validate_time(self.at)


@dataclass(frozen=True)
class MonthlyTrigger:
    """Describe a trigger on a day of selected months."""

    at: time
    day: int
    months: tuple[Month, ...]

    def __post_init__(self) -> None:
        validate_integer(self.day, "day", 1, 31)
        if not isinstance(self.months, tuple):
            raise TypeError("months must be a tuple of Month values")
        if not self.months:
            raise ValueError("months must contain at least one month")
        if any(type(value) is not Month for value in self.months):
            raise TypeError("months must contain Month values")
        if len(set(self.months)) != len(self.months):
            raise ValueError("months must not contain duplicates")
        validate_time(self.at)
