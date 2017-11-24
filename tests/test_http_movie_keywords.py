from pytest import fixture

from urllib.request import urlopen

from imdb.parser.http.movieParser import DOMHTMLKeywordsParser


@fixture(scope='module')
def movie_keywords(movies):
    """A function to retrieve the keywords page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/keywords'
        return urlopen(url).read().decode('utf-8')
    return retrieve


parser = DOMHTMLKeywordsParser()


def test_keywords_multiple_should_be_parsed_correctly(movie_keywords):
    page = movie_keywords('matrix')
    data = parser.parse(page)['data']
    assert {'computer-hacker', 'messiah', 'artificial-reality'}.issubset(set(data['keywords']))


def test_keywords_none_should_be_excluded(movie_keywords):
    page = movie_keywords('ates parcasi')
    data = parser.parse(page)['data']
    assert 'keywords' not in data
