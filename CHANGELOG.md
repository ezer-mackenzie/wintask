# Changelog

All notable changes to `wintask` are documented in this file.

## [Unreleased]

## [1.0.0] - 2026-09-20

### Fixed

- Validate integer ranges, task names, local times, XML text, arguments and boolean flags before COM.
- Respect existing STA/MTA COM initialization and release the GIL during native calls.
- Preserve native HRESULT and operation in consistent public permission/runtime exceptions.


### Changed

- Validate release tags, package versions, changelog, tests and docs before publishing.
- Build release artifacts from the validated commit and test installed Windows wheels.
- Serialize publication of the same version and check PyPI for existing files on retries.
- Preserve manual dispatch and automatic publication when a GitHub release is published.

### Added

- Native execution, update, apartment ownership, concurrency and validation regression tests.
- Explicit scheduling/support contracts, complete distribution metadata and wheel/sdist checks.
- CPython 3.9-3.14 Windows x64 test matrix and a non-publishing release rehearsal option.
- Pre-1.0 audit with reproduced failures, support gaps and acceptance criteria.

## [0.9.0] - 2026-09-19

### Added

- Added `TaskScheduler.exists()` for idempotent task management.
- Added the native `task_exists` operation without exposing the private backend
	as part of the public Python API.

### Fixed

- Treat native file/path-not-found errors as absent tasks while preserving other errors.
- Use the valid `ScheduleByMonth` XML element for monthly tasks.
- Omit the byte-encoding declaration from Unicode task XML passed to COM.
- Ensure existence checks run in the test suite and add opt-in Windows lifecycle coverage.

## [0.8.0] - 2026-09-19

### Added

- Added `TaskNameError` and centralized validation for task names.
- Task names now reject empty values, control characters, and root-folder
	separators before calling the native backend.

## [0.7.0] - 2026-09-18

### Added

- Added a MkDocs documentation site with getting-started, API, and architecture
	guides.
- Added Read the Docs configuration and documentation build dependencies.

## [0.6.0] - 2026-09-18

### Added

- Added optional task descriptions for daily, weekly, and monthly schedules.
- Renamed the validation workflow to `ci.yml`.

## [0.5.0] - 2026-09-17

### Added

- Added `working_directory` support for daily, weekly, and monthly tasks.
- Added an `enabled` option to register tasks in an enabled or disabled state.
- Added validation that the configured working directory exists.

## [0.4.0] - 2026-09-17

### Added

- Added an `arguments` parameter to daily, weekly, and monthly scheduling
	methods.
- Added Windows-compatible quoting for script paths and command-line
	arguments in generated Task Scheduler XML.

## [0.3.0] - 2026-09-17

### Added

- Added `MonthlyTrigger` and `TaskScheduler.create_monthly()` for scheduling
	Python scripts on a selected day of one or more months.
- Added monthly Task Scheduler XML serialization and validation.
- Added Dependabot coverage for Python packages managed through PyPI metadata
	and `uv.lock`.

## [0.2.0] - 2026-09-17

### Added

- Added `WeeklyTrigger` and `TaskScheduler.create_weekly()` for scheduling
	Python scripts on selected weekdays.
- Added XML serialization and validation for weekly schedules.

## [0.1.1] - 2026-09-17

### Fixed

- Forwarded `DailyTrigger.interval` through `TaskScheduler.create_daily()`.

### Added

- Documented the project's purpose, architecture, public API, setup, and
	development workflow.
- Added the initial Python API for daily task creation, execution, and
	deletion.
- Added the Rust/PyO3 bridge to Windows Task Scheduler COM.

## [0.1.0]

Initial project scaffold.
