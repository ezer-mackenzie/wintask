# Changelog

All notable changes to `wintask` are documented in this file.

## [Unreleased]

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
