import pytest

from imdb.Character import Character


def test_search_and_get_person(ia):
    people = ia.search_person('Fred Astaire', results=5)
    assert people

    person = next(
        item for item in people
        if item.get('name') == 'Fred Astaire' and item.get('primary profession')
    )
    assert person.personID == 1
    assert person['name'] == 'Fred Astaire'
    assert person.current_info == []

    fetched = ia.get_person(str(person.personID))
    assert fetched.personID == str(person.personID)
    assert fetched['name'] == 'Fred Astaire'
    assert fetched['primary profession'] == 'actor,miscellaneous,producer'
    assert len(fetched['known for']) == 4
    assert fetched.current_info == ['main', 'filmography', 'biography']


def test_search_and_get_movie(ia):
    movies = ia.search_movie('Miss Jerry', results=5)
    assert movies

    movie = next(
        item for item in movies
        if item.get('title') == 'Miss Jerry' and item.get('year') == '1894'
    )
    assert movie.movieID == 9
    assert movie['title'] == 'Miss Jerry'
    assert movie['year'] == '1894'
    assert movie.current_info == []

    fetched = ia.get_movie(str(movie.movieID))
    assert fetched.movieID == str(movie.movieID)
    assert fetched['title'] == 'Miss Jerry'
    assert fetched['kind'] == 'movie'
    assert fetched['year'] == '1894'
    assert len(fetched['cast']) == 3
    assert fetched.current_info == ['main', 'plot']


def test_movie_cast_contains_character_roles(ia):
    movie = ia.get_movie('9')
    character = movie['cast'][0].currentRole

    assert isinstance(character, Character)
    assert not character
    assert character.get('name') is None


@pytest.mark.xfail(reason='standalone character search/get is not available in the S3 backend', raises=AttributeError)
def test_character_search_and_get_not_available(ia):
    ia.search_character('The Queen')