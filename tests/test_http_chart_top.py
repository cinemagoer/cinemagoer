from pytest import fixture

from imdb.parser.http.topBottomParser import DOMHTMLTop250Parser


@fixture(scope='module')
def chart_top(url_opener, base_url):
    """A function to retrieve the top movies page."""
    def retrieve():
        url = base_url + '/chart/top'
        return url_opener.retrieve_unicode(url)
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


def test_ranks_should_proceed_in_order(chart_top):
    page = chart_top()
    data = parser.parse(page)['data']
    ranks = [m['top 250 rank'] for m_id, m in data]
    assert ranks == list(range(1, 251))


def test_chart_should_contain_matrix(chart_top):
    page = chart_top()
    data = parser.parse(page)['data']
    assert '0133093' in dict(data)


def test_shawshank_should_be_top_movie(chart_top):
    page = chart_top()
    data = parser.parse(page)['data']
    top_id, top_movie = data[0]
    assert top_id == '0111161'
    assert top_movie['title'] == 'The Shawshank Redemption'
    assert top_movie['year'] == 1994
    assert top_movie['rating'] > 9
    assert top_movie['votes'] > 1900000
