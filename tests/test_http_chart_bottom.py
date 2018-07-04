def test_bottom_chart_should_contain_100_entries(ia):
    chart = ia.get_bottom100_movies()
    assert len(chart) == 100


def test_bottom_chart_entries_should_have_rank(ia):
    movies = ia.get_bottom100_movies()
    assert movies[0]['bottom 100 rank'] == 1


def test_bottom_chart_entries_should_have_movie_id(ia):
    movies = ia.get_bottom100_movies()
    assert movies[0].movieID == '4458206'


def test_bottom_chart_entries_should_have_title(ia):
    movies = ia.get_bottom100_movies()
    assert movies[0]['title'] == 'Code Name: K.O.Z.'


def test_bottom_chart_entries_should_have_kind(ia):
    movies = ia.get_bottom100_movies()
    assert movies[0]['kind'] == 'movie'


def test_bottom_chart_entries_should_have_year(ia):
    movies = ia.get_bottom100_movies()
    assert movies[0]['year'] == 2015


def test_bottom_chart_entries_should_have_rating(ia):
    movies = ia.get_bottom100_movies()
    assert movies[0]['rating'] < 1.6


def test_bottom_chart_entries_should_have_votes(ia):
    movies = ia.get_bottom100_movies()
    assert movies[0]['votes'] > 25000
