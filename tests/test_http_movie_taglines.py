from pytest import fixture

from imdb.parser.http.movieParser import DOMHTMLTaglinesParser


@fixture(scope='module')
def movie_taglines(url_opener, movies):
    """A function to retrieve the taglines page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/taglines'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLTaglinesParser()


def test_movie_taglines_single_should_be_a_list_of_phrases(movie_taglines):
    page = movie_taglines('if....')
    data = parser.parse(page)['data']
    assert data['taglines'] == ['Which side will you be on?']


def test_movie_taglines_multiple_should_be_a_list_of_phrases(movie_taglines):
    page = movie_taglines('manos')
    data = parser.parse(page)['data']
    assert len(data['taglines']) == 3
    assert data['taglines'][0] == "It's Shocking! It's Beyond Your Imagination!"


def test_summary_none_should_be_excluded(movie_taglines):
    page = movie_taglines('ates parcasi')
    data = parser.parse(page)['data']
    assert 'taglines' not in data
