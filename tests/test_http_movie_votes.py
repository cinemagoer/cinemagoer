from pytest import fixture

from urllib.request import urlopen

from imdb.parser.http.movieParser import DOMHTMLRatingsParser


@fixture(scope='module')
def movie_ratings(movies):
    """A function to retrieve the ratings page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/ratings'
        return urlopen(url).read().decode('utf-8')
    return retrieve


parser = DOMHTMLRatingsParser()


def test_movie_ratings_nr_votes_must_be_10(movie_ratings):
    page = movie_ratings('matrix')
    data = parser.parse(page)['data']
    assert len(data['number of votes']) == 10

def test_movie_ratings_nr_votes_must_integer(movie_ratings):
    page = movie_ratings('matrix')
    data = parser.parse(page)['data']
    assert isinstance(data['number of votes'][10],  int)

def test_movie_ratings_median_must_integer(movie_ratings):
    page = movie_ratings('matrix')
    data = parser.parse(page)['data']
    assert isinstance(data['median'],  int)

def test_movie_ratings_mean_must_numeric(movie_ratings):
    page = movie_ratings('matrix')
    data = parser.parse(page)['data']
    assert isinstance(data['arithmetic mean'],  float)

def test_movie_ratings_demographics_must_19(movie_ratings):
    page = movie_ratings('matrix')
    data = parser.parse(page)['data']
    assert len(data['demographics']) == 19

def test_movie_ratings_demographics_must_numeric(movie_ratings):
    page = movie_ratings('matrix')
    data = parser.parse(page)['data']
    top1000 = data['demographics']['top 1000 voters']
    assert isinstance(top1000['votes'],  int)
    assert isinstance(top1000['rating'],  float)
