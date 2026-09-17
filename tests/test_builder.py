import tempfile
import unittest
from datetime import time
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from wintask.builder import NAMESPACE, build_daily_xml
from wintask.scheduler import TaskScheduler
from wintask.triggers import DailyTrigger


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
            self.assertEqual(days_interval.text, "3")

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


if __name__ == "__main__":
    unittest.main()