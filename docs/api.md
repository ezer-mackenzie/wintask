# API reference

## `TaskScheduler`

`TaskScheduler` exposes `create_daily`, `create_weekly`, and
`create_monthly`. Each method accepts a task name, Python script path, local
start time, optional trigger-specific values, script `arguments`,
`working_directory`, `enabled`, and `description`.

Use `run(name)` to start a registered task immediately and `delete(name)` to
remove it from the root Task Scheduler folder.

`exists(name)` returns `True` when the task is registered in the root folder
and `False` when it is not. Permission and other native errors still raise
exceptions.

Task names are validated before the native backend is called. Names violating the
[root-folder name policy](support.md#input-validation) raise `TaskNameError`.

## Errors

`TaskNameError` is raised for invalid task names. Native access denials raise
`TaskPermissionError` (a `PermissionError` subclass); other native Windows
failures raise `TaskSchedulerError` (a `RuntimeError` subclass). Both expose an
unsigned `hresult` and an `operation` string. These classes are public exports
from `wintask`. See [errors and threading](support.md#errors-com-and-threads).

## Trigger models

### `DailyTrigger`

```python
DailyTrigger(at=time(9, 30), interval=1)
```

`interval` must be an integer from `1` through `365`; booleans are rejected.

### `WeeklyTrigger`

```python
WeeklyTrigger(
    at=time(9, 30),
    days=(Weekday.MONDAY, Weekday.FRIDAY),
)
```

At least one unique `Weekday` is required.

### `MonthlyTrigger`

```python
MonthlyTrigger(
    at=time(9, 30),
    day=15,
    months=(Month.JANUARY, Month.JUNE),
)
```

The day must be an integer between `1` and `31` (excluding booleans), and months
must be unique. A day absent from a selected month does not mean its last day.
See the [scheduling contract](support.md#scheduling-behavior).

## XML builders

The lower-level `build_daily_xml`, `build_weekly_xml`, and `build_monthly_xml`
functions return XML compatible with the Windows Task Scheduler namespace.
They are useful for inspection and testing without registering a task.
