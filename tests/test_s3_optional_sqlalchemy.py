import pytest

import gzip
import importlib.util
import json
import logging
import sqlite3
from pathlib import Path

from imdb import Cinemagoer
from imdb._exceptions import IMDbDataAccessError, IMDbError
from imdb.parser.s3.adapters import SQLiteAdapter, sqlite_path_from_uri
from imdb.parser.s3.importer import (
    DATASET_HEADERS,
    MANIFEST_FILENAME,
    SQLAlchemyImporter,
    SQLiteImporter,
    import_dir,
)
from imdb.parser.s3.utils import transf_multi_character
from imdb.utils import RolesList


def _write_dataset(directory, name, headers, rows):
    path = directory / f'{name}.tsv.gz'
    with gzip.open(path, 'wt', encoding='utf-8') as stream:
        stream.write('\t'.join(headers) + '\n')
        for row in rows:
            stream.write('\t'.join(row) + '\n')


def _write_complete_dataset(directory):
    _write_dataset(
        directory,
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
        directory,
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
        directory,
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
        directory,
        'title.principals',
        ['tconst', 'ordering', 'nconst', 'category', 'job', 'characters'],
        [[
            'tt0000001', '1', 'nm0000001', 'actor', r'\N',
            '["Hero","Narrator"]',
        ]],
    )
    _write_dataset(
        directory,
        'title.crew',
        ['tconst', 'directors', 'writers'],
        [['tt0000001', r'\N', r'\N']],
    )
    _write_dataset(
        directory,
        'title.episode',
        ['tconst', 'parentTconst', 'seasonNumber', 'episodeNumber'],
        [['tt0000002', 'tt0000001', '1', '1']],
    )
    _write_dataset(
        directory,
        'title.ratings',
        ['tconst', 'averageRating', 'numVotes'],
        [['tt0000001', '7.5', '100']],
    )


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
    database.touch()
    ia = Cinemagoer('s3', uri=f'sqlite:///{database}')

    assert isinstance(ia._adapter, SQLiteAdapter)
    assert sqlite_path_from_uri('sqlite://') == ':memory:'
    assert sqlite_path_from_uri('sqlite:///:memory:') == ':memory:'
    assert sqlite_path_from_uri('sqlite:///relative.db') == 'relative.db'
    assert sqlite_path_from_uri('sqlite:////tmp/absolute.db') == \
        '/tmp/absolute.db'


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_query_adapter_does_not_create_missing_sqlite_database(
        tmp_path, monkeypatch, scheme):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    monkeypatch.chdir(tmp_path)
    database = Path('missing.db')

    with pytest.raises(IMDbDataAccessError, match='does not exist'):
        Cinemagoer('s3', uri=f'{scheme}:///missing.db')

    assert not database.exists()


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_file_backed_query_adapters_are_read_only(tmp_path, scheme):
    sqlalchemy = None
    if scheme == 'sqlite+pysqlite':
        sqlalchemy = pytest.importorskip('sqlalchemy')
    database = tmp_path / 'existing.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE marker (id INTEGER, value TEXT)')
        connection.execute("INSERT INTO marker VALUES (1, 'original')")

    ia = Cinemagoer('s3', uri=f'{scheme}:///{database}')
    assert ia._adapter.get_row('marker', 'id', 1)['value'] == 'original'

    if scheme == 'sqlite':
        with ia._adapter._connect() as connection:
            with pytest.raises(sqlite3.OperationalError, match='readonly'):
                connection.execute("INSERT INTO marker VALUES (2, 'changed')")
    else:
        with pytest.raises(sqlalchemy.exc.DBAPIError, match='readonly'):
            with ia._adapter.engine.begin() as connection:
                connection.execute(
                    sqlalchemy.text("INSERT INTO marker VALUES (2, 'changed')")
                )

    ia._adapter.close()
    with sqlite3.connect(database) as connection:
        rows = connection.execute('SELECT id, value FROM marker').fetchall()
    assert rows == [(1, 'original')]


