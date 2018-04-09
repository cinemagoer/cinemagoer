from pytest import mark


def test_movie_votes_should_be_divided_into_10_slots(ia):
    movie = ia.get_movie('0133093', info=['vote details'])  # Matrix
    votes = movie.get('number of votes', [])
    assert len(votes) == 10


def test_movie_votes_should_be_integers(ia):
    movie = ia.get_movie('0133093', info=['vote details'])  # Matrix
    votes = movie.get('number of votes', [])
    for vote in votes:
        assert isinstance(vote, int)


@mark.fragile
def test_movie_votes_median_should_be_an_integer(ia):
    movie = ia.get_movie('0133093', info=['vote details'])  # Matrix
    median = movie.get('median')
    assert median == 9


@mark.fragile
def test_movie_votes_mean_should_be_numeric(ia):
    movie = ia.get_movie('0133093', info=['vote details'])  # Matrix
    mean = movie.get('arithmetic mean')
    assert 8.5 <= mean <= 9


def test_movie_demographics_should_be_divided_into_19_categories(ia):
    movie = ia.get_movie('0133093', info=['vote details'])  # Matrix
    demographics = movie['demographics']
    assert len(demographics) == 19


def test_movie_demographics_votes_should_be_integers(ia):
    movie = ia.get_movie('0133093', info=['vote details'])  # Matrix
    top1000 = movie['demographics']['top 1000 voters']
    assert isinstance(top1000['votes'], int)
    assert isinstance(top1000['rating'], float)
