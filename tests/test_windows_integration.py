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

    def test_run_and_update_preserve_action_configuration(self):
        import json
        import subprocess
        import time as clock
        from datetime import datetime, timedelta
        from xml.etree import ElementTree as ET
        from wintask.builder import NAMESPACE

        scheduler = TaskScheduler()
        name = 'wintask-test-' + uuid4().hex
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / 'work with spaces'
            work.mkdir()
            script = root / 'job with spaces.py'
            marker = root / 'result.json'
            script.write_text(
                'import json, os, sys\n'
                'from pathlib import Path\n'
                'Path(sys.argv[1]).write_text(json.dumps({"args": sys.argv[2:], '
                '"cwd": os.getcwd(), "executable": sys.executable}), encoding="utf-8")\n',
                encoding='utf-8',
            )
            arguments = ('hello world', 'a"b', 'trailing\\', '', 'caf\u00e9', '&<test>', 'line1\r\nline2', '\t', '\U0001f680')
            at = (datetime.now() + timedelta(hours=12)).time().replace(microsecond=0)
            registered = False
            try:
                scheduler.create_daily(name, script, at, enabled=False, description='original')
                registered = True
                scheduler.create_daily(
                    name, script, at, interval=2, arguments=(str(marker), *arguments),
                    working_directory=work, enabled=True, description='updated',
                )
                command = (
                    '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); '
                    '$service = New-Object -ComObject Schedule.Service; $service.Connect(); '
                    '$task = $service.GetFolder("\\").GetTask($env:WINTASK_TEST_NAME); '
                    '@{xml=$task.Xml; enabled=$task.Enabled} | ConvertTo-Json -Compress'
                )
                xml = subprocess.check_output(
                    ['powershell', '-NoProfile', '-NonInteractive', '-Command', command],
                    env={**os.environ, 'WINTASK_TEST_NAME': name}, encoding='utf-8', timeout=20,
                )
                state = json.loads(xml.strip('\ufeff\r\n '))
                task = ET.fromstring(state['xml'])
                ns = {'t': NAMESPACE}
                self.assertEqual(task.find('t:RegistrationInfo/t:Description', ns).text, 'updated')
                self.assertEqual(task.find('t:Triggers/t:CalendarTrigger/t:ScheduleByDay/t:DaysInterval', ns).text, '2')
                self.assertTrue(state['enabled'])
                scheduler.run(name)
                deadline = clock.monotonic() + 30
                while not marker.exists() and clock.monotonic() < deadline:
                    clock.sleep(0.1)
                self.assertTrue(marker.exists(), 'Task did not write its marker within 30 seconds')
                # The writer may still be flushing immediately after file creation.
                while True:
                    try:
                        result = json.loads(marker.read_text(encoding='utf-8'))
                        break
                    except (json.JSONDecodeError, PermissionError):
                        if clock.monotonic() >= deadline:
                            raise
                        clock.sleep(0.1)
                self.assertEqual(result['args'], list(arguments))
                self.assertTrue(Path(result['cwd']).samefile(work), f"{result['cwd']} is not the same directory as {work}")
                self.assertTrue(Path(result['executable']).samefile(sys.executable), f"{result['executable']} is not the same file as {sys.executable}")
            finally:
                if registered:
                    # Stop any running instance before removing its temporary files.
                    stop = (
                        '$ErrorActionPreference = "Stop"; '
                        '$s = New-Object -ComObject Schedule.Service; $s.Connect(); '
                        '$s.GetFolder("\\").GetTask($env:WINTASK_TEST_NAME).Stop(0)'
                    )
                    try:
                        subprocess.run(
                            ['powershell', '-NoProfile', '-NonInteractive', '-Command', stop],
                            env={**os.environ, 'WINTASK_TEST_NAME': name},
                            check=True, capture_output=True, timeout=20,
                        )
                    finally:
                        scheduler.delete(name)
        self.assertFalse(scheduler.exists(name))

    def test_missing_run_and_delete_keep_hresult(self):
        from wintask import TaskSchedulerError
        scheduler = TaskScheduler()
        name = 'wintask-test-' + uuid4().hex
        for operation in (scheduler.run, scheduler.delete):
            with self.subTest(operation=operation.__name__), self.assertRaises(TaskSchedulerError) as caught:
                operation(name)
            self.assertIn(caught.exception.hresult, (0x80070002, 0x80070003))
            self.assertIn(caught.exception.operation, ('GetTask', 'DeleteTask'))

    def test_sta_and_mta_ownership_survives_success_and_error(self):
        import subprocess
        from textwrap import dedent
        code = dedent('''
            import ctypes
            import sys
            from uuid import uuid4
            from wintask import TaskScheduler, TaskSchedulerError
            ole = ctypes.WinDLL('ole32')
            mode = int(sys.argv[1])
            assert ole.CoInitializeEx(None, mode) == 0
            def apartment():
                kind, qualifier = ctypes.c_int(), ctypes.c_int()
                result = ole.CoGetApartmentType(ctypes.byref(kind), ctypes.byref(qualifier))
                return result, kind.value
            original = apartment()
            try:
                scheduler = TaskScheduler()
                for _ in range(3):
                    name = 'wintask-test-' + uuid4().hex
                    assert scheduler.exists(name) is False
                    try:
                        scheduler.run(name)
                    except TaskSchedulerError:
                        pass
                    else:
                        raise AssertionError('missing task unexpectedly ran')
                    assert apartment() == original
            finally:
                ole.CoUninitialize()
            assert apartment()[0] & 0xffffffff == 0x800401f0
        ''')
        for mode in (0, 2):
            with self.subTest(mode=mode):
                subprocess.run([sys.executable, '-c', code, str(mode)], check=True, timeout=30)

    def test_concurrent_calls_have_independent_com_lifetimes(self):
        from concurrent.futures import ThreadPoolExecutor
        scheduler = TaskScheduler()
        names = ['wintask-test-' + uuid4().hex for _ in range(24)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(scheduler.exists, names)), [False] * len(names))
