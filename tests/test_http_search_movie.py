from pytest import fixture, mark

from imdb.parser.http.searchMovieParser import DOMHTMLSearchMovieParser


@fixture(scope='module')
def search_movie(url_opener, search):
    """A function to retrieve the search result for a title."""
    def retrieve(term):
        url = search + '?s=tt&q=' + term.replace(' ', '+')
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLSearchMovieParser()


def test_found_one_result_should_be_list_with_one_movie(search_movie):
    page = search_movie('od instituta do proizvodnje')
    data = parser.parse(page)['data']
    assert data == [
        ('0483758', {'kind': 'short', 'title': 'Od instituta do proizvodnje', 'year': 1971})
    ]


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_movies(search_movie):
    page = search_movie('ace in the hole')
    data = parser.parse(page)['data']
    assert 185 < len(data) < 200


def test_found_too_many_result_should_contain_200_movies(search_movie):
    page = search_movie('matrix')
    data = parser.parse(page)['data']
    assert len(data) == 200


def test_found_many_result_should_contain_correct_movie(search_movie):
    page = search_movie('matrix')
    data = parser.parse(page)['data']
    movies = dict(data)
    assert movies['0133093'] == {'title': 'The Matrix', 'kind': 'movie', 'year': 1999}


def test_found_movie_should_have_kind(search_movie):
    page = search_movie('matrix')
    data = parser.parse(page)['data']
    movies = dict(data)
    assert movies['0106062'] == {'title': 'Matrix', 'kind': 'tv series', 'year': 1993}


def test_found_movie_should_have_imdb_index(search_movie):
    page = search_movie('blink')
    data = parser.parse(page)['data']
    movies = dict(data)
    assert movies['4790262'] == {'title': 'Blink', 'imdbIndex': 'IV',
                                 'kind': 'movie', 'year': 2015}


def test_found_none_result_should_be_empty(search_movie):
    page = search_movie('%e3%82%a2')
    data = parser.parse(page)['data']
    assert data == []
