#!/usr/bin/env python3
# Copyright 2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Verify built Cinemagoer wheels and their source distribution."""

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

EXPECTED_CATALOGS = {
    'ar', 'bg', 'de', 'en', 'es', 'fr', 'it', 'pt_BR', 'sr', 'tr',
}
SMOKE_TEST = r'''
import gettext
import importlib.metadata
import importlib.util
import sys
from pathlib import Path

import imdb
from imdb import Cinemagoer, IMDb, Movie

assert Cinemagoer is IMDb
assert Movie is not None
installed_version = importlib.metadata.version('cinemagoer')
assert tuple(map(int, imdb.VERSION.split('.'))) == \
    tuple(map(int, installed_version.split('.')))
assert importlib.util.find_spec('sqlalchemy') is None

locale_dir = Path(imdb.__file__).parent / 'locale'
italian = gettext.translation(
    'imdbpy', locale_dir, languages=['it'], fallback=False
)
assert italian.gettext('title') == 'Titolo'

database_uri = 'sqlite:///%s' % Path(sys.argv[1]).resolve()
with Cinemagoer('s3', uri=database_uri) as access:
    assert type(access._adapter).__name__ == 'SQLiteAdapter'
    results = access.search_movie('Miss Jerry')
    assert results
    assert results[0]['title'] == 'Miss Jerry'
    assert results[0].movieID == '0000009'
'''


def _relative_members(names):
    """Strip the single top-level sdist directory from archive names."""
    members = set()
    for name in names:
        parts = PurePosixPath(name).parts
        if len(parts) > 1:
            members.add(PurePosixPath(*parts[1:]).as_posix())
    return members


def verify_sdist(path, fixture_path):
    """Check that the sdist contains its tests and locale build support."""
    with tarfile.open(path, 'r:*') as archive:
        members = _relative_members(archive.getnames())
        required = {
            'MANIFEST.in',
            'build_support.py',
            'msgfmt.py',
            'rebuildmo.py',
            'tests/conftest.py',
            'tests/partial.db',
            'tools/verify_distributions.py',
        }
        missing = required.difference(members)
        if missing:
            raise AssertionError(
                'sdist is missing: %s' % ', '.join(sorted(missing))
            )
        source_catalogs = {
            PurePosixPath(name).stem.removeprefix('imdbpy-')
            for name in members
            if name.startswith('imdb/locale/imdbpy-') and name.endswith('.po')
        }
        if source_catalogs != EXPECTED_CATALOGS:
            raise AssertionError(
                'sdist source catalogs differ: expected %s, found %s'
                % (sorted(EXPECTED_CATALOGS), sorted(source_catalogs))
            )
        if any(name.endswith('.mo') for name in members):
            raise AssertionError('sdist must not contain generated .mo files')
        fixture_member = next(
            member for member in archive.getmembers()
            if PurePosixPath(member.name).parts[1:] == ('tests', 'partial.db')
        )
        fixture = archive.extractfile(fixture_member)
        if fixture is None:
            raise AssertionError('unable to read tests/partial.db from sdist')
        fixture_path.write_bytes(fixture.read())


def inspect_wheel(path):
    """Check wheel contents and return its compiled catalog payloads."""
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        unexpected = {
            name for name in names
            if name.startswith(('tests/', 'tools/'))
            or name in {'build_support.py', 'msgfmt.py', 'rebuildmo.py'}
        }
        if unexpected:
            raise AssertionError(
                'wheel contains non-package source files: %s'
                % ', '.join(sorted(unexpected))
            )
        catalogs = {
            PurePosixPath(name).parts[-3]: archive.read(name)
            for name in names
            if name.startswith('imdb/locale/')
            and name.endswith('/LC_MESSAGES/imdbpy.mo')
        }
        if set(catalogs) != EXPECTED_CATALOGS:
            raise AssertionError(
                'wheel catalogs differ: expected %s, found %s'
                % (sorted(EXPECTED_CATALOGS), sorted(catalogs))
            )
        metadata_name = next(
            name for name in names if name.endswith('.dist-info/METADATA')
        )
        metadata = BytesParser().parsebytes(archive.read(metadata_name))
        for requirement in metadata.get_all('Requires-Dist', []):
            if requirement.lower().startswith('sqlalchemy') and \
                    'extra ==' not in requirement:
                raise AssertionError(
                    'SQLAlchemy is an unconditional wheel dependency'
                )
        entry_points_name = next(
            name for name in names
            if name.endswith('.dist-info/entry_points.txt')
        )
        entry_points = archive.read(entry_points_name).decode('utf-8')
        if 'cinemagoer = imdb.cli:main' not in entry_points:
            raise AssertionError('wheel has no cinemagoer console entry point')
    return catalogs


def smoke_test_wheel(wheel, fixture, directory):
    """Install one wheel without dependencies and exercise public behavior."""
    environment_dir = directory / (
        'venv-%s-%s' % (wheel.parent.name, wheel.stem)
    )
    venv.EnvBuilder(with_pip=True).create(environment_dir)
    scripts_dir = 'Scripts' if os.name == 'nt' else 'bin'
    python = environment_dir / scripts_dir / ('python.exe' if os.name == 'nt'
                                                else 'python')
    cli = environment_dir / scripts_dir / ('cinemagoer.exe'
                                             if os.name == 'nt'
                                             else 'cinemagoer')
    environment = os.environ.copy()
    environment.pop('PYTHONPATH', None)
    environment['PIP_CACHE_DIR'] = str(directory / 'pip-cache')
    environment['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    subprocess.run(
        [str(python), '-m', 'pip', 'install', '--no-deps', str(wheel)],
        check=True,
        cwd=directory,
        env=environment,
    )
    subprocess.run(
        [str(python), '-I', '-c', SMOKE_TEST, str(fixture)],
        check=True,
        cwd=directory,
        env=environment,
    )
    version = subprocess.run(
        [str(cli), '--version'],
        check=True,
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
    )
    if not version.stdout.startswith('cinemagoer '):
        raise AssertionError('cinemagoer --version returned unexpected output')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdist', required=True, type=Path)
    parser.add_argument('--wheel', required=True, action='append', type=Path)
    arguments = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix='cinemagoer-dist-') as temporary:
        directory = Path(temporary)
        fixture = directory / 'partial.db'
        verify_sdist(arguments.sdist.resolve(), fixture)
        reference_catalogs = None
        for wheel in arguments.wheel:
            wheel = wheel.resolve()
            catalogs = inspect_wheel(wheel)
            if reference_catalogs is not None and catalogs != reference_catalogs:
                raise AssertionError(
                    'direct and sdist wheel catalogs are not reproducible'
                )
            reference_catalogs = catalogs
            smoke_test_wheel(wheel, fixture, directory)
            print('verified %s' % wheel)
        print('verified %s' % arguments.sdist.resolve())
    return 0


if __name__ == '__main__':
    sys.exit(main())
