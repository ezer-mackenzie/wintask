"""Validate a release tag against the checked-out source (Python 3.11+)."""
from __future__ import annotations

import os
import re
from pathlib import Path


def validate(root: Path, tag: str, prerelease: bool | None = None) -> str:
    import tomllib

    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-(?:alpha|beta|rc)\.[1-9][0-9]*)?", tag):
        raise ValueError(f"Invalid release tag: {tag!r}; use vX.Y.Z or vX.Y.Z-rc.N/alpha.N/beta.N")
    cargo = tomllib.loads((root / 'Cargo.toml').read_text(encoding='utf-8'))
    version = cargo['package']['version']
    if tag != f'v{version}':
        raise ValueError(f'Tag {tag!r} does not match Cargo version {version!r}')
    lock = tomllib.loads((root / 'Cargo.lock').read_text(encoding='utf-8'))
    packages = [p for p in lock['package'] if p['name'] == 'wintask' and 'source' not in p]
    if len(packages) != 1 or packages[0]['version'] != version:
        raise ValueError('Cargo.lock version does not match Cargo.toml')
    changelog = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    if not re.search(r'^## \[' + re.escape(version) + r'\] - \d{4}-\d{2}-\d{2}$', changelog, re.MULTILINE):
        raise ValueError('Missing dated changelog entry for this version')
    if not (root / 'tests/test_windows_integration.py').is_file():
        raise ValueError('Release must include Windows integration tests')
    if prerelease is not None and prerelease != ('-' in version):
        raise ValueError('GitHub prerelease flag must match the package version')
    return version


if __name__ == '__main__':
    flag = os.environ.get('RELEASE_PRERELEASE', '')
    try:
        print(validate(Path('.'), os.environ['RELEASE_TAG'], None if not flag else flag == 'true'))
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(str(error)) from error
