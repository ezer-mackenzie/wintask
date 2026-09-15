from dataclasses import dataclass
from datetime import time


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