import sys
import tempfile
import unittest
from datetime import time
from pathlib import Path

from wintask import TaskScheduler


@unittest.skipIf(sys.platform == 'win32', 'non-Windows contract')
class UnsupportedPlatformTests(unittest.TestCase):
    def test_native_operations_fail_explicitly(self):
        scheduler = TaskScheduler()
        for operation in (scheduler.exists, scheduler.run, scheduler.delete):
            with self.subTest(operation=operation), self.assertRaisesRegex(RuntimeError, 'only available on Windows'):
                operation('test-task')
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'job.py'
            script.write_text('pass', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'only available on Windows'):
                scheduler.create_daily('test-task', script, time(9))
