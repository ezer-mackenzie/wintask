# Support and scheduling contract

This contract describes the candidate for 0.10.0. Stable 1.0 publication still
requires the remote checks and release rehearsal listed in the roadmap.

## Supported configurations

- Native Task Scheduler operations target Windows 11 and Windows Server 2022+
  on x64 with standard, GIL-enabled CPython 3.9 through 3.14. The Windows CI
  matrix installs and tests a wheel for every one of those Python versions.
  A successful matrix run is required before claiming a released version works
  on those combinations; this change has only been exercised locally so far.
- Windows x86 and ARM64 builds have additional CPython 3.13 test jobs. They are
  experimental until their runners and native integration results are verified.
- Linux/macOS support XML generation and validation for development. Native
  operations raise `RuntimeError` rather than returning misleading results.
  Portable tests cover CPython 3.9 and 3.14. Additional architecture wheels are
  best-effort builds, not a native scheduling support promise.
- PyPy, free-threaded CPython, Python 3.15+, Windows 10 and older Windows versions
  are not in the supported matrix. Package metadata constrains Python to
  `>=3.9,<3.15`; adding an interpreter requires testing and updating that bound.
- Building from source requires Rust 1.85+ and maturin 1.15+. CI checks the Rust
  minimum separately. Installing a compatible wheel does not require Rust.

The default environment uses the current user's interactive token. An
interactive session must be available for the task to run. Services, alternate
credentials, remote machines, elevated principals and task folders are outside
the public API. Creating a task does not grant its action extra permissions.

## Input validation

Names identify a single task in the root folder. The library deliberately uses
a conservative policy: 1-200 UTF-16 code units, no surrounding whitespace,
control characters, surrogates, reserved path characters (`<>:"/\\|?*`), dot
paths or trailing dots. This is a library limit, not a claim about the maximum
accepted by every Windows installation. Invalid names raise `TaskNameError`
before invoking COM and are never silently trimmed.

Daily intervals are integers from 1 through 365; monthly days are integers from
1 through 31. Booleans and fractional numbers are rejected. Weekday/month
collections must be non-empty tuples of the corresponding enums without
duplicates. Times must be naive `datetime.time` values with whole seconds and
`fold=0`; timezone-aware values, fractional seconds and explicit DST-fold
selection are rejected rather than silently changed.

`arguments` must be a sequence of strings, not one string or bytes. XML-illegal
characters (including NUL and lone surrogates) are rejected. Each argument is
quoted using Windows command-line rules; it is not interpreted through a shell.
`enabled` and `wake_to_run` must be booleans. Descriptions must be non-empty
strings containing valid XML text. Script and working-directory paths must
exist; the default directory is the resolved script parent.

## Scheduling behavior

The start date is the local date at registration; the time is local wall-clock
time without a UTC offset. Windows, its timezone configuration and timezone
updates determine DST transitions. wintask does not promise a particular
resolution of nonexistent/repeated wall-clock times or an exactly-once result
across timezone changes. Use Windows' task history to inspect actual execution.

Days 29-31 are literal days of selected months; they do not mean the last day of
the month. A nonexistent date does not become a different date. wintask delegates
calendar matching to Windows and does not add a compensating run.

`StartWhenAvailable` is explicitly false: missed schedules are not opted into
catch-up execution. `wake_to_run` requests waking the machine, subject to Windows
and hardware policies; it does not guarantee execution while powered off.
Windows may impose additional service, battery, idle or account restrictions.
Tasks use `MultipleInstancesPolicy=IgnoreNew`, so a running instance is not
replaced by an overlapping request. Other settings retain Windows defaults.

`create_*` registers or updates by name. `run()` requests an immediate start; it
does not wait for completion or return the script's exit status. `delete()` removes
the registration and does not provide a stop-running-process guarantee. `exists()`
is a point-in-time query, not an atomic check-and-create/delete operation. Other
processes can change a task between calls.

## Errors, COM and threads

- `TaskNameError` inherits from `ValueError`.
- Invalid types raise `TypeError`; invalid values raise `ValueError`. Missing
  scripts/directories raise `FileNotFoundError`/`NotADirectoryError`.
- `TaskPermissionError` inherits from `PermissionError` for native access denial.
- Other native failures raise `TaskSchedulerError`, a `RuntimeError` subclass.
- Both native error classes expose an unsigned integer `hresult` and the native
  `operation` that failed, including connection and COM-initialization failures.
- Only file/path-not-found returned by the task lookup becomes `False` in
  `exists()`. Connection, folder, service and permission failures propagate.

Calls use the caller's COM apartment. A pre-existing STA is borrowed; successful
initialization on a fresh or MTA thread is balanced by one uninitialization.
COM objects are created and released on the same thread, before releasing the
owned COM count. The bridge detaches from Python while calling COM, allowing
other Python threads to progress, but each API call remains synchronous. GUI
and async applications should call it on a worker thread (for example
`asyncio.to_thread`), rather than blocking their event loop.

Tests cover actual STA/MTA ownership on success/error, concurrent lookups,
execution with arguments/interpreter/directory, updates and missing tasks.
Access-denied and unavailable-service HRESULT mappings are tested with synthetic
native errors; the suite does not stop the system service or modify unrelated
users' task ACLs to force failures.

## Release procedure

1. Keep source version, Cargo.lock, dated changelog and tag aligned. Commit all
   fixes before tagging; never move or overwrite a published tag.
2. Require green CI, including the Windows Python matrix, Rust minimum,
   portable tests, documentation, distribution metadata and a wheel rebuilt
   from the source distribution. Review the exact commit being released.
3. Use the manual `Release` workflow with `publish=false` for a non-publishing
   rehearsal. The same build and test gates run; the PyPI job is skipped.
4. Exercise Trusted Publishing on a correctly versioned release candidate
   before 1.0. Publishing a GitHub release/prerelease enables publication to
   PyPI. Its prerelease flag must agree with the version (such as
   `1.0.0-rc.1` in Cargo and `v1.0.0-rc.1` as the tag).
5. Reinstall the published artifacts in a clean environment and record the
   workflow URLs in the roadmap. Do not claim the stable gate is complete until
   these external checks have actually run.

References: [Task registration](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskfolder-registertask),
[DaysInterval](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-daysinterval-dailyscheduletype-element),
[StartWhenAvailable](https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-startwhenavailable),
[CoInitializeEx](https://learn.microsoft.com/en-us/windows/win32/api/combaseapi/nf-combaseapi-coinitializeex).
