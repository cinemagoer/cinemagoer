import pytest

import sqlite3
from contextlib import closing

from imdb import Cinemagoer
from imdb._exceptions import IMDbError
from imdb.parser.s3.utils import scan_titles, title_soundex


def test_exact_movie_title_ranks_before_aka_and_no_year_noise():
    candidates = [
        (40123928, {'title': 'The Matrix', 'kind': 'short', 'year': '2022'}),
        (31444806, {'title': 'The Matrix'}),
        (133093, {'title': 'The Matrix', 'kind': 'movie', 'year': '1999'}),
        (9851526, {'title': 'The Matrix', 'kind': 'short', 'year': '2004'}),
    ]

    ranked = scan_titles(candidates, 'The Matrix', results=10)

    assert [item[1][0] for item in ranked[:3]] == [133093, 40123928, 9851526]


@pytest.mark.parametrize(
    ('query', 'matching_title', 'competing_title'),
    [
        ('Matrix, The', 'The Matrix', 'Matrix Reloaded'),
        ('Vita è bella, La', 'La vita è bella', 'Vita da cani'),
        ('Himmel über Berlin, Der', 'Der Himmel über Berlin', 'Himmel ohne Sterne'),
        (
            'Fabuleux destin d’Amélie Poulain, Le',
            'Le fabuleux destin d’Amélie Poulain',
            'Fabuleux voyage',
        ),
    ],
)
def test_canonical_article_queries_rank_leading_article_titles_first(
        query, matching_title, competing_title):
    candidates = [
        (1, {'title': matching_title, 'kind': 'movie'}),
        (2, {'title': competing_title, 'kind': 'movie'}),
    ]

    ranked = scan_titles(candidates, query)

    assert ranked[0][1][0] == 1


def test_article_insensitive_ranking_preserves_deduplication_kind_and_limits():
    candidates = [
        (1, {'title': 'The Matrix', 'kind': 'episode', 'year': '1999'}),
        (2, {'title': 'The Matrix', 'kind': 'short', 'year': '1999'}),
        (3, {'title': 'The Matrix', 'kind': 'movie', 'year': '1999'}),
        # An AKA-style duplicate for the same title ID must not add a result.
        (3, {'title': 'Matrix, The'}),
    ]

    ranked = scan_titles(candidates, 'Matrix', results=2)

    assert [item[1][0] for item in ranked] == [3, 2]


def test_title_query_year_is_respected_in_search(tmp_path):
    database = tmp_path / 'ranking.db'
    matrix_soundex = title_soundex('The Matrix')
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
            '''
        )
        connection.executemany(
            'INSERT INTO title_basics VALUES (?, ?, ?, ?, ?)',
            [
                (133093, 'The Matrix', 'movie', 1999, matrix_soundex),
                (9642498, 'The Matrix', 'movie', 2016, matrix_soundex),
            ],
        )

    with Cinemagoer('s3', uri=f'sqlite:///{database}') as ia:
        movies = ia.search_movie('Matrix, The (2016)', results=5)

    assert movies[0].movieID == '9642498'
    assert movies[0]['title'] == 'The Matrix'
    assert movies[0]['year'] == '2016'


def _search_options_database(path):
    shared_soundex = title_soundex('Shared Title')
    series_soundex = title_soundex('Example Series')
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(
            '''
            CREATE TABLE title_basics (
                tconst INTEGER,
                primaryTitle TEXT,
                titleType TEXT,
                isAdult INTEGER,
                t_soundex TEXT
            );
            CREATE TABLE title_akas (
                titleId INTEGER,
                title TEXT,
                t_soundex TEXT
            );
            '''
        )
        connection.executemany(
            'INSERT INTO title_basics VALUES (?, ?, ?, ?, ?)',
            [
                (1, 'Shared Title', 'movie', 0, shared_soundex),
                (2, 'Shared Title', 'movie', 1, shared_soundex),
                (3, 'Example Series', 'tv series', 0, series_soundex),
                (4, 'Example Series', 'tvSeries', 0, series_soundex),
            ],
        )


def test_adult_search_constructor_sets_default_policy(tmp_path):
    database = tmp_path / 'search-options.db'
    _search_options_database(database)

    with Cinemagoer(
        's3', uri=f'sqlite:///{database}', adultSearch=False
    ) as restricted:
        default_results = restricted.search_movie('Shared Title')
        adult_results = restricted.search_movie_advanced(
            'Shared Title', adult=True
        )
    with Cinemagoer('s3', uri=f'sqlite:///{database}') as unrestricted:
        all_results = unrestricted.search_movie('Shared Title')
        nonadult_results = unrestricted.search_movie_advanced(
            'Shared Title', adult=False
        )

    assert {movie.movieID for movie in default_results} == {'0000001'}
    assert {movie.movieID for movie in adult_results} == {'0000002'}
    assert {movie.movieID for movie in all_results} == {
        '0000001', '0000002',
    }
    assert {movie.movieID for movie in nonadult_results} == {'0000001'}


@pytest.mark.parametrize('title_types', [['tvSeries'], 'tv series'])
def test_title_type_filter_supports_raw_and_transformed_values(
        tmp_path, title_types):
    database = tmp_path / 'search-options.db'
    _search_options_database(database)

    with Cinemagoer('s3', uri=f'sqlite:///{database}') as ia:
        results = ia.search_movie_advanced(
            'Example Series', title_types=title_types
        )

    assert {movie.movieID for movie in results} == {'0000003', '0000004'}


@pytest.mark.parametrize(
    'options',
    [
        {'sort': 'year'},
        {'sort_dir': 'asc'},
        {'sort': 'title', 'sort_dir': 'desc'},
    ],
)
def test_advanced_search_rejects_unsupported_sort_options(ia, options):
    with pytest.raises(
        IMDbError,
        match='sort and sort_dir are not supported.*omit both arguments',
    ):
        ia.search_movie_advanced('Miss Jerry', **options)


def test_reversed_person_name_query_ranks_the_intended_person_first(ia):
    normal_people = ia.search_person('Fred Astaire', results=5)
    reversed_people = ia.search_person('Astaire Fred', results=5)

    assert normal_people[0]['name'] == 'Fred Astaire'
    assert reversed_people[0]['name'] == 'Fred Astaire'
    assert reversed_people[0].personID == normal_people[0].personID
