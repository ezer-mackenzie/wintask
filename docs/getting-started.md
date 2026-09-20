# Getting started

## Requirements

- Windows for actual Task Scheduler operations.
- Standard CPython 3.9 through 3.14; see the [support matrix](support.md).
- Rust 1.85+ and Cargo when building from source.
- `uv` and `maturin`.

## Install for development

```powershell
uv sync --group docs
uv run maturin develop --uv
```

## Create a task

```python
from datetime import time

from wintask import TaskScheduler, Weekday

scheduler = TaskScheduler()
scheduler.create_weekly(
    name="Weekday job",
    script_path="C:/work/job.py",
    at=time(8, 0),
    days=(Weekday.MONDAY, Weekday.FRIDAY),
    working_directory="C:/work",
    arguments=("--verbose",),
)
```

The script must exist. Times are naive local times because Windows Task
Scheduler interprets the generated boundary in the machine's local context.

## Manage a task

```python
scheduler.run("Weekday job")
scheduler.delete("Weekday job")
```

Task registration requires a Windows account with permission to create tasks.

## Verify a checkout

```powershell
$env:PYO3_PYTHON = (Join-Path $PWD ".venv\Scripts\python.exe")
cargo check
uv run python -m unittest discover -s tests -v
uv run --group docs mkdocs build --strict
```
