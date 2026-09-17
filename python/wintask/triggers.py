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
        if any(type(day) is not Weekday for day in self.days):
            raise TypeError("days must contain Weekday values")
        if self.at.tzinfo is not None:
            raise ValueError("at must be a naive local time")


@dataclass(frozen=True)
class MonthlyTrigger:
    """Describe a trigger on a day of selected months."""

    at: time
    day: int
    months: tuple[Month, ...]

    def __post_init__(self) -> None:
        if not 1 <= self.day <= 31:
            raise ValueError("day must be between 1 and 31")
        if not self.months:
            raise ValueError("months must contain at least one month")
        if len(set(self.months)) != len(self.months):
            raise ValueError("months must not contain duplicates")
        if any(type(month) is not Month for month in self.months):
            raise TypeError("months must contain Month values")
        if self.at.tzinfo is not None:
            raise ValueError("at must be a naive local time")