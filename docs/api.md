# API reference

## `TaskScheduler`

`TaskScheduler` exposes `create_daily`, `create_weekly`, and
`create_monthly`. Each method accepts a task name, Python script path, local
start time, optional trigger-specific values, script `arguments`,
`working_directory`, `enabled`, and `description`.

Use `run(name)` to start a registered task immediately and `delete(name)` to
remove it from the root Task Scheduler folder.

Task names are validated before the native backend is called. Empty names,
control characters, and backslashes raise `TaskNameError` because this release
targets the root Task Scheduler folder.

## Errors

`TaskNameError` is raised for invalid task names. Native Windows failures are
reported as Python runtime or permission errors by the Rust extension.

## Trigger models

### `DailyTrigger`

```python
DailyTrigger(at=time(9, 30), interval=1)
```

`interval` must be at least `1`.

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

The day must be between `1` and `31`, and months must be unique.

## XML builders

The lower-level `build_daily_xml`, `build_weekly_xml`, and `build_monthly_xml`
functions return XML compatible with the Windows Task Scheduler namespace.
They are useful for inspection and testing without registering a task.