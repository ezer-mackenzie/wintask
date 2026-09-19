"""Opt-in Windows integration checks: WINTASK_INTEGRATION=1."""

import os
import sys
import tempfile
import unittest
from datetime import time
from pathlib import Path
from uuid import uuid4

from wintask import Month, TaskScheduler, Weekday


@unittest.skipUnless(
    sys.platform == "win32" and os.environ.get("WINTASK_INTEGRATION") == "1",
    "requires Windows Task Scheduler and WINTASK_INTEGRATION=1",
)
class TaskExistenceIntegrationTests(unittest.TestCase):
    def test_exists_before_registration_after_registration_and_after_deletion(self):
        scheduler = TaskScheduler()
        schedules = (
            (scheduler.create_daily, {}),
            (scheduler.create_weekly, {"days": (Weekday.MONDAY,)}),
            (scheduler.create_monthly, {"day": 1, "months": (Month.JANUARY,)}),
        )
        for create, options in schedules:
            with self.subTest(schedule=create.__name__):
                name = "wintask-test-" + uuid4().hex
                self.assertFalse(scheduler.exists(name))
                with tempfile.TemporaryDirectory() as directory:
                    script = Path(directory) / "job.py"
                    script.write_text("pass\n", encoding="utf-8")
                    registered = False
                    try:
                        create(name, script, time(0), enabled=False, **options)
                        registered = True
                        self.assertTrue(scheduler.exists(name))
                    finally:
                        if registered:
                            scheduler.delete(name)
                self.assertFalse(scheduler.exists(name))
