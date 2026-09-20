import pickle
import tempfile
import unittest
from datetime import time, timezone
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from wintask import (
    DailyTrigger, Month, MonthlyTrigger, TaskNameError, TaskPermissionError,
    TaskScheduler, TaskSchedulerError, Weekday, WeeklyTrigger,
)
from wintask.builder import NAMESPACE, build_daily_xml, build_monthly_xml, build_weekly_xml
from wintask.validation import validate_task_name


class InputValidationTests(unittest.TestCase):
    def test_integer_types_and_boundaries(self):
        for value in (True, False, 1.5, '1', None):
            with self.subTest(value=value), self.assertRaises(TypeError):
                DailyTrigger(time(9), interval=value)
            with self.subTest(value=value), self.assertRaises(TypeError):
                MonthlyTrigger(time(9), day=value, months=(Month.JANUARY,))
        for value in (0, -1, 366):
            with self.subTest(value=value), self.assertRaises(ValueError):
                DailyTrigger(time(9), interval=value)
        for value in (0, -1, 32):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MonthlyTrigger(time(9), day=value, months=(Month.JANUARY,))
        for value in (1, 365):
            self.assertEqual(DailyTrigger(time(9), value).interval, value)
        for value in (1, 31):
            self.assertEqual(MonthlyTrigger(time(9), value, (Month.FEBRUARY,)).day, value)

    def test_time_contract_for_all_triggers(self):
        constructors = (
            lambda at: DailyTrigger(at),
            lambda at: WeeklyTrigger(at, (Weekday.MONDAY,)),
            lambda at: MonthlyTrigger(at, 1, (Month.JANUARY,)),
        )
        for constructor in constructors:
            for value, exception in ((None, TypeError), ('09:00', TypeError),
                                     (time(9, tzinfo=timezone.utc), ValueError),
                                     (time(9, microsecond=1), ValueError),
                                     (time(1, fold=1), ValueError)):
                with self.subTest(value=value), self.assertRaises(exception):
                    constructor(value)
            self.assertEqual(constructor(time(23, 59, 59)).at, time(23, 59, 59))

    def test_enum_collections_are_typed_immutable_and_unique(self):
        for constructor, enum in ((lambda values: WeeklyTrigger(time(9), values), Weekday.MONDAY),
                                  (lambda values: MonthlyTrigger(time(9), 1, values), Month.JANUARY)):
            for values, exception in (((), ValueError), ((enum, enum), ValueError),
                                      ([enum], TypeError), (('invalid',), TypeError),
                                      (([],), TypeError)):
                with self.subTest(values=values), self.assertRaises(exception):
                    constructor(values)

    def test_invalid_names_are_rejected_by_every_scheduler_operation(self):
        scheduler = TaskScheduler()
        operations = (
            scheduler.exists, scheduler.run, scheduler.delete,
            lambda name: scheduler.create_daily(name, 'missing.py', time(9)),
            lambda name: scheduler.create_weekly(name, 'missing.py', time(9), (Weekday.MONDAY,)),
            lambda name: scheduler.create_monthly(name, 'missing.py', time(9), 1, (Month.JANUARY,)),
        )
        with patch('wintask.scheduler._wintask_backend') as backend:
            for name in (None, 1, '', ' ', ' leading', 'trailing ', '.', '..', 'dot.',
                         'folder/task', 'folder\\task', 'bad:name', 'bad*name', 'bad?name',
                         'bad\x00name', 'bad\x7fname', 'bad\x85name', 'bad\ud800name',
                         'x' * 201, '\U0001f680' * 101):
                for operation in operations:
                    with self.subTest(name=repr(name), operation=operation), self.assertRaises(TaskNameError):
                        operation(name)
            self.assertEqual(backend.mock_calls, [])
        for name in ('daily job', 'caf\u00e9', 'x' * 200, '\U0001f680' * 100):
            self.assertEqual(validate_task_name(name), name)

    def test_builder_options_rejected_before_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'job.py'
            script.write_text('pass', encoding='utf-8')
            for options, exception in (
                ({'arguments': 'ab'}, TypeError), ({'arguments': b'ab'}, TypeError),
                ({'arguments': [1]}, TypeError), ({'arguments': [None]}, TypeError),
                ({'arguments': ['a\x00b']}, ValueError), ({'arguments': ['a\ud800b']}, ValueError),
                ({'enabled': 1}, TypeError), ({'wake_to_run': 'false'}, TypeError),
                ({'description': 1}, TypeError), ({'description': '\x01'}, ValueError),
            ):
                with self.subTest(options=options), patch('wintask.scheduler._wintask_backend.register_xml') as register:
                    with self.assertRaises(exception):
                        TaskScheduler().create_daily('valid-name', script, time(9), **options)
                    register.assert_not_called()

    def test_xml_boundaries_and_explicit_missed_schedule_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'job.py'
            script.write_text('pass', encoding='utf-8')
            for builder, trigger in (
                (build_daily_xml, DailyTrigger(time(23, 59, 59), 365)),
                (build_weekly_xml, WeeklyTrigger(time(0), (Weekday.SUNDAY,))),
                (build_monthly_xml, MonthlyTrigger(time(0), 31, (Month.FEBRUARY,))),
            ):
                xml = builder(script, trigger, description='caf\u00e9 & <test>')
                root = ET.fromstring(xml)
                self.assertFalse(xml.startswith('<?xml'))
                self.assertEqual(root.find(f'{{{NAMESPACE}}}Settings/{{{NAMESPACE}}}StartWhenAvailable').text, 'false')
                self.assertEqual(root.find(f'{{{NAMESPACE}}}RegistrationInfo/{{{NAMESPACE}}}Description').text, 'caf\u00e9 & <test>')
            with self.assertRaises(TypeError):
                build_daily_xml(script, WeeklyTrigger(time(9), (Weekday.MONDAY,)))

    def test_public_native_errors_preserve_builtin_compatibility_and_pickle(self):
        for cls, base, code in ((TaskSchedulerError, RuntimeError, 0x800706BA),
                                (TaskPermissionError, PermissionError, 0x80070005)):
            error = cls('native failure', code, 'Connect')
            self.assertIsInstance(error, base)
            recovered = pickle.loads(pickle.dumps(error))
            self.assertEqual((str(recovered), recovered.hresult, recovered.operation),
                             ('native failure', code, 'Connect'))
