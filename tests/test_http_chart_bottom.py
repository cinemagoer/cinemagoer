def test_bottom_chart_should_contain_100_entries(ia):
    chart = ia.get_bottom100_movies()
    assert len(chart) == 100


def test_bottom_chart_entries_should_have_rank(ia):
    movies = ia.get_bottom100_movies()
    for rank, movie in enumerate(movies):
        assert movie['bottom 100 rank'] == rank + 1


def test_bottom_chart_entries_should_have_movie_id(ia):
    movies = ia.get_bottom100_movies()
    for movie in movies:
        assert movie.movieID.isdigit()


def test_bottom_chart_entries_should_have_title(ia):
    movies = ia.get_bottom100_movies()
    for movie in movies:
        assert 'title' in movie


def test_bottom_chart_entries_should_be_movies(ia):
    movies = ia.get_bottom100_movies()
    for movie in movies:
        assert movie['kind'] == 'movie'


def test_bottom_chart_entries_should_have_year(ia):
    movies = ia.get_bottom100_movies()
    for movie in movies:
        assert isinstance(movie['year'], int)


def test_bottom_chart_entries_should_have_low_ratings(ia):
    movies = ia.get_bottom100_movies()
    for movie in movies:
        assert movie['rating'] < 5.0


def test_bottom_chart_entries_should_have_minimal_number_of_votes(ia):
    movies = ia.get_bottom100_movies()
    for movie in movies:
        assert movie['votes'] >= 1500  # limit stated by IMDb
