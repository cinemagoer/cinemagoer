def test_search_results_should_include_correct_number_of_works_by_default(ia):
    movies = ia.search_movie_advanced('matrix')
    assert len(movies) == 20


def test_search_results_should_include_correct_number_of_works(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    assert len(movies) > 220


def test_search_results_should_include_correct_number_of_works_if_asked_less_than_available(ia):
    movies = ia.search_movie_advanced('matrix', results=25)
    assert len(movies) == 25


def test_found_movies_should_have_movie_ids(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    assert all(isinstance(m.movieID, str) for m in movies)


def test_found_movies_should_have_titles(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    assert all(isinstance(m['title'], str) for m in movies)


def test_selected_movie_should_have_cover_url(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['cover url'].endswith(".jpg")
