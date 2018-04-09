from pytest import mark


def test_bottom_chart_should_contain_100_movies(ia):
    data = ia.get_bottom100_movies()
    assert len(data) == 100


def test_bottom_chart_all_movies_should_have_rating_and_votes(ia):
    data = ia.get_bottom100_movies()
    for movie in data:
        assert {'bottom 100 rank', 'title', 'kind', 'year', 'rating', 'votes'}.issubset(set(movie.keys()))


def test_bottom_chart_ranks_should_proceed_in_order(ia):
    data = ia.get_bottom100_movies()
    ranks = [m['bottom 100 rank'] for m in data]
    assert ranks == list(range(1, 101))


def test_bottom_chart_should_contain_manos(ia):
    data = ia.get_bottom100_movies()
    movieIDs = [m.movieID for m in data]
    assert '0060666' in movieIDs


@mark.fragile
def test_bottom_chart_koz_should_be_bottom_movie(ia):
    data = ia.get_bottom100_movies()
    assert data[0].movieID == '4458206'
    assert data[0]['title'] == 'Code Name: K.O.Z.'
    assert data[0]['kind'] == 'movie'
    assert data[0]['year'] == 2015
    assert data[0]['rating'] < 1.6
    assert data[0]['votes'] > 25000
