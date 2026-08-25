import pytest

import gzip
import importlib.util
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

from imdb import Cinemagoer
from imdb._exceptions import IMDbDataAccessError, IMDbError
from imdb.parser import s3 as s3_parser
from imdb.parser.s3._uri import redact_uri_secrets
from imdb.parser.s3.adapters import (
    NO_SOUNDEX_TITLE_LIMIT,
    SEARCH_CANDIDATE_LIMIT,
    SEARCH_CANDIDATE_MAX,
    SQLiteAdapter,
    search_candidate_limit,
    sqlite_path_from_uri,
)
from imdb.parser.s3.importer import (
    DATASET_HEADERS,
    MANIFEST_FILENAME,
    SQLAlchemyImporter,
    SQLiteImporter,
    import_dir,
)
from imdb.parser.s3.utils import name_soundexes, title_soundex, transf_multi_character
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


class _TrackingAdapter:
    def __init__(self):
        self.close_calls = 0

    def close(self):
        self.close_calls += 1


def test_access_system_context_manager_and_close_are_deterministic(monkeypatch):
    adapter = _TrackingAdapter()
    monkeypatch.setattr(s3_parser, 'adapter_for_uri', lambda _uri: adapter)
    access = s3_parser.IMDbS3AccessSystem(uri='tracking://')

    with access as entered:
        assert entered is access

    assert access._adapter is None
    assert adapter.close_calls == 1

    access.close()
    assert adapter.close_calls == 1


def test_access_system_context_manager_preserves_exceptions(monkeypatch):
    adapter = _TrackingAdapter()
    monkeypatch.setattr(s3_parser, 'adapter_for_uri', lambda _uri: adapter)

    with pytest.raises(RuntimeError, match='inside context'):
        with s3_parser.IMDbS3AccessSystem(uri='tracking://'):
            raise RuntimeError('inside context')

    assert adapter.close_calls == 1


def test_canonical_sqlite_uris_use_native_adapter(tmp_path):
    database = tmp_path / 'native.db'
    database.touch()

    with Cinemagoer('s3', uri=f'sqlite:///{database}') as ia:
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
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute('CREATE TABLE marker (id INTEGER, value TEXT)')
        connection.execute("INSERT INTO marker VALUES (1, 'original')")

    with Cinemagoer('s3', uri=f'{scheme}:///{database}') as ia:
        assert ia._adapter.get_row('marker', 'id', 1)['value'] == 'original'

        if scheme == 'sqlite':
            with closing(ia._adapter._connect()) as connection, connection:
                with pytest.raises(sqlite3.OperationalError, match='readonly'):
                    connection.execute("INSERT INTO marker VALUES (2, 'changed')")
        else:
            with pytest.raises(sqlalchemy.exc.DBAPIError, match='readonly'):
                with ia._adapter.engine.begin() as connection:
                    connection.execute(
                        sqlalchemy.text("INSERT INTO marker VALUES (2, 'changed')")
                    )

    with closing(sqlite3.connect(database)) as connection, connection:
        rows = connection.execute('SELECT id, value FROM marker').fetchall()
    assert rows == [(1, 'original')]


