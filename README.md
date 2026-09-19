# wintask

Read the full documentation at [wintask.readthedocs.io](https://wintask.readthedocs.io/).

`wintask` is a Python library for managing Windows Task Scheduler tasks through
the native Windows Task Scheduler COM API. Python provides the ergonomic API,
validation, and Task Scheduler XML generation; Rust provides a small PyO3
bridge that owns COM initialization and calls `ITaskService`.

Invalid task names raise the public `TaskNameError` before any native call is
made. Names must be non-empty and cannot contain control characters or
backslashes because the current API registers tasks in the root folder.

Use `TaskScheduler.exists(name)` to check whether a task is registered before
creating, running, or deleting it.

## Purpose

The project aims to make scheduled Python jobs predictable and easy to manage
from Python code. A caller should be able to create, run, and delete a task
without invoking `schtasks.exe`, assembling command lines manually, or
depending on undocumented Windows APIs.

The first release focuses on one reliable workflow:

1. Select the active Python interpreter with `sys.executable`.
2. Create a daily trigger for an existing Python script.
3. Register the generated XML with Windows Task Scheduler.
4. Run or delete the task by name.

## Architecture

```text
Python application
	|
	v
TaskScheduler -> builder -> Task Scheduler XML
	|
	v
PyO3 extension (_wintask_backend)
	|
	v
Rust COM bridge -> ITaskService / ITaskFolder / IRegisteredTask
	|
	v
Windows Task Scheduler
```

### Python layer

The Python layer is responsible for:

- The public `TaskScheduler` API.
- Typed trigger models such as `DailyTrigger`.
- Input validation and filesystem path resolution.
- XML serialization using the official Task Scheduler namespace.
- Using the current virtual environment's `sys.executable` as the action
  command and the script directory as its working directory.

### Rust layer

The Rust extension is deliberately narrow. It is responsible for:

- Initializing and uninitializing COM with RAII.
- Connecting to `Schedule.Service` through `ITaskService`.
- Registering XML, deleting tasks, and starting registered tasks.
- Translating Windows errors into Python runtime or permission exceptions.

Rust does not decide scheduling policy or build business-level XML.

## Requirements

- Windows for actual Task Scheduler operations.
- Python 3.9 or newer.
- Rust toolchain with Cargo.
- `uv` for environment and dependency management.
- `maturin` 1.15 or newer, installed by the project build configuration.

The package can be compiled on non-Windows hosts for development, but native
Task Scheduler operations return a `RuntimeError` there.

## Installation

Create or synchronize the development environment:

```powershell
uv sync
```

Build and install the mixed Python/Rust project in the active environment:

```powershell
uv run maturin develop --uv
```

For a release build:

```powershell
uv run maturin develop --uv --release
```

## Usage

```python
from datetime import time

from wintask import TaskScheduler

scheduler = TaskScheduler()

scheduler.create_daily(
    name="Example Python Job",
    script_path="C:/Users/example/project/job.py",
    at=time(9, 30),
    wake_to_run=True,
	interval=1,
	arguments=("--environment", "production"),
	working_directory="C:/Users/example/project",
	enabled=True,
	description="Runs the daily data refresh",
)

scheduler.run("Example Python Job")
scheduler.delete("Example Python Job")
```

Weekly schedules are also supported:

```python
from datetime import time

from wintask import TaskScheduler, Weekday

TaskScheduler().create_weekly(
	name="Weekday Python Job",
	script_path="C:/Users/example/project/job.py",
	at=time(9, 30),
	days=(Weekday.MONDAY, Weekday.FRIDAY),
)
```

Monthly schedules are supported with an explicit day of the month:

```python
from datetime import time

from wintask import Month, TaskScheduler

TaskScheduler().create_monthly(
	name="Monthly Python Job",
	script_path="C:/Users/example/project/job.py",
	at=time(9, 30),
	day=15,
	months=(Month.JANUARY, Month.JUNE),
)
```

`script_path` must point to an existing file. The time is a naive local
`datetime.time`; timezone-aware times are rejected because Windows Task
Scheduler interprets the generated boundary in the local machine context.

For direct XML generation:

```python
from datetime import time

from wintask.builder import build_daily_xml
from wintask.triggers import DailyTrigger

xml = build_daily_xml(
    "C:/Users/example/project/job.py",
    DailyTrigger(at=time(9, 30), interval=1),
)
```

## Public API

### `TaskScheduler`

- `create_daily(name, script_path, at, wake_to_run=False, interval=1,
	arguments=())` registers or updates a daily task.
- `create_weekly(name, script_path, at, days, wake_to_run=False,
	arguments=())` registers or updates a weekly task.
- `create_monthly(name, script_path, at, day, months, wake_to_run=False,
	arguments=())` registers or updates a monthly task.
- `arguments`: command-line arguments passed to the Python script. Values are
	quoted using Windows command-line rules.
- `working_directory`: existing directory used as the task process working
	directory. Defaults to the script's parent directory.
- `enabled`: whether the task is enabled when registered. Defaults to `True`.
- `description`: optional text displayed in Task Scheduler's task metadata.
- `run(name)` starts an existing registered task.
- `delete(name)` removes an existing registered task.
- `exists(name)` returns whether a task is registered in the root folder.
  Missing tasks return `False`; permission and other native errors propagate.

### `DailyTrigger`

- `at`: local time at which the task starts.
- `interval`: number of days between runs; must be at least `1`.

### `WeeklyTrigger`

- `at`: local time at which the task starts.
- `days`: one or more `Weekday` values.

### `Weekday`

Provides the `MONDAY` through `SUNDAY` values used by weekly triggers.

### `MonthlyTrigger`

- `at`: local time at which the task starts.
- `day`: day of the month from `1` through `31`.
- `months`: one or more `Month` values.

### `Month`

Provides the `JANUARY` through `DECEMBER` values used by monthly triggers.

### `build_daily_xml`

Builds the XML consumed by Task Scheduler. It is useful for inspection,
testing, or integration with a lower-level registration flow.

## Permissions and security

Tasks are registered in the root Task Scheduler folder using the interactive
token logon type. The current implementation does not accept passwords or
arbitrary credentials. The caller's Windows account must have permission to
create, execute, and delete the requested task.

Never pass untrusted task names, script paths, or XML to privileged automation
without validating them in the application that calls `wintask`. See
[SECURITY.md](SECURITY.md) for reporting security issues.

## Development and verification

Run the Rust checks with the project's Python interpreter available to PyO3:

```powershell
$env:PYO3_PYTHON = (Join-Path $PWD ".venv\Scripts\python.exe")
cargo check
```

Validate the Python sources:

```powershell
uv run python -m compileall -q python
```

Verify installation and import:

```powershell
uv run python -c "from wintask import DailyTrigger, TaskScheduler; print('wintask import: OK')"
```

Run the opt-in Windows integration test (creates and deletes a disabled task):

```powershell
$env:WINTASK_INTEGRATION = "1"
uv run python -m unittest discover -s tests -v
```

## Project layout

```text
Cargo.toml                 Rust package and native dependencies
pyproject.toml             Python packaging and maturin configuration
src/lib.rs                 PyO3 extension and COM bridge
python/wintask/__init__.py Public Python exports
python/wintask/scheduler.py High-level task operations
python/wintask/triggers.py Typed trigger models
python/wintask/builder.py  Task Scheduler XML serialization
```

## Project status

Version `0.9.0` adds task existence checks with validated task names. The project
supports descriptions, configurable working directories, enabled state,
arguments, and daily, weekly, and monthly trigger schedules. Richer principals, task folders, and detailed HRESULT
exception types remain future work.
