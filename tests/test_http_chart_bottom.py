from pytest import fixture

from imdb.parser.http.topBottomParser import DOMHTMLBottom100Parser


@fixture(scope='module')
def chart_bottom(url_opener, base_url):
    """A function to retrieve the bottom movies page."""
    def retrieve():
        url = base_url + '/chart/bottom'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLBottom100Parser()


def test_chart_should_contain_100_movies(chart_bottom):
    page = chart_bottom()
    data = parser.parse(page)['data']
    assert len(data) == 100


def test_all_movies_should_have_rating_and_votes(chart_bottom):
    page = chart_bottom()
    data = parser.parse(page)['data']
    for movie in dict(data).values():
        assert {'title', 'kind', 'year', 'rating', 'votes'}.issubset(set(movie.keys()))


def test_chart_should_contain_correct_movie(chart_bottom):
    page = chart_bottom()
    data = parser.parse(page)['data']
    assert '0060666' in dict(data)          # Manos
