# Architecture

```text
Python API
    |
    v
Trigger models and XML builders
    |
    v
PyO3 extension: _wintask_backend
    |
    v
Rust COM bridge
    |
    v
Windows Task Scheduler
```

## Python layer

Python owns the public API, validation, path resolution, command-line quoting,
and XML serialization. It uses `sys.executable` so tasks run with the Python
interpreter from the active environment.

## Rust layer

Rust owns COM initialization through RAII, connects to `Schedule.Service`, and
exposes only `register_xml`, `run_task`, and `delete_task` to Python. Windows
errors are translated into Python exceptions.

The `_wintask_backend` name is intentionally private. Applications should use
the stable `wintask` Python API instead of importing the extension directly.