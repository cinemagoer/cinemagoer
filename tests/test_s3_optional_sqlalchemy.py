import pytest

import gzip
import importlib.util
import sqlite3
from pathlib import Path

from imdb import Cinemagoer
from imdb._exceptions import IMDbError
from imdb.parser.s3.adapters import SQLiteAdapter, sqlite_path_from_uri
from imdb.parser.s3.importer import import_dir
from imdb.parser.s3.utils import transf_multi_character
from imdb.utils import RolesList


def _write_dataset(directory, name, headers, rows):
    path = directory / f'{name}.tsv.gz'
    with gzip.open(path, 'wt', encoding='utf-8') as stream:
        stream.write('\t'.join(headers) + '\n')
        for row in rows:
            stream.write('\t'.join(row) + '\n')


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (None, None),
        ('', ''),
        ('[]', ''),
        ('["Neo"]', 'Neo'),
        ('["Neo","Thomas Anderson"]', 'Neo / Thomas Anderson'),
        ('["The \\"Dude\\""]', 'The "Dude"'),
        ('["Amélie"]', 'Amélie'),
    ],
)
def test_transform_character_names(value, expected):
    assert transf_multi_character(value) == expected


def test_canonical_sqlite_uris_use_native_adapter(tmp_path):
    database = tmp_path / 'native.db'
    ia = Cinemagoer('s3', uri=f'sqlite:///{database}')

    assert isinstance(ia._adapter, SQLiteAdapter)
    assert sqlite_path_from_uri('sqlite://') == ':memory:'
    assert sqlite_path_from_uri('sqlite:///:memory:') == ':memory:'
    assert sqlite_path_from_uri('sqlite:///relative.db') == 'relative.db'
    assert sqlite_path_from_uri('sqlite:////tmp/absolute.db') == \
        '/tmp/absolute.db'


def test_invalid_sqlite_uri_is_actionable():
    with pytest.raises(IMDbError, match='invalid SQLite URI'):
        Cinemagoer('s3', uri='sqlite://database.db')


def test_missing_sqlalchemy_extra_is_actionable():
    try:
        import sqlalchemy  # noqa: F401
    except ImportError:
        with pytest.raises(IMDbError, match=r'cinemagoer\[sqlalchemy\]'):
            Cinemagoer('s3', uri='postgresql://localhost/cinemagoer')
    else:
        pytest.skip('SQLAlchemy is installed in this test environment')


def test_missing_database_driver_is_not_reported_as_missing_sqlalchemy():
    pytest.importorskip('sqlalchemy')
    if importlib.util.find_spec('psycopg') is not None:
        pytest.skip('psycopg is installed in this test environment')

    with pytest.raises(IMDbError, match='database driver') as exc_info:
        Cinemagoer('s3', uri='postgresql+psycopg://localhost/cinemagoer')

    assert 'cinemagoer[sqlalchemy]' not in str(exc_info.value)


def test_incomplete_sqlite_schema_is_actionable(tmp_path):
    database = tmp_path / 'empty.db'
    database.touch()
    ia = Cinemagoer('s3', uri=f'sqlite:///{database}')

    with pytest.raises(IMDbError, match='invalid or incomplete'):
        ia.search_movie('Missing tables')


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_importer_round_trip(tmp_path, scheme):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_dataset(
        datasets,
        'title.basics',
        [
            'tconst', 'titleType', 'primaryTitle', 'originalTitle',
            'isAdult', 'startYear', 'endYear', 'runtimeMinutes', 'genres',
        ],
        [[
            'tt0000001', 'movie', 'Example Movie', 'Example Movie', '0',
            '2026', r'\N', '95', 'Drama',
        ]],
    )
    _write_dataset(
        datasets,
        'title.akas',
        [
            'titleId', 'ordering', 'title', 'region', 'language', 'types',
            'attributes', 'isOriginalTitle',
        ],
        [[
            'tt0000001', '1', 'Example Alternate', 'US', 'en', r'\N',
            r'\N', '0',
        ]],
    )
    _write_dataset(
        datasets,
        'name.basics',
        [
            'nconst', 'primaryName', 'birthYear', 'deathYear',
            'primaryProfession', 'knownForTitles',
        ],
        [[
            'nm0000001', 'Example Actor', r'\N', r'\N', 'actor',
            'tt0000001',
        ]],
    )
    _write_dataset(
        datasets,
        'title.principals',
        ['tconst', 'ordering', 'nconst', 'category', 'job', 'characters'],
        [[
            'tt0000001', '1', 'nm0000001', 'actor', r'\N',
            '["Hero","Narrator"]',
        ]],
    )
    _write_dataset(
        datasets,
        'title.crew',
        ['tconst', 'directors', 'writers'],
        [['tt0000001', r'\N', r'\N']],
    )
    _write_dataset(
        datasets,
        'title.episode',
        ['tconst', 'parentTconst', 'seasonNumber', 'episodeNumber'],
        [],
    )
    _write_dataset(
        datasets,
        'title.ratings',
        ['tconst', 'averageRating', 'numVotes'],
        [['tt0000001', '7.5', '100']],
    )
    database = tmp_path / 'imported.db'
    import_dir(str(datasets), f'{scheme}:///{database}')

    ia = Cinemagoer('s3', uri=f'{scheme}:///{database}')
    result = ia.search_movie('Example Movie', results=5)[0]
    assert result.movieID == 1
    assert result['year'] == '2026'
    assert result['runtimes'] == [95]

    aka_result = ia.search_movie('Example Alternate', results=5)[0]
    assert aka_result.movieID == 1

    movie = ia.get_movie('1')
    actor = movie['cast'][0]
    assert isinstance(actor.currentRole, RolesList)
    assert [role['name'] for role in actor.currentRole] == [
        'Hero', 'Narrator',
    ]
    assert str(actor.currentRole) == 'Hero / Narrator'
    assert '<name>Hero</name>' in actor.asXML()
    assert '<name>Narrator</name>' in actor.asXML()
    assert 'Example Actor (Hero / Narrator)' in movie.summary()

    with sqlite3.connect(database) as connection:
        indexes = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    assert ('ix_title_basics_tconst',) in indexes


def test_existing_partial_database_uses_native_adapter():
    database = Path(__file__).with_name('partial.db').resolve()
    ia = Cinemagoer('s3', uri=f'sqlite:///{database}')

    assert isinstance(ia._adapter, SQLiteAdapter)
    assert ia.search_movie('Miss Jerry', results=5)[0].movieID == 9


def test_sqlalchemy_sqlite_adapter_parity_when_installed():
    pytest.importorskip('sqlalchemy')
    database = Path(__file__).with_name('partial.db').resolve()
    native = Cinemagoer('s3', uri=f'sqlite:///{database}')
    sqlalchemy_access = Cinemagoer(
        's3', uri=f'sqlite+pysqlite:///{database}'
    )

    assert [movie.movieID for movie in native.search_movie('Miss Jerry')] == [
        movie.movieID for movie in sqlalchemy_access.search_movie('Miss Jerry')
    ]
    assert native.get_movie('9')['title'] == \
        sqlalchemy_access.get_movie('9')['title']
