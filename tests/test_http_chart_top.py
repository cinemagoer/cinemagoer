def test_top_chart_should_contain_250_entries(ia):
    chart = ia.get_top250_movies()
    assert len(chart) == 250


def test_top_chart_entries_should_have_rank(ia):
    movies = ia.get_top250_movies()
    for rank, movie in enumerate(movies):
        assert movie['top 250 rank'] == rank + 1


def test_top_chart_entries_should_have_movie_id(ia):
    movies = ia.get_top250_movies()
    for movie in movies:
        assert movie.movieID.isdigit()


def test_top_chart_entries_should_have_title(ia):
    movies = ia.get_top250_movies()
    for movie in movies:
        assert 'title' in movie


def test_top_chart_entries_should_be_movies(ia):
    movies = ia.get_top250_movies()
    for movie in movies:
        assert movie['kind'] == 'movie'


def test_top_chart_entries_should_have_year(ia):
    movies = ia.get_top250_movies()
    for movie in movies:
        assert isinstance(movie['year'], int)


def test_top_chart_entries_should_have_high_ratings(ia):
    movies = ia.get_top250_movies()
    for movie in movies:
        assert movie['rating'] > 7.5


def test_top_chart_entries_should_have_minimal_number_of_votes(ia):
    movies = ia.get_top250_movies()
    for movie in movies:
        assert movie['votes'] >= 25000  # limit stated by IMDb
