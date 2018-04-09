def test_chart_should_contain_250_movies(ia):
    data = ia.get_top250_movies()
    assert len(data) == 250


def test_all_movies_should_have_rating_and_votes(ia):
    data = ia.get_top250_movies()
    for movie in data:
        assert {'title', 'kind', 'year', 'rating', 'votes'}.issubset(set(movie.keys()))


def test_ranks_should_proceed_in_order(ia):
    data = ia.get_top250_movies()
    ranks = [m['top 250 rank'] for m in data]
    assert ranks == list(range(1, 251))


def test_chart_should_contain_matrix(ia):
    data = ia.get_top250_movies()
    movieIDs = [m.movieID for m in data]
    assert '0133093' in movieIDs


def test_shawshank_should_be_top_movie(ia):
    data = ia.get_top250_movies()
    top_movie = data[0]
    assert top_movie.movieID == '0111161'
    assert top_movie['title'] == 'The Shawshank Redemption'
    assert top_movie['year'] == 1994
    assert top_movie['rating'] > 9
    assert top_movie['votes'] > 1900000