@pytest.mark.parametrize('uri', ['sqlite://', 'sqlite+pysqlite://'])
def test_in_memory_query_database_lives_for_adapter_lifetime(
        tmp_path, monkeypatch, uri):
    sqlalchemy = None
    if uri.startswith('sqlite+'):
        sqlalchemy = pytest.importorskip('sqlalchemy')
    monkeypatch.chdir(tmp_path)
    with Cinemagoer('s3', uri=uri) as ia:
        adapter = ia._adapter
        if uri == 'sqlite://':
            adapter.connection.execute(
                'CREATE TABLE marker (id INTEGER, value TEXT)'
            )
            adapter.connection.execute(
                "INSERT INTO marker VALUES (1, 'in memory')"
            )
        else:
            with adapter.engine.begin() as connection:
                connection.execute(sqlalchemy.text(
                    'CREATE TABLE marker (id INTEGER, value TEXT)'
                ))
                connection.execute(sqlalchemy.text(
                    "INSERT INTO marker VALUES (1, 'in memory')"
                ))
            adapter.metadata.reflect(bind=adapter.engine)

        assert adapter.get_row('marker', 'id', 1)['value'] == 'in memory'
        assert not list(tmp_path.iterdir())
    assert ia._adapter is None
    if uri == 'sqlite://':
        assert adapter.connection is None


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

    uri = (
        'postgresql+psycopg://user:uri-password@localhost/cinemagoer'
        '?password=query-password&token=query-token'
    )
    with pytest.raises(IMDbError, match='database driver') as exc_info:
        Cinemagoer('s3', uri=uri)

    assert 'cinemagoer[sqlalchemy]' not in str(exc_info.value)
    assert 'uri-password' not in str(exc_info.value)
    assert 'query-password' not in str(exc_info.value)
    assert 'query-token' not in str(exc_info.value)
    assert '***' in str(exc_info.value)


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_incomplete_sqlite_schema_is_actionable(tmp_path, scheme):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    database = tmp_path / 'empty.db'
    database.touch()
    with Cinemagoer('s3', uri=f'{scheme}:///{database}') as ia:
        with pytest.raises(
                IMDbDataAccessError, match='invalid or incomplete') as exc_info:
            ia.search_movie('Missing tables')

    if scheme == 'sqlite':
        cause_type = sqlite3.Error
    else:
        import sqlalchemy
        cause_type = sqlalchemy.exc.NoSuchTableError
    assert isinstance(exc_info.value.__cause__, cause_type)


def test_sqlalchemy_reflects_and_caches_only_tables_as_they_are_used(tmp_path):
    pytest.importorskip('sqlalchemy')
    database = tmp_path / 'lazy-reflection.db'
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript(
            '''
            CREATE TABLE marker (id INTEGER, value TEXT);
            CREATE TABLE unrelated (id INTEGER, value TEXT);
            INSERT INTO marker VALUES (1, 'expected');
            '''
        )

    with Cinemagoer('s3', uri=f'sqlite+pysqlite:///{database}') as ia:
        adapter = ia._adapter
        assert not adapter.tables
        assert adapter.get_row('marker', 'id', 1)['value'] == 'expected'
        reflected = adapter._table('marker')
        assert set(adapter.tables) == {'marker'}
        assert adapter._table('marker') is reflected


def test_uri_redaction_hides_credentials_and_common_query_secrets():
    uri = (
        'postgresql://user:password@database.example/cinemagoer'
        '?sslmode=require&api_key=key-value&access_token=token-value'
    )

    redacted = redact_uri_secrets(uri)

    assert redacted == (
        'postgresql://user:***@database.example/cinemagoer'
        '?sslmode=require&api_key=***&access_token=***'
    )


