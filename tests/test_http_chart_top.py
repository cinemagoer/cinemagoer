def test_top_chart_should_contain_250_entries(ia):
    chart = ia.get_top250_movies()
    assert len(chart) == 250


def test_top_chart_entries_should_have_rank(ia):
    movies = ia.get_top250_movies()
    assert movies[0]['top 250 rank'] == 1


def test_top_chart_entries_should_have_movie_id(ia):
    movies = ia.get_top250_movies()
    assert movies[0].movieID == '0111161'


def test_top_chart_entries_should_have_title(ia):
    movies = ia.get_top250_movies()
    assert movies[0]['title'] == 'The Shawshank Redemption'


def test_top_chart_entries_should_have_kind(ia):
    movies = ia.get_top250_movies()
    assert movies[0]['kind'] == 'movie'


def test_top_chart_entries_should_have_year(ia):
    movies = ia.get_top250_movies()
    assert movies[0]['year'] == 1994


def test_top_chart_entries_should_have_rating(ia):
    movies = ia.get_top250_movies()
    assert movies[0]['rating'] > 9


def test_top_chart_entries_should_have_votes(ia):
    movies = ia.get_top250_movies()
    assert movies[0]['votes'] > 1900000
