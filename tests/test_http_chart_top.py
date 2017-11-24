from pytest import fixture

from urllib.request import urlopen

from imdb.parser.http.topBottomParser import DOMHTMLTop250Parser


@fixture(scope='module')
def chart_top(base_url):
    """A function to retrieve the top movies page."""
    def retrieve():
        url = base_url + '/chart/top'
        return urlopen(url).read().decode('utf-8')
    return retrieve


parser = DOMHTMLTop250Parser()


def test_chart_should_contain_250_movies(chart_top):
    page = chart_top()
    data = parser.parse(page)['data']
    assert len(data) == 250


def test_all_movies_should_have_rating_and_votes(chart_top):
    page = chart_top()
    data = parser.parse(page)['data']
    for movie in dict(data).values():
        assert {'title', 'kind', 'year', 'rating', 'votes'}.issubset(set(movie.keys()))


def test_chart_should_contain_correct_movie(chart_top):
    page = chart_top()
    data = parser.parse(page)['data']
    assert '0133093' in dict(data)      # The Matrix
