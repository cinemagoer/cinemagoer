from pytest import mark


def test_found_one_result_should_be_list_with_one_movie(ia):
    data = ia.search_movie('od instituta do proizvodnje')
    # XXX: returns empty list if results = -1
    assert len(data) == 1
    assert data[0].movieID == '0483758'
    assert data[0]['kind'] == 'short'
    assert data[0]['title'] == 'Od instituta do proizvodnje'
    assert data[0]['year'] == 1971


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_movies(ia):
    data = ia.search_movie('ace in the hole', results=-1)
    assert 185 < len(data) < 200


def test_found_too_many_result_should_contain_upper_limit_of_movies(ia):
    data = ia.search_movie('matrix', results=-1)
    # XXX: there's something wrong here
    assert len(data) == 199


def test_found_many_result_should_contain_correct_movie(ia):
    data = ia.search_movie('matrix', results=-1)
    movie = [m for m in data if m.movieID == '0133093']
    assert len(movie) == 1
    assert movie[0]['title'] == 'The Matrix'
    assert movie[0]['kind'] == 'movie'
    assert movie[0]['year'] == 1999


def test_found_movie_should_have_kind(ia):
    data = ia.search_movie('matrix', results=-1)
    movie = [m for m in data if m.movieID == '0106062']
    assert len(movie) == 1
    assert movie[0]['title'] == 'Matrix'
    assert movie[0]['kind'] == 'tv series'
    assert movie[0]['year'] == 1993


def test_found_movie_should_have_imdb_index(ia):
    data = ia.search_movie('blink', results=-1)
    movie = [m for m in data if m.movieID == '4790262']
    assert len(movie) == 1
    assert movie[0]['title'] == 'Blink'
    assert movie[0]['imdbIndex'] == 'IV'
    assert movie[0]['kind'] == 'movie'
    assert movie[0]['year'] == 2015


def test_found_none_result_should_be_empty(ia):
    data = ia.search_movie('%e3%82%a2', results=-1)
    assert data == []
