from pytest import fixture

from imdb.parser.http.movieParser import DOMHTMLOfficialsitesParser


@fixture(scope='module')
def movie_official_sites(url_opener, movies):
    """A function to retrieve the official sites page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/externalsites'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLOfficialsitesParser()


def test_sites_should_be_lists(movie_official_sites):
    page = movie_official_sites('matrix')
    data = parser.parse(page)['data']
    assert len(data.get('official sites', [])) == 1
    assert len(data.get('sound clips', [])) == 3
