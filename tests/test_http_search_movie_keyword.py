def test_get_keyword_should_list_correct_number_of_movies(ia):
    movies = ia.get_keyword('colander')
    assert len(movies) == 6


def test_get_keyword_if_too_many_should_list_upper_limit_of_movies(ia):
    movies = ia.get_keyword('computer')
    assert len(movies) == 50


def test_get_keyword_entries_should_include_movie_id(ia):
    movies = ia.get_keyword('colander')
    assert movies[0].movieID == '0382932'


def test_get_keyword_entries_should_include_movie_title(ia):
    movies = ia.get_keyword('colander')
    assert movies[0]['title'] == 'Ratatouille'


def test_get_keyword_entries_should_include_movie_kind(ia):
    movies = ia.get_keyword('colander')
    assert movies[0]['kind'] == 'movie'


def test_get_keyword_entries_should_include_movie_year(ia):
    movies = ia.get_keyword('colander')
    assert movies[0]['year'] == 2007
