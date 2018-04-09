from pytest import mark


@mark.skip('no method for searching movie by keyword')
def test_found_many_result_should_contain_correct_number_of_movies(ia):
    data = ia.search_movie_by_keyword('colander')
    assert len(data) == 4


@mark.skip('no method for searching movie by keyword')
def test_found_too_many_result_should_contain_50_movies(ia):
    data = ia.search_movie_by_keyword('computer')
    assert len(data) == 50


@mark.skip('no method for searching movie by keyword')
def test_found_many_result_should_contain_correct_movie(ia):
    data = ia.search_movie_by_keyword('colander')
    movie = [m for m in data if m.movieID == '0382932']
    assert len(movie) == 1
    assert movie[0]['title'] == 'Ratatouille'
    assert movie[0]['kind'] == 'movie'
    assert movie[0]['year'] == 2007
