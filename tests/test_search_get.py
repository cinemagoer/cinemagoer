import pytest

from imdb._exceptions import IMDbError


def test_search_and_get_person(ia):
    people = ia.search_person('Fred Astaire', results=5)
    assert people

    person = next(
        item for item in people
        if item.get('name') == 'Fred Astaire' and item.get('primary profession')
    )
    assert person.personID == '0000001'
    assert person['name'] == 'Fred Astaire'
    assert person.current_info == []

    fetched = ia.get_person(str(person.personID))
    assert fetched.personID == person.personID
    assert fetched['name'] == 'Fred Astaire'
    assert fetched['first name'] == 'Fred'
    assert fetched['last name'] == 'Astaire'
    assert fetched['primary profession'] == 'actor,miscellaneous,producer'
    assert len(fetched['known for']) == 4
    assert all(
        isinstance(movie.movieID, str) and len(movie.movieID) >= 7
        for movie in fetched['known for']
    )
    assert fetched.current_info == ['main', 'filmography', 'biography']


def test_search_and_get_movie(ia):
    movies = ia.search_movie('Miss Jerry', results=5)
    assert movies

    movie = next(
        item for item in movies
        if item.get('title') == 'Miss Jerry' and item.get('year') == '1894'
    )
    assert movie.movieID == '0000009'
    assert movie['title'] == 'Miss Jerry'
    assert movie['year'] == '1894'
    assert movie.current_info == []
    assert ia.get_imdbID(movie) == '0000009'
    assert ia.get_imdbURL(movie).endswith('/title/tt0000009/')

    fetched = ia.get_movie(str(movie.movieID))
    assert fetched.movieID == movie.movieID
    assert fetched == movie
    assert fetched['title'] == 'Miss Jerry'
    assert fetched['kind'] == 'movie'
    assert fetched['year'] == '1894'
    assert len(fetched['cast']) == 4
    assert all(
        isinstance(person.personID, str) and len(person.personID) >= 7
        for person in fetched['cast']
    )
    assert fetched.current_info == ['main', 'plot']


@pytest.mark.parametrize(
    ('getter', 'attribute', 'value', 'expected'),
    [
        ('get_movie', 'movieID', 9, '0000009'),
        ('get_movie', 'movieID', '9', '0000009'),
        ('get_movie', 'movieID', '0000009', '0000009'),
        ('get_movie', 'movieID', 'tt0000009', '0000009'),
        ('get_movie', 'movieID', 'TT0000009', '0000009'),
        ('get_person', 'personID', 1, '0000001'),
        ('get_person', 'personID', '1', '0000001'),
        ('get_person', 'personID', '0000001', '0000001'),
        ('get_person', 'personID', 'nm0000001', '0000001'),
        ('get_person', 'personID', 'NM0000001', '0000001'),
        ('get_movie', 'movieID', 12345678, '12345678'),
        ('get_movie', 'movieID', 'tt12345678', '12345678'),
        ('get_person', 'personID', 12345678, '12345678'),
        ('get_person', 'personID', 'nm12345678', '12345678'),
    ],
)
def test_get_normalizes_supported_imdb_id_inputs(
        ia, getter, attribute, value, expected):
    item = getattr(ia, getter)(value)

    assert getattr(item, attribute) == expected


@pytest.mark.parametrize(
    ('getter', 'value'),
    [
        ('get_movie', 'nm0000001'),
        ('get_movie', 'not-an-id'),
        ('get_person', 'tt0000009'),
        ('get_person', -1),
    ],
)
def test_get_rejects_invalid_imdb_id_inputs(ia, getter, value):
    with pytest.raises(IMDbError, match='invalid .* IMDb id'):
        getattr(ia, getter)(value)