def test_sqlalchemy_query_errors_are_wrapped_with_their_cause(tmp_path):
    sqlalchemy = pytest.importorskip('sqlalchemy')
    database = tmp_path / 'empty.db'
    database.touch()
    with Cinemagoer('s3', uri=f'sqlite+pysqlite:///{database}') as ia:
        with pytest.raises(
                IMDbDataAccessError, match='unable to query') as exc_info:
            ia._adapter._fetchall(sqlalchemy.text('SELECT * FROM missing'))

    assert isinstance(
        exc_info.value.__cause__, sqlalchemy.exc.SQLAlchemyError
    )


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_no_soundex_search_does_not_scan_unindexed_title_tables(
        tmp_path, scheme):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    database = tmp_path / 'unindexed-no-soundex.db'
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript(
            '''
            CREATE TABLE title_basics (
                tconst INTEGER,
                primaryTitle TEXT,
                t_soundex TEXT
            );
            CREATE TABLE title_akas (
                titleId INTEGER,
                title TEXT,
                t_soundex TEXT
            );
            INSERT INTO title_basics VALUES (1, '!!!', NULL);
            INSERT INTO title_akas VALUES (1, '123', NULL);
            '''
        )

    with Cinemagoer('s3', uri=f'{scheme}:///{database}') as ia:
        assert ia.search_movie('!!!', results=5) == []
        assert ia.search_movie('123', results=5) == []


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_searches_without_soundex_are_exact_bounded_and_consistent(
        tmp_path, monkeypatch, scheme):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    database = tmp_path / 'no-soundex.db'
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript(
            '''
            CREATE TABLE title_basics (
                tconst INTEGER,
                primaryTitle TEXT,
                titleType TEXT,
                startYear INTEGER,
                t_soundex TEXT
            );
            CREATE TABLE title_akas (
                titleId INTEGER,
                title TEXT,
                t_soundex TEXT
            );
            CREATE TABLE name_basics (
                nconst INTEGER,
                primaryName TEXT,
                ns_soundex TEXT,
                sn_soundex TEXT,
                s_soundex TEXT
            );
            CREATE INDEX ix_title_basics_primaryTitle
                ON title_basics (primaryTitle);
            CREATE INDEX ix_title_akas_title ON title_akas (title);
            '''
        )
        connection.executemany(
            'INSERT INTO title_basics VALUES (?, ?, ?, ?, ?)',
            [
                (movie_id, str(movie_id), 'movie', 2025, None)
                for movie_id in range(1, 1001)
            ] + [
                (2001 + offset, '!!!', 'movie', 2025, None)
                for offset in range(NO_SOUNDEX_TITLE_LIMIT + 5)
            ] + [
                (3001, '!!!', 'movie', 2026, None),
                (3002, '東京', 'movie', 2026, None),
            ],
        )
        connection.executemany(
            'INSERT INTO title_akas VALUES (?, ?, ?)',
            [
                (movie_id, str(movie_id + 10000), None)
                for movie_id in range(1, 1001)
            ] + [
                (movie_id, '123', None)
                for movie_id in range(1, NO_SOUNDEX_TITLE_LIMIT + 6)
            ],
        )

    with Cinemagoer('s3', uri=f'{scheme}:///{database}') as ia:
        assert ia.search_movie('!!', results=5) == []
        assert ia.search_movie('!!! (2026)', results=5)[0].movieID == '0003001'
        assert ia.search_movie('東京', results=5)[0].movieID == '0003002'
        assert len(ia.search_movie('123', results=5)) == 5

        title_rows, _ = ia._adapter.search_titles(None, '!!!')
        _, aka_rows = ia._adapter.search_titles(None, '123')
        assert len(title_rows) == NO_SOUNDEX_TITLE_LIMIT
        assert len(aka_rows) == NO_SOUNDEX_TITLE_LIMIT
        assert ia._adapter.search_people([]) == []

        def fail_if_called(_soundexes):
            pytest.fail('person adapter called without a usable soundex')

        monkeypatch.setattr(ia._adapter, 'search_people', fail_if_called)
        assert ia.search_person('!!!', results=5) == []
        assert ia.search_person('123', results=5) == []


