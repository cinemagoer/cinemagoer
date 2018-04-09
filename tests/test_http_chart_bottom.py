def test_bottom_chart_should_contain_100_movies(ia):
    data = ia.get_bottom100_movies()
    assert len(data) == 100


def test_bottom_chart_all_movies_should_have_rating_and_votes(ia):
    data = ia.get_bottom100_movies()
    for movie in data:
        assert {'title', 'kind', 'year', 'rating', 'votes'}.issubset(set(movie.keys()))


def test_bottom_chart_should_contain_manos(ia):
    data = ia.get_bottom100_movies()
    movieIDs = [m.movieID for m in data]
    assert '0060666' in movieIDs
