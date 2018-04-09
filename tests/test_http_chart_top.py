from pytest import mark


def test_top_chart_should_contain_250_movies(ia):
    data = ia.get_top250_movies()
    assert len(data) == 250


def test_top_chart_all_movies_should_have_rating_and_votes(ia):
    data = ia.get_top250_movies()
    for movie in data:
        assert {'top 250 rank', 'title', 'kind', 'year', 'rating', 'votes'}.issubset(set(movie.keys()))


def test_top_chart_ranks_should_proceed_in_order(ia):
    data = ia.get_top250_movies()
    ranks = [m['top 250 rank'] for m in data]
    assert ranks == list(range(1, 251))


def test_top_chart_should_contain_matrix(ia):
    data = ia.get_top250_movies()
    movieIDs = [m.movieID for m in data]
    assert '0133093' in movieIDs


@mark.fragile
def test_top_chart_shawshank_should_be_top_movie(ia):
    data = ia.get_top250_movies()
    assert data[0].movieID == '0111161'
    assert data[0]['title'] == 'The Shawshank Redemption'
    assert data[0]['kind'] == 'movie'
    assert data[0]['year'] == 1994
    assert data[0]['rating'] > 9
    assert data[0]['votes'] > 1900000
