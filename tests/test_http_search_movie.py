def test_search_movie_if_single_should_list_one_movie(ia):
    movies = ia.search_movie('od instituta do proizvodnje')
    assert len(movies) == 1
    assert movies[0].movieID == '0483758'
    assert movies[0]['kind'] == 'short'
    assert movies[0]['title'] == 'Od instituta do proizvodnje'
    assert movies[0]['year'] == 1971


def test_search_movie_should_list_default_number_of_movies(ia):
    movies = ia.search_movie('movie')
    assert len(movies) == 20


def test_search_movie_limited_should_list_requested_number_of_movies(ia):
    movies = ia.search_movie('ace in the hole', results=98)
    assert len(movies) == 98


def test_search_movie_unlimited_should_list_correct_number_of_movies(ia):
    movies = ia.search_movie('ace in the hole', results=500)
    assert 185 <= len(movies) <= 200


def test_search_movie_if_too_many_result_should_list_upper_limit_of_movies(ia):
    movies = ia.search_movie('matrix', results=500)
    assert len(movies) == 200


def test_search_movie_should_contain_correct_movie(ia):
    movies = ia.search_movie('matrix', results=500)
    movie = [m for m in movies if m.movieID == '0133093']
    assert len(movie) == 1
    assert movie[0]['title'] == 'The Matrix'
    assert movie[0]['kind'] == 'movie'
    assert movie[0]['year'] == 1999


def test_search_movie_found_movie_should_have_kind(ia):
    movies = ia.search_movie('matrix', results=500)
    movie = [m for m in movies if m.movieID == '0106062']
    assert len(movie) == 1
    assert movie[0]['title'] == 'Matrix'
    assert movie[0]['kind'] == 'tv series'
    assert movie[0]['year'] == 1993


def test_search_movie_found_movie_should_have_imdb_index(ia):
    movies = ia.search_movie('blink', results=500)
    movie = [m for m in movies if m.movieID == '4790262']
    assert len(movie) == 1
    assert movie[0]['title'] == 'Blink'
    assert movie[0]['imdbIndex'] == 'IV'
    assert movie[0]['kind'] == 'movie'
    assert movie[0]['year'] == 2015


def test_search_movie_if_none_should_be_empty(ia):
    movies = ia.search_movie('%e3%82%a2', results=500)
    assert movies == []
