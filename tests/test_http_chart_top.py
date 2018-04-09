from imdb.Movie import Movie


chart_keys = {'top 250 rank', 'title', 'kind', 'year', 'rating', 'votes'}


def test_top_chart_should_contain_250_entries(ia):
    chart = ia.get_top250_movies()
    assert len(chart) == 250


def test_top_chart_all_entries_should_be_movies(ia):
    chart = ia.get_top250_movies()
    for movie in chart:
        assert isinstance(movie, Movie)


def test_top_chart_all_movies_should_have_movie_ids(ia):
    chart = ia.get_top250_movies()
    for movie in chart:
        assert hasattr(movie, 'movieID')


def test_top_chart_all_movies_should_have_same_keys(ia):
    chart = ia.get_top250_movies()
    for movie in chart:
        assert chart_keys.issubset(set(movie.keys()))


def test_top_chart_ranks_should_proceed_in_order(ia):
    chart = ia.get_top250_movies()
    ranks = [m['top 250 rank'] for m in chart]
    assert ranks == list(range(1, 251))


def test_top_chart_should_contain_matrix(ia):
    chart = ia.get_top250_movies()
    movieIDs = [m.movieID for m in chart]
    assert '0133093' in movieIDs


def test_top_chart_shawshank_should_be_top_movie(ia):
    movie = ia.get_top250_movies()[0]
    assert movie.movieID == '0111161'
    assert movie['title'] == 'The Shawshank Redemption'
    assert movie['kind'] == 'movie'
    assert movie['year'] == 1994
    assert movie['rating'] > 9
    assert movie['votes'] > 1900000
