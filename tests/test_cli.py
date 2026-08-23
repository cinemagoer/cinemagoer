import pytest

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from imdb.cli import CLIError, get_item, list_results, search_item

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTIAL_DB = Path(__file__).with_name('partial.db').resolve()


def run_cli(*arguments, uri=PARTIAL_DB, pythonpath=None):
    command = [sys.executable, '-m', 'imdb.cli']
    if uri is not None:
        command.extend(('--uri', f'sqlite:///{uri}'))
    command.extend(arguments)
    environment = os.environ.copy()
    environment.pop('CINEMAGOER_S3_URI', None)
    import_paths = [str(REPO_ROOT)]
    if pythonpath is not None:
        import_paths.insert(0, str(pythonpath))
    environment['PYTHONPATH'] = os.pathsep.join(import_paths)
    return subprocess.run(
        command, cwd=REPO_ROOT, env=environment,
        capture_output=True, text=True, check=False,
    )


class _FakeItem:
    def __init__(self, item_id, label, field='name'):
        self.personID = item_id if field == 'name' else None
        self.movieID = item_id if field == 'title' else None
        self._label = label
        self._field = field

    def __getitem__(self, key):
        if key == f'long imdb {self._field}':
            return self._label
        raise KeyError(key)


def test_list_results_aligns_variable_width_ids(capsys):
    items = [
        _FakeItem(12584561, 'Fred Astaire'),
        _FakeItem(1, 'Fred Astaire'),
        _FakeItem(9056407, 'Alistair Ford'),
    ]

    list_results(items, type_='person')

    out = capsys.readouterr().out.splitlines()
    assert out[0] == '  # IMDb id  name'
    assert out[1] == '=== ======== ===='
    assert out[2].startswith('  1 12584561 ')
    assert out[3].startswith('  2        1 ')
    assert out[4].startswith('  3  9056407 ')


class _FakeConnection:
    def __init__(self, error=None):
        self.closed = False
        self.error = error

    def search_movie(self, _key):
        if self.error is not None:
            raise self.error
        return []

    def get_movie(self, _key):
        return SimpleNamespace(summary=lambda: 'Movie summary')

    def close(self):
        self.closed = True


def test_search_command_closes_connection(monkeypatch):
    connection = _FakeConnection()
    monkeypatch.setattr('imdb.cli.get_connection', lambda _args: connection)
    args = SimpleNamespace(
        type='movie', key='Matrix', first=False, n=5,
    )

    with pytest.raises(CLIError, match='no movie results'):
        search_item(args)

    assert connection.closed is True


def test_search_command_closes_connection_after_error(monkeypatch):
    connection = _FakeConnection(error=RuntimeError('search failed'))
    monkeypatch.setattr('imdb.cli.get_connection', lambda _args: connection)
    args = SimpleNamespace(
        type='movie', key='Matrix', first=False, n=5,
    )

    with pytest.raises(RuntimeError, match='search failed'):
        search_item(args)

    assert connection.closed is True


def test_get_command_closes_connection(monkeypatch, capsys):
    connection = _FakeConnection()
    monkeypatch.setattr('imdb.cli.get_connection', lambda _args: connection)
    args = SimpleNamespace(type='movie', key='9')

    get_item(args)

    assert capsys.readouterr().out == 'Movie summary\n'
    assert connection.closed is True


@pytest.mark.parametrize(
    ('arguments', 'expected'),
    [
        (('search', 'movie', 'Miss Jerry', '-n', '1'), 'Miss Jerry (1894)'),
        (('search', 'movie', 'Miss Jerry', '--first'), 'Title: Miss Jerry (1894)'),
        (('get', 'movie', 'tt0000009'), 'Title: Miss Jerry (1894)'),
        (('get', 'person', 'nm0000001'), 'Name: Astaire, Fred'),
    ],
)
def test_cli_search_and_get_subprocesses(arguments, expected):
    result = run_cli(*arguments)

    assert result.returncode == 0
    assert expected in result.stdout
    assert result.stderr == ''


def test_cli_no_result_is_concise_failure():
    result = run_cli(
        'search', 'movie', 'a-title-that-does-not-exist', '--first'
    )

    assert result.returncode == 1
    assert result.stdout == ''
    assert result.stderr == (
        "cinemagoer: error: no movie results found for "
        "'a-title-that-does-not-exist'\n"
    )
    assert 'Traceback' not in result.stderr


@pytest.mark.parametrize(
    ('item_id', 'message'),
    [
        ('invalid', 'invalid movie IMDb id'),
        ('999999999', 'movie with IMDb id'),
    ],
)
def test_cli_invalid_or_missing_id_is_concise_failure(item_id, message):
    result = run_cli('get', 'movie', item_id)

    assert result.returncode == 1
    assert result.stdout == ''
    assert message in result.stderr
    assert 'Traceback' not in result.stderr


def test_cli_invalid_uri_is_concise_failure(tmp_path):
    result = run_cli('get', 'movie', '9', uri=tmp_path / 'missing.db')

    assert result.returncode == 1
    assert result.stdout == ''
    assert 'SQLite database does not exist or is not a file' in result.stderr
    assert 'Traceback' not in result.stderr


def test_cli_missing_optional_dependency_is_concise_failure(tmp_path):
    (tmp_path / 'sqlalchemy.py').write_text(
        "raise ImportError('blocked for test', name='sqlalchemy')\n",
        encoding='utf-8',
    )
    result = run_cli(
        '--uri', 'postgresql://localhost/cinemagoer',
        'get', 'movie', '9', uri=None, pythonpath=tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == ''
    assert 'requires the cinemagoer[sqlalchemy] extra' in result.stderr
    assert 'Traceback' not in result.stderr


def test_cli_rejects_non_positive_result_count():
    result = run_cli('search', 'movie', 'Miss Jerry', '-n', '0')

    assert result.returncode == 2
    assert result.stdout == ''
    assert result.stderr.startswith('usage: cinemagoer search')
    assert 'must be a positive integer' in result.stderr


def test_cli_debug_mode_retains_traceback(tmp_path):
    command = [
        '--debug', '--uri', f'sqlite:///{tmp_path / "missing.db"}',
        'get', 'movie', '9',
    ]
    result = run_cli(*command, uri=None)

    assert result.returncode == 1
    assert 'Traceback (most recent call last)' in result.stderr
    assert 'SQLite database does not exist or is not a file' in result.stderr


def test_cli_expected_error_closes_connection_in_subprocess(tmp_path):
    marker = tmp_path / 'closed.txt'
    script = """
import os
from pathlib import Path

import imdb.cli as cli
from imdb import IMDbError


class Connection:
    def search_movie(self, key):
        raise IMDbError('forced search failure')

    def close(self):
        Path(os.environ['CINEMAGOER_CLOSE_MARKER']).write_text(
            'closed', encoding='utf-8'
        )


cli.get_connection = lambda args: Connection()
raise SystemExit(cli.main(['cinemagoer', 'search', 'movie', 'anything']))
"""
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(REPO_ROOT)
    environment['CINEMAGOER_CLOSE_MARKER'] = str(marker)
    result = subprocess.run(
        [sys.executable, '-c', script], cwd=REPO_ROOT, env=environment,
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 1
    assert result.stdout == ''
    assert result.stderr == 'cinemagoer: error: forced search failure\n'
    assert marker.read_text(encoding='utf-8') == 'closed'