@pytest.mark.parametrize('uri', ['sqlite://', 'sqlite+pysqlite://'])
def test_in_memory_query_database_lives_for_adapter_lifetime(
        tmp_path, monkeypatch, uri):
    sqlalchemy = None
    if uri.startswith('sqlite+'):
        sqlalchemy = pytest.importorskip('sqlalchemy')
    monkeypatch.chdir(tmp_path)
    ia = Cinemagoer('s3', uri=uri)

    if uri == 'sqlite://':
        ia._adapter.connection.execute(
            'CREATE TABLE marker (id INTEGER, value TEXT)'
        )
        ia._adapter.connection.execute(
            "INSERT INTO marker VALUES (1, 'in memory')"
        )
    else:
        with ia._adapter.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                'CREATE TABLE marker (id INTEGER, value TEXT)'
            ))
            connection.execute(sqlalchemy.text(
                "INSERT INTO marker VALUES (1, 'in memory')"
            ))
        ia._adapter.metadata.reflect(bind=ia._adapter.engine)

    assert ia._adapter.get_row('marker', 'id', 1)['value'] == 'in memory'
    assert not list(tmp_path.iterdir())
    ia._adapter.close()


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
    _write_complete_dataset(datasets)
    database = tmp_path / 'imported.db'
    manifest = import_dir(str(datasets), f'{scheme}:///{database}')

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
    assert manifest['status'] == 'completed'
    assert all(file_info['source_rows'] == 1
               for file_info in manifest['files'])
    assert all(file_info['imported_rows'] == 1
               for file_info in manifest['files'])
    manifest_path = datasets / MANIFEST_FILENAME
    assert json.loads(manifest_path.read_text(encoding='utf-8')) == manifest

    with sqlite3.connect(database) as connection:
        indexes = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    assert ('ix_title_basics_tconst',) in indexes


@pytest.mark.parametrize('directory_state', ['missing', 'empty'])
def test_missing_or_empty_dataset_does_not_create_database(
        tmp_path, directory_state):
    datasets = tmp_path / 'datasets'
    if directory_state == 'empty':
        datasets.mkdir()
    database = tmp_path / 'should-not-exist.db'

    with pytest.raises(IMDbError, match='directory'):
        import_dir(str(datasets), f'sqlite:///{database}')

    assert not database.exists()


def test_incomplete_dataset_does_not_create_database(tmp_path):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_dataset(
        datasets,
        'title.ratings',
        ['tconst', 'averageRating', 'numVotes'],
        [['tt0000001', '7.5', '100']],
    )
    database = tmp_path / 'should-not-exist.db'

    with pytest.raises(IMDbError, match='missing required dataset'):
        import_dir(str(datasets), f'sqlite:///{database}')

    assert not database.exists()


def test_unsupported_dataset_does_not_create_database(tmp_path):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    _write_dataset(datasets, 'title.unknown', ['id'], [['1']])
    database = tmp_path / 'should-not-exist.db'

    with pytest.raises(IMDbError, match='unsupported dataset archive'):
        import_dir(str(datasets), f'sqlite:///{database}')

    assert not database.exists()


def test_empty_dataset_file_does_not_create_database(tmp_path):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    _write_dataset(
        datasets,
        'title.ratings',
        ['tconst', 'averageRating', 'numVotes'],
        [],
    )
    database = tmp_path / 'should-not-exist.db'

    with pytest.raises(IMDbError, match='dataset contains no rows'):
        import_dir(str(datasets), f'sqlite:///{database}')

    assert not database.exists()


def test_corrupt_dataset_does_not_change_database(tmp_path):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    (datasets / 'title.crew.tsv.gz').write_bytes(b'not a gzip archive')
    database = tmp_path / 'existing.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE marker (value TEXT)')
        connection.execute("INSERT INTO marker VALUES ('original')")

    with pytest.raises(IMDbError, match='unreadable gzip archive'):
        import_dir(str(datasets), f'sqlite:///{database}')

    with sqlite3.connect(database) as connection:
        value = connection.execute('SELECT value FROM marker').fetchone()[0]
    assert value == 'original'


