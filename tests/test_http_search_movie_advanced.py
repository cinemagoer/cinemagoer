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


def test_selected_movie_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['kind'] == 'movie'


def test_selected_video_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0295432'][0]
    assert selected['kind'] == 'video movie'


def test_selected_tv_movie_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '4151794'][0]
    assert selected['kind'] == 'tv movie'


def test_selected_tv_short_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0274085'][0]
    assert selected['kind'] == 'tv short movie'


def test_selected_tv_series_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0106062'][0]
    assert selected['kind'] == 'tv series'


def test_selected_ended_tv_series_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0364888'][0]
    assert selected['kind'] == 'tv series'


# def test_selected_tv_episode_should_have_correct_kind(ia):
#     movies = ia.search_movie_advanced('matrix', results=250)
#     selected = [m for m in movies if m.movieID == '0594932'][0]
#     assert selected['kind'] == 'episode'


def test_selected_tv_special_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '1025014'][0]
    assert selected['kind'] == 'tv special'


def test_selected_video_game_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0277828'][0]
    assert selected['kind'] == 'video game'


def test_selected_movie_should_have_correct_year(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['year'] == 1999


def test_selected_ended_tv_series_should_have_correct_end_year(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0364888'][0]
    assert selected['end_year'] == 2004


def test_selected_unreleased_movie_should_have_correct_state(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '5359784'][0]
    assert selected['state'] == 'Completed'


def test_selected_movie_should_have_correct_certification(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['certificates'] == ['R']


def test_selected_movie_should_have_correct_runtime(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['runtimes'] == ['136']


def test_selected_work_should_have_correct_genres(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['genres'] == ['Action', 'Sci-Fi']


def test_selected_movie_should_have_cover_url(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['cover url'].endswith('.jpg')
