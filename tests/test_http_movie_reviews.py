from pytest import fixture

from imdb.parser.http.movieParser import DOMHTMLReviewsParser


@fixture(scope='module')
def movie_reviews(url_opener, movies):
    """A function to retrieve the reviews page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/reviews'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLReviewsParser()


def test_number_of_reviews_should_be_correct(movie_reviews):
    page = movie_reviews('dust devil')
    data = parser.parse(page)['data']
    assert len(data.get('reviews', [])) == 25
