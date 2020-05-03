def test_popular_tv_should_contain_100_entries(ia):
    chart = ia.get_popular100_tv()
    assert len(chart) == 100


def test_popular_tv_entries_should_have_rank(ia):
    movies = ia.get_popular100_tv()
    for rank, movie in enumerate(movies):
        assert movie['popular tv 100 rank'] == rank + 1


def test_popular_tv_entries_should_have_movie_id(ia):
    movies = ia.get_popular100_tv()
    for movie in movies:
        assert movie.movieID.isdigit()


def test_popular_tv_entries_should_have_title(ia):
    movies = ia.get_popular100_tv()
    for movie in movies:
        assert 'title' in movie


def test_popular_tv_entries_should_have_year(ia):
    movies = ia.get_popular100_tv()
    for movie in movies:
        assert isinstance(movie['year'], int)

