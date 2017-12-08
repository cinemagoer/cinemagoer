from pytest import fixture

from imdb.parser.http.movieParser import DOMHTMLReviewsParser


@fixture(scope='module')
def movie_reviews_details(url_opener, movies):
    """A function to retrieve the reviews details page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/reviews'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLReviewsParser()


def test_number_of_reviews(movie_reviews_details):
    page = movie_reviews_details('dust devil')
    data = parser.parse(page)['data']
    reviews_number = len(data.get('reviews', []))
    assert(reviews_number == 10)

