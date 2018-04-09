from pytest import mark

from imdb.Movie import Movie


chart_keys = {'bottom 100 rank', 'title', 'kind', 'year', 'rating', 'votes'}


def test_bottom_chart_should_contain_100_entries(ia):
    chart = ia.get_bottom100_movies()
    assert len(chart) == 100


def test_bottom_chart_all_entries_should_be_movies(ia):
    chart = ia.get_bottom100_movies()
    for movie in chart:
        assert isinstance(movie, Movie)


def test_bottom_chart_all_movies_should_have_movie_ids(ia):
    chart = ia.get_bottom100_movies()
    for movie in chart:
        assert hasattr(movie, 'movieID')


def test_bottom_chart_all_movies_should_have_same_keys(ia):
    chart = ia.get_bottom100_movies()
    for movie in chart:
        assert chart_keys.issubset(set(movie.keys()))


def test_bottom_chart_ranks_should_proceed_in_order(ia):
    chart = ia.get_bottom100_movies()
    ranks = [m['bottom 100 rank'] for m in chart]
    assert ranks == list(range(1, 101))


def test_bottom_chart_should_contain_manos(ia):
    chart = ia.get_bottom100_movies()
    movieIDs = [m.movieID for m in chart]
    assert '0060666' in movieIDs


@mark.fragile
def test_bottom_chart_koz_should_be_bottom_movie(ia):
    movie = ia.get_bottom100_movies()[0]
    assert movie.movieID == '4458206'
    assert movie['title'] == 'Code Name: K.O.Z.'
    assert movie['kind'] == 'movie'
    assert movie['year'] == 2015
    assert movie['rating'] < 1.6
    assert movie['votes'] > 25000
