from pytest import fixture

from imdb.parser.http.movieParser import DOMHTMLOfficialsitesParser


@fixture(scope='module')
def movie_sites_details(url_opener, movies):
    """A function to retrieve the sites details page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/externalsites'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLOfficialsitesParser()


def test_number_of_links(movie_sites_details):
    page = movie_sites_details('matrix')
    data = parser.parse(page)['data']
    official_sites_number = len(data.get('official sites', []))
    sound_clies_number = len(data.get('sound clips', []))
    assert(official_sites_number == 1)
    assert(sound_clies_number == 3)

