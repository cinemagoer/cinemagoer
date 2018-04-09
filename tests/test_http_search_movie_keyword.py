def test_get_keyword_should_list_correct_number_of_movies(ia):
    movies = ia.get_keyword('colander')
    assert len(movies) == 4


def test_get_keyword_if_too_many_should_list_upper_limit_of_movies(ia):
    movies = ia.get_keyword('computer')
    assert len(movies) == 50


def test_get_keyword_should_contain_correct_movie(ia):
    movies = ia.get_keyword('colander')
    movie = [m for m in movies if m.movieID == '0382932']
    assert len(movie) == 1
    assert movie[0]['title'] == 'Ratatouille'
    assert movie[0]['kind'] == 'movie'
    assert movie[0]['year'] == 2007
