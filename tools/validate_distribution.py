"""Check distribution contents and metadata without importing the package."""
from __future__ import annotations

import argparse
import tarfile
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile


def check_metadata(data: bytes | bytearray) -> str:
    metadata = BytesParser().parsebytes(data)

    required_fields = (
        'Name',
        'Version',
        'Summary',
        'Requires-Python',
        'License-Expression',
        'Description-Content-Type',
    )
    for field in required_fields:
        if not metadata.get(field):
            raise ValueError(f'Missing metadata: {field}')

    if metadata['Name'] != 'wintask' or metadata['License-Expression'] != 'Apache-2.0':
        raise ValueError('Incorrect project name or license')

    project_urls = metadata.get_all('Project-URL')
    if not project_urls:
        raise ValueError('Missing Project-URL entries')

    long_description = metadata.get_payload()
    if not isinstance(long_description, str) or not long_description.strip():
        raise ValueError('Missing or empty long description')

    return metadata['Version']


def check(path: Path) -> str:
    if path.suffix == '.whl':
        with ZipFile(path) as archive:
            names = archive.namelist()
            version = check_metadata(archive.read(next(name for name in names if name.endswith('/METADATA'))))
            for required in ('wintask/py.typed', 'wintask/_wintask_backend.pyi', 'wintask/errors.py'):
                if required not in names:
                    raise ValueError(f'Missing wheel file: {required}')

            if not any(name.endswith(('.pyd', '.so')) for name in names):
                raise ValueError('Missing native extension')

            if not any(name.endswith('/LICENSE.md') for name in names):
                raise ValueError('Missing license file')
    else:
        with tarfile.open(path) as archive:
            names = archive.getnames()
            metadata = archive.extractfile(next(name for name in names if name.endswith('/PKG-INFO')))

            if not metadata:
                raise ValueError('Missing PKG-INFO file')

            version = check_metadata(metadata.read())
            for required in ('Cargo.toml', 'Cargo.lock', 'pyproject.toml', 'src/lib.rs',
                             'python/wintask/scheduler.py', 'tests/test_windows_integration.py',
                             'tools/validate_release.py', 'LICENSE.md'):

                if not any(name.endswith('/' + required) for name in names):
                    raise ValueError(f'Missing source file: {required}')

    return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    distributions = sorted(args.directory.glob('*.whl')) + sorted(args.directory.glob('*.tar.gz'))

    if not distributions:
        raise SystemExit('No distributions found')

    versions: set[str] = set()
    for distribution in distributions:
        versions.add(check(distribution))
        print(f'Validated {distribution.name}')

    if len(versions) != 1:
        raise SystemExit('Distribution versions disagree')