def test_malformed_row_reports_file_and_line_without_changing_database(
        tmp_path):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    _write_dataset(
        datasets,
        'title.basics',
        DATASET_HEADERS['title.basics.tsv.gz'],
        [['tt0000001', 'movie']],
    )
    database = tmp_path / 'existing.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE marker (value TEXT)')
        connection.execute("INSERT INTO marker VALUES ('original')")

    with pytest.raises(
            IMDbError, match=r'title\.basics\.tsv\.gz:2: expected 9 fields'):
        import_dir(str(datasets), f'sqlite:///{database}')

    with sqlite3.connect(database) as connection:
        value = connection.execute('SELECT value FROM marker').fetchone()[0]
    assert value == 'original'


@pytest.mark.parametrize(
    'uri',
    ['sqlite://', 'sqlite:///:memory:', 'sqlite+pysqlite:///:memory:'],
)
def test_importer_rejects_ephemeral_sqlite_destinations(tmp_path, uri):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)

    with pytest.raises(IMDbError, match='persistent database'):
        import_dir(str(datasets), uri)

    assert not (datasets / MANIFEST_FILENAME).exists()


def test_connectivity_failure_preserves_sources_and_records_manifest(tmp_path):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    database = tmp_path / 'missing-parent' / 'imported.db'

    with pytest.raises(IMDbError, match='unable to open SQLite database'):
        import_dir(
            str(datasets), f'sqlite:///{database}', cleanup=True
        )

    assert sorted(path.name for path in datasets.glob('*.tsv.gz')) == \
        sorted(DATASET_HEADERS)
    manifest = json.loads(
        (datasets / MANIFEST_FILENAME).read_text(encoding='utf-8')
    )
    assert manifest['status'] == 'failed'
    assert manifest['removed_files'] == []
    assert all(item['imported_rows'] is None for item in manifest['files'])


@pytest.mark.parametrize(
    ('scheme', 'importer_class'),
    [
        ('sqlite', SQLiteImporter),
        ('sqlite+pysqlite', SQLAlchemyImporter),
    ],
)
def test_later_import_failure_rolls_back_and_preserves_sources(
        tmp_path, monkeypatch, scheme, importer_class):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    database = tmp_path / 'existing.db'
    with sqlite3.connect(database) as connection:
        connection.execute(
            'CREATE TABLE name_basics (nconst INTEGER, primaryName TEXT)'
        )
        connection.execute(
            "INSERT INTO name_basics VALUES (99, 'Original Person')"
        )

    original_import_file = importer_class.import_file

    def fail_on_second_file(importer, filename):
        if filename.endswith('title.akas.tsv.gz'):
            raise RuntimeError('injected later-file failure')
        return original_import_file(importer, filename)

    monkeypatch.setattr(importer_class, 'import_file', fail_on_second_file)

    with pytest.raises(RuntimeError, match='injected later-file failure'):
        import_dir(
            str(datasets), f'{scheme}:///{database}', cleanup=True
        )

    assert sorted(path.name for path in datasets.glob('*.tsv.gz')) == \
        sorted(DATASET_HEADERS)
    manifest = json.loads(
        (datasets / MANIFEST_FILENAME).read_text(encoding='utf-8')
    )
    assert manifest['status'] == 'failed'
    assert manifest['removed_files'] == []
    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            'SELECT nconst, primaryName FROM name_basics'
        ).fetchall()
    assert rows == [(99, 'Original Person')]


def test_cleanup_runs_only_after_success_and_reports_removed_files(
        tmp_path, caplog):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    database = tmp_path / 'imported.db'
    caplog.set_level(logging.INFO)

    manifest = import_dir(
        str(datasets), f'sqlite:///{database}', cleanup=True
    )

    assert manifest['status'] == 'completed'
    assert manifest['removed_files'] == sorted(DATASET_HEADERS)
    assert not list(datasets.glob('*.tsv.gz'))
    for filename in DATASET_HEADERS:
        assert 'removed source archive' in caplog.text
        assert filename in caplog.text


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
