def test_movie_ratings_nr_votes_should_be_10(ia):
    data = ia.get_movie('0063850', info=['vote details'])   # Matrix
    assert len(data['number of votes']) == 10


def test_movie_ratings_nr_votes_should_be_integer(ia):
    data = ia.get_movie('0063850', info=['vote details'])   # Matrix
    assert isinstance(data['number of votes'][10], int)


def test_movie_ratings_median_should_integer(ia):
    data = ia.get_movie('0063850', info=['vote details'])   # Matrix
    assert isinstance(data['median'], int)


def test_movie_ratings_mean_should_be_numeric(ia):
    data = ia.get_movie('0063850', info=['vote details'])   # Matrix
    assert isinstance(data['arithmetic mean'], float)


def test_movie_ratings_demographics_should_be_19(ia):
    data = ia.get_movie('0063850', info=['vote details'])   # Matrix
    assert len(data['demographics']) == 19


def test_movie_ratings_demographics_should_be_numeric(ia):
    data = ia.get_movie('0063850', info=['vote details'])   # Matrix
    top1000 = data['demographics']['top 1000 voters']
    assert isinstance(top1000['votes'], int)
    assert isinstance(top1000['rating'], float)