def test_candidate_limit_scales_but_never_undercuts_requested_results():
    assert search_candidate_limit(5) == SEARCH_CANDIDATE_LIMIT
    assert search_candidate_limit(1000) == SEARCH_CANDIDATE_MAX
    assert search_candidate_limit(SEARCH_CANDIDATE_MAX + 1) == \
        SEARCH_CANDIDATE_MAX + 1


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_soundex_candidates_are_bounded_with_exact_and_reversed_matches_first(
        tmp_path, scheme):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    database = tmp_path / 'bounded-search.db'
    movie_soundex = title_soundex('Exact Movie')
    person_soundexes = name_soundexes('Person, Exact')
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript(
            '''
            CREATE TABLE title_basics (
                tconst INTEGER,
                primaryTitle TEXT,
                titleType TEXT,
                startYear INTEGER,
                t_soundex TEXT
            );
            CREATE TABLE title_akas (
                titleId INTEGER,
                ordering INTEGER,
                title TEXT,
                t_soundex TEXT
            );
            CREATE TABLE name_basics (
                nconst INTEGER,
                primaryName TEXT,
                ns_soundex TEXT,
                sn_soundex TEXT,
                s_soundex TEXT
            );
            CREATE INDEX ix_title_basics_t_soundex
                ON title_basics (t_soundex);
            CREATE INDEX ix_title_akas_t_soundex ON title_akas (t_soundex);
            CREATE INDEX ix_name_basics_ns_soundex
                ON name_basics (ns_soundex);
            CREATE INDEX ix_name_basics_sn_soundex
                ON name_basics (sn_soundex);
            CREATE INDEX ix_name_basics_s_soundex
                ON name_basics (s_soundex);
            '''
        )
        collision_count = SEARCH_CANDIDATE_LIMIT + 5
        connection.executemany(
            'INSERT INTO title_basics VALUES (?, ?, ?, ?, ?)',
            [
                (movie_id, 'Fuzzy Candidate', 'movie', 2025, movie_soundex)
                for movie_id in range(1, collision_count + 1)
            ] + [
                (50000, 'Exact Movie', 'movie', 2026, movie_soundex),
            ],
        )
        connection.executemany(
            'INSERT INTO title_akas VALUES (?, ?, ?, ?)',
            [
                (movie_id, 1, 'Fuzzy Alternate', movie_soundex)
                for movie_id in range(1, collision_count + 1)
            ] + [
                (60000, 1, 'Exact Movie', movie_soundex),
            ],
        )
        connection.executemany(
            'INSERT INTO name_basics VALUES (?, ?, ?, ?, ?)',
            [
                (
                    person_id,
                    'Fuzzy Candidate',
                    person_soundexes[0],
                    person_soundexes[1],
                    person_soundexes[2],
                )
                for person_id in range(1, collision_count + 1)
            ] + [
                (
                    50000,
                    'Exact Person',
                    person_soundexes[0],
                    person_soundexes[1],
                    person_soundexes[2],
                ),
            ],
        )

    with Cinemagoer('s3', uri=f'{scheme}:///{database}') as ia:
        title_rows, aka_rows = ia._adapter.search_titles(
            movie_soundex,
            'Exact Movie',
            exact_titles=('Exact Movie',),
        )
        people_rows = ia._adapter.search_people(
            [code for code in person_soundexes if code],
            exact_names=('Person, Exact', 'Exact Person'),
        )
        movies = ia.search_movie('Exact Movie', results=5)
        people = ia.search_person('Person, Exact', results=5)

    assert len(title_rows) == SEARCH_CANDIDATE_LIMIT
    assert len(aka_rows) == SEARCH_CANDIDATE_LIMIT
    assert len(people_rows) == SEARCH_CANDIDATE_LIMIT
    assert title_rows[0]['tconst'] == 50000
    assert aka_rows[0]['titleId'] == 60000
    assert people_rows[0]['nconst'] == 50000
    assert movies[0].movieID == '0050000'
    assert people[0].personID == '0050000'


@pytest.mark.parametrize('scheme', ['sqlite', 'sqlite+pysqlite'])
def test_importer_round_trip(tmp_path, scheme):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    database = tmp_path / 'imported.db'
    manifest = import_dir(str(datasets), f'{scheme}:///{database}')

    with Cinemagoer('s3', uri=f'{scheme}:///{database}') as ia:
        result = ia.search_movie('Example Movie', results=5)[0]
        assert result.movieID == '0000001'
        assert result['year'] == '2026'
        assert result['runtimes'] == [95]

        aka_result = ia.search_movie('Example Alternate', results=5)[0]
        assert aka_result.movieID == '0000001'

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

    with closing(sqlite3.connect(database)) as connection, connection:
        indexes = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    assert ('ix_title_basics_tconst',) in indexes
    assert ('ix_title_basics_primaryTitle',) in indexes
    assert ('ix_title_akas_title',) in indexes


