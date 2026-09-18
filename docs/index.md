# wintask

`wintask` manages Windows Task Scheduler tasks from Python through a native
Rust and PyO3 bridge.

## What it provides

- Daily, weekly, and monthly schedules.
- The active Python interpreter as the task command.
- Windows-compatible script arguments.
- Configurable working directory, enabled state, and task description.
- COM calls isolated in a small native backend.

## Quick example

```python
from datetime import time

from wintask import TaskScheduler

TaskScheduler().create_daily(
    name="Data refresh",
    script_path="C:/work/jobs/refresh.py",
    at=time(9, 30),
    arguments=("--environment", "production"),
    description="Refreshes the production data set",
)
```

Continue with [Getting started](getting-started.md), or inspect the
[API reference](api.md) and [Architecture](architecture.md).