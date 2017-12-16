from pytest import fixture, mark

from imdb.parser.http.searchKeywordParser import DOMHTMLSearchMovieKeywordParser


@fixture(scope='module')
def search_movie_keyword(url_opener, base_url):
    """A function to retrieve the search result for movies with a keyword."""
    def retrieve(term):
        url = base_url + '/search/keyword?keywords=' + term.replace(' ', '+')
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLSearchMovieKeywordParser()


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_movies(search_movie_keyword):
    page = search_movie_keyword('colander')
    data = parser.parse(page)['data']
    assert len(data) == 4


def test_found_too_many_result_should_contain_50_movies(search_movie_keyword):
    page = search_movie_keyword('computer')
    data = parser.parse(page)['data']
    assert len(data) == 50


def test_found_many_result_should_contain_correct_movie(search_movie_keyword):
    page = search_movie_keyword('colander')
    data = parser.parse(page)['data']
    movies = dict(data)
    assert movies['0382932'] == {'title': 'Ratatouille', 'kind': 'movie', 'year': 2007}