def test_importer_verbose_flag_reports_coarse_progress(tmp_path):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    script = Path(__file__).resolve().parents[1] / 'bin' / 's32cinemagoer.py'
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(script.parents[1])

    quiet = subprocess.run(
        [
            sys.executable, script, str(datasets),
            f'sqlite:///{tmp_path / "quiet.db"}',
        ],
        env=environment, capture_output=True, text=True, check=False,
    )
    verbose = subprocess.run(
        [
            sys.executable, script, '--verbose', str(datasets),
            f'sqlite:///{tmp_path / "verbose.db"}',
        ],
        env=environment, capture_output=True, text=True, check=False,
    )

    assert quiet.returncode == 0
    assert 'progress:' not in quiet.stderr
    assert verbose.returncode == 0
    assert 'DEBUG:imdb.parser.s3.importer:preflight progress: 0%' \
        in verbose.stderr
    assert 'DEBUG:imdb.parser.s3.importer:preflight progress: 100%' \
        in verbose.stderr
    assert 'DEBUG:imdb.parser.s3.importer:row import progress: 0%' \
        in verbose.stderr
    assert 'DEBUG:imdb.parser.s3.importer:row import progress: 100%' \
        in verbose.stderr


@pytest.mark.parametrize(
    ('signum', 'exit_code'),
    [
        (getattr(signal, name), 128 + getattr(signal, name))
        for name in ('SIGINT', 'SIGTERM', 'SIGHUP')
        if hasattr(signal, name)
    ],
)
def test_importer_script_stops_cleanly_on_signal(
        tmp_path, monkeypatch, capsys, signum, exit_code):
    script = Path(__file__).resolve().parents[1] / 'bin' / 's32cinemagoer.py'
    spec = importlib.util.spec_from_file_location('s32cinemagoer', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    previous_handler = signal.getsignal(signum)
    if previous_handler == signal.SIG_IGN:
        pytest.skip('the parent process ignores this signal')

    def interrupt_import(*_args, **_kwargs):
        signal.raise_signal(signum)

    monkeypatch.setattr(module, 'import_dir', interrupt_import)
    monkeypatch.setattr(
        sys,
        'argv',
        [str(script), str(tmp_path), f'sqlite:///{tmp_path / "signal.db"}'],
    )

    with pytest.raises(SystemExit) as exc_info:
        module.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == exit_code
    assert captured.out == ''
    assert captured.err == (
        's32cinemagoer.py: interrupted by %s; stopped cleanly\n'
        % signal.Signals(signum).name
    )
    assert 'Traceback' not in captured.err
    assert signal.getsignal(signum) == previous_handler


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
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute('CREATE TABLE marker (value TEXT)')
        connection.execute("INSERT INTO marker VALUES ('original')")

    with pytest.raises(IMDbError, match='unreadable gzip archive'):
        import_dir(str(datasets), f'sqlite:///{database}')

    with closing(sqlite3.connect(database)) as connection, connection:
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
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute('CREATE TABLE marker (value TEXT)')
        connection.execute("INSERT INTO marker VALUES ('original')")

    with pytest.raises(
            IMDbError, match=r'title\.basics\.tsv\.gz:2: expected 9 fields'):
        import_dir(str(datasets), f'sqlite:///{database}')

    with closing(sqlite3.connect(database)) as connection, connection:
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
    with closing(sqlite3.connect(database)) as connection, connection:
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
    with closing(sqlite3.connect(database)) as connection, connection:
        rows = connection.execute(
            'SELECT nconst, primaryName FROM name_basics'
        ).fetchall()
    assert rows == [(99, 'Original Person')]


@pytest.mark.parametrize(
    ('scheme', 'importer_class'),
    [
        ('sqlite', SQLiteImporter),
        ('sqlite+pysqlite', SQLAlchemyImporter),
    ],
)
def test_keyboard_interrupt_rolls_back_and_records_failed_manifest(
        tmp_path, monkeypatch, scheme, importer_class):
    if scheme == 'sqlite+pysqlite':
        pytest.importorskip('sqlalchemy')
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    database = tmp_path / 'existing.db'
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            'CREATE TABLE name_basics (nconst INTEGER, primaryName TEXT)'
        )
        connection.execute(
            "INSERT INTO name_basics VALUES (99, 'Original Person')"
        )

    original_import_file = importer_class.import_file

    def interrupt_on_second_file(importer, filename):
        if filename.endswith('title.akas.tsv.gz'):
            raise KeyboardInterrupt
        return original_import_file(importer, filename)

    monkeypatch.setattr(
        importer_class, 'import_file', interrupt_on_second_file
    )

    with pytest.raises(KeyboardInterrupt):
        import_dir(
            str(datasets), f'{scheme}:///{database}', cleanup=True
        )

    manifest = json.loads(
        (datasets / MANIFEST_FILENAME).read_text(encoding='utf-8')
    )
    assert manifest['status'] == 'failed'
    assert manifest['failure_type'] == 'KeyboardInterrupt'
    assert manifest['removed_files'] == []
    assert sorted(path.name for path in datasets.glob('*.tsv.gz')) == \
        sorted(DATASET_HEADERS)
    with closing(sqlite3.connect(database)) as connection, connection:
        rows = connection.execute(
            'SELECT nconst, primaryName FROM name_basics'
        ).fetchall()
    assert rows == [(99, 'Original Person')]


