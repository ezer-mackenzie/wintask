import sys
import tempfile
import unittest
from pathlib import Path

from tools.validate_release import validate


@unittest.skipIf(sys.version_info < (3, 11), 'release tooling requires Python 3.11+')
class ReleaseValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'tests').mkdir()
        (self.root / 'tests/test_windows_integration.py').write_text('# tests', encoding='utf-8')
        self.write_version('0.10.0')

    def write_version(self, version):
        (self.root / 'Cargo.toml').write_text(f'[package]\nname="wintask"\nversion="{version}"\n', encoding='utf-8')
        (self.root / 'Cargo.lock').write_text(f'[[package]]\nname="wintask"\nversion="{version}"\n', encoding='utf-8')
        (self.root / 'CHANGELOG.md').write_text(f'## [{version}] - 2026-09-19\n', encoding='utf-8')

    def test_stable_and_prerelease_versions(self):
        self.assertEqual(validate(self.root, 'v0.10.0', False), '0.10.0')
        for suffix in ('rc.1', 'alpha.2', 'beta.3'):
            version = '1.0.0-' + suffix
            self.write_version(version)
            self.assertEqual(validate(self.root, 'v' + version, True), version)

    def test_invalid_and_mismatched_tags_are_rejected(self):
        for tag in ('main', 'v99.0.0', 'v0.10.0; echo unsafe', 'v01.0.0', 'v1.0.0-rc.0', 'v1.0.0+build'):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                validate(self.root, tag)

    def test_lock_changelog_and_integration_tests_are_required(self):
        for filename, replacement in (('Cargo.lock', '[[package]]\nname="wintask"\nversion="99.0.0"'),
                                      ('CHANGELOG.md', '# No release entry')):
            self.write_version('0.10.0')
            (self.root / filename).write_text(replacement, encoding='utf-8')
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                validate(self.root, 'v0.10.0')
        self.write_version('0.10.0')
        (self.root / 'tests/test_windows_integration.py').unlink()
        with self.assertRaises(ValueError):
            validate(self.root, 'v0.10.0')

    def test_github_prerelease_flag_must_match_metadata(self):
        with self.assertRaises(ValueError):
            validate(self.root, 'v0.10.0', True)
        self.write_version('1.0.0-rc.1')
        with self.assertRaises(ValueError):
            validate(self.root, 'v1.0.0-rc.1', False)
