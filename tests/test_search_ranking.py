import sqlite3

from imdb import Cinemagoer
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


def test_title_query_year_is_respected_in_search(tmp_path):
    database = tmp_path / 'ranking.db'
    matrix_soundex = title_soundex('The Matrix')
    with sqlite3.connect(database) as connection:
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

    ia = Cinemagoer('s3', uri=f'sqlite:///{database}')

    movies = ia.search_movie('The Matrix (2016)', results=5)

    assert movies[0].movieID == 9642498
    assert movies[0]['title'] == 'The Matrix'
    assert movies[0]['year'] == '2016'


def test_reversed_person_name_query_ranks_the_intended_person_first(ia):
    normal_people = ia.search_person('Fred Astaire', results=5)
    reversed_people = ia.search_person('Astaire Fred', results=5)

    assert normal_people[0]['name'] == 'Fred Astaire'
    assert reversed_people[0]['name'] == 'Fred Astaire'
    assert reversed_people[0].personID == normal_people[0].personID
