import pytest

from types import SimpleNamespace

from imdb.cli import get_item, list_results, search_item


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
    assert out[0] == '  # IMDb id name'
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
