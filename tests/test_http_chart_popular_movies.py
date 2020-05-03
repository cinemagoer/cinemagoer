def test_popular_movies_chart_should_contain_100_entries(ia):
    chart = ia.get_popular100_movies()
    assert len(chart) == 100


def test_popular_movies_chart_entries_should_have_rank(ia):
    movies = ia.get_popular100_movies()
    for rank, movie in enumerate(movies):
        assert movie['popular movies 100 rank'] == rank + 1


def test_popular_movies_chart_entries_should_have_movie_id(ia):
    movies = ia.get_popular100_movies()
    for movie in movies:
        assert movie.movieID.isdigit()


def test_popular_movies_chart_entries_should_have_title(ia):
    movies = ia.get_popular100_movies()
    for movie in movies:
        assert 'title' in movie


def test_popular_movies_chart_entries_should_be_movies(ia):
    movies = ia.get_popular100_movies()
    for movie in movies:
        assert movie['kind'] == 'movie'

