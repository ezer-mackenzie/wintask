import tempfile
import unittest
from datetime import time
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from wintask.builder import (
    NAMESPACE,
    build_daily_xml,
    build_monthly_xml,
    build_weekly_xml,
)
from wintask.scheduler import TaskScheduler
from wintask.triggers import DailyTrigger, Month, MonthlyTrigger, Weekday, WeeklyTrigger
from wintask.errors import TaskNameError


class BuilderTests(unittest.TestCase):
    def test_daily_interval_is_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            xml = build_daily_xml(script, DailyTrigger(time(9, 30), interval=3))
            root = ElementTree.fromstring(xml)
            days_interval = root.find(
                f"{{{NAMESPACE}}}Triggers/{{{NAMESPACE}}}CalendarTrigger/"
                f"{{{NAMESPACE}}}ScheduleByDay/{{{NAMESPACE}}}DaysInterval"
            )

            self.assertIsNotNone(days_interval)
            assert days_interval is not None
            self.assertEqual(days_interval.text, "3")

    def test_script_arguments_are_quoted_in_xml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            xml = build_daily_xml(
                script,
                DailyTrigger(time(9, 30)),
                arguments=("hello world", "--count", "2"),
            )
            root = ElementTree.fromstring(xml)
            arguments = root.find(
                f"{{{NAMESPACE}}}Actions/{{{NAMESPACE}}}Exec/{{{NAMESPACE}}}Arguments"
            )

            self.assertIsNotNone(arguments)
            assert arguments is not None
            self.assertIn('"hello world"', arguments.text or "")
            self.assertIn("--count", arguments.text or "")

    def test_working_directory_and_enabled_state_are_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script = root / "job.py"
            working_directory = root / "work"
            script.write_text("print('ok')", encoding="utf-8")
            working_directory.mkdir()

            xml = build_daily_xml(
                script,
                DailyTrigger(time(9, 30)),
                working_directory=working_directory,
                enabled=False,
            )
            parsed = ElementTree.fromstring(xml)
            settings = parsed.find(f"{{{NAMESPACE}}}Settings")
            working = parsed.find(
                f"{{{NAMESPACE}}}Actions/{{{NAMESPACE}}}Exec/{{{NAMESPACE}}}WorkingDirectory"
            )

            self.assertIsNotNone(settings)
            self.assertIsNotNone(working)
            assert settings is not None
            assert working is not None
            enabled = settings.find(f"{{{NAMESPACE}}}Enabled")
            self.assertIsNotNone(enabled)
            assert enabled is not None
            self.assertEqual(enabled.text, "false")
            self.assertEqual(working.text, str(working_directory.resolve()))

    def test_task_description_is_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            xml = build_daily_xml(
                script,
                DailyTrigger(time(9, 30)),
                description="Runs the daily data refresh",
            )
            root = ElementTree.fromstring(xml)
            description = root.find(
                f"{{{NAMESPACE}}}RegistrationInfo/{{{NAMESPACE}}}Description"
            )

            self.assertIsNotNone(description)
            assert description is not None
            self.assertEqual(description.text, "Runs the daily data refresh")

    def test_empty_task_description_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            with self.assertRaises(ValueError):
                build_daily_xml(
                    script,
                    DailyTrigger(time(9, 30)),
                    description="   ",
                )

    def test_missing_working_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            with self.assertRaises(NotADirectoryError):
                build_daily_xml(
                    script,
                    DailyTrigger(time(9, 30)),
                    working_directory=script / "missing",
                )

    def test_missing_script_is_rejected(self) -> None:
        with self.assertRaises(FileNotFoundError):
            build_daily_xml(
                "does-not-exist.py",
                DailyTrigger(time(9, 30)),
            )

    def test_scheduler_forwards_interval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            with patch("wintask.scheduler._wintask_backend.register_xml") as register:
                TaskScheduler().create_daily(
                    "test-task",
                    script,
                    time(9, 30),
                    interval=3,
                )

            self.assertIn("<DaysInterval>3</DaysInterval>", register.call_args.args[1])

    def test_scheduler_rejects_invalid_task_names(self) -> None:
        with self.assertRaises(TaskNameError):
            TaskScheduler().delete("folder\\task")

        with self.assertRaises(TaskNameError):
            TaskScheduler().run("   ")

    def test_scheduler_checks_task_existence(self) -> None:
        for expected in (True, False):
            with self.subTest(expected=expected):
                with patch(
                    "wintask.scheduler._wintask_backend.task_exists",
                    return_value=expected,
                ) as exists:
                    self.assertIs(TaskScheduler().exists("test-task"), expected)
                    exists.assert_called_once_with("test-task")

    def test_scheduler_exists_rejects_invalid_names_before_native_call(self) -> None:
        with patch("wintask.scheduler._wintask_backend.task_exists") as exists:
            for name in ("", "   ", "folder\\task", "task\n"):
                with self.subTest(name=name), self.assertRaises(TaskNameError):
                    TaskScheduler().exists(name)
            exists.assert_not_called()

    def test_scheduler_exists_preserves_native_errors(self) -> None:
        for error in (PermissionError("denied"), RuntimeError("COM failure")):
            with self.subTest(error=error):
                with patch(
                    "wintask.scheduler._wintask_backend.task_exists", side_effect=error
                ):
                    with self.assertRaises(type(error)) as caught:
                        TaskScheduler().exists("test-task")
                    self.assertIs(caught.exception, error)

    def test_weekly_days_are_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            xml = build_weekly_xml(
                script,
                WeeklyTrigger(
                    time(9, 30),
                    days=(Weekday.MONDAY, Weekday.FRIDAY),
                ),
            )
            root = ElementTree.fromstring(xml)
            days = root.findall(
                f"{{{NAMESPACE}}}Triggers/{{{NAMESPACE}}}CalendarTrigger/"
                f"{{{NAMESPACE}}}ScheduleByWeek/{{{NAMESPACE}}}DaysOfWeek/*"
            )

            self.assertEqual([day.tag.rsplit("}", 1)[-1] for day in days], ["Monday", "Friday"])

    def test_weekly_trigger_requires_days(self) -> None:
        with self.assertRaises(ValueError):
            WeeklyTrigger(time(9, 30), days=())

    def test_monthly_schedule_is_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "job.py"
            script.write_text("print('ok')", encoding="utf-8")

            xml = build_monthly_xml(
                script,
                MonthlyTrigger(
                    time(9, 30),
                    day=15,
                    months=(Month.JANUARY, Month.JUNE),
                ),
            )
            root = ElementTree.fromstring(xml)
            schedule = root.find(
                f"{{{NAMESPACE}}}Triggers/{{{NAMESPACE}}}CalendarTrigger/"
                f"{{{NAMESPACE}}}ScheduleByMonth"
            )

            self.assertIsNotNone(schedule)
            assert schedule is not None
            day = schedule.find(f"{{{NAMESPACE}}}DaysOfMonth/{{{NAMESPACE}}}Day")
            self.assertIsNotNone(day)
            assert day is not None
            self.assertEqual(day.text, "15")
            self.assertIsNotNone(schedule.find(f"{{{NAMESPACE}}}Months/{{{NAMESPACE}}}January"))
            self.assertIsNotNone(schedule.find(f"{{{NAMESPACE}}}Months/{{{NAMESPACE}}}June"))

    def test_monthly_trigger_rejects_invalid_days(self) -> None:
        with self.assertRaises(ValueError):
            MonthlyTrigger(time(9, 30), day=32, months=(Month.JANUARY,))


if __name__ == "__main__":
    unittest.main()