def test_keyboard_interrupt_during_cleanup_records_partial_cleanup(
        tmp_path, monkeypatch):
    datasets = tmp_path / 'datasets'
    datasets.mkdir()
    _write_complete_dataset(datasets)
    database = tmp_path / 'imported.db'
    original_remove = os.remove
    removed = []

    def interrupt_on_second_remove(filename):
        if removed:
            raise KeyboardInterrupt
        original_remove(filename)
        removed.append(Path(filename).name)

    monkeypatch.setattr(
        'imdb.parser.s3.importer.os.remove', interrupt_on_second_remove
    )

    with pytest.raises(KeyboardInterrupt):
        import_dir(str(datasets), f'sqlite:///{database}', cleanup=True)

    manifest = json.loads(
        (datasets / MANIFEST_FILENAME).read_text(encoding='utf-8')
    )
    assert manifest['status'] == 'database-complete-cleanup-interrupted'
    assert manifest['failure_type'] == 'KeyboardInterrupt'
    assert manifest['removed_files'] == removed
    assert len(list(datasets.glob('*.tsv.gz'))) == len(DATASET_HEADERS) - 1


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

    with Cinemagoer('s3', uri=f'sqlite:///{database}') as ia:
        assert isinstance(ia._adapter, SQLiteAdapter)
        assert ia.search_movie('Miss Jerry', results=5)[0].movieID == '0000009'


def test_sqlalchemy_sqlite_adapter_parity_when_installed():
    pytest.importorskip('sqlalchemy')
    database = Path(__file__).with_name('partial.db').resolve()
    with Cinemagoer('s3', uri=f'sqlite:///{database}') as native, \
            Cinemagoer(
                's3', uri=f'sqlite+pysqlite:///{database}'
            ) as sqlalchemy_access:
        assert [movie.movieID for movie in native.search_movie('Miss Jerry')] == [
            movie.movieID for movie in sqlalchemy_access.search_movie('Miss Jerry')
        ]
        assert native.get_movie('9')['title'] == \
            sqlalchemy_access.get_movie('9')['title']
