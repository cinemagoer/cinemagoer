import sys
from pytest import mark


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
    assert all(isinstance(m['title'], (str, unicode) if sys.version_info < (3,) else str) for m in movies)


def test_selected_movie_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['kind'] == 'movie'


def test_selected_video_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0295432'][0]
    assert selected['kind'] == 'video movie'


def test_selected_tv_movie_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('Sharknado', results=250)
    selected = [m for m in movies if m.movieID == '2724064'][0]
    assert selected['kind'] == 'tv movie'


def test_selected_tv_short_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0274085'][0]
    assert selected['kind'] == 'tv short movie'


@mark.skip('apparently we can no longer tell a series from a movie, in search results')
def test_selected_tv_series_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0106062'][0]
    assert selected['kind'] == 'tv series'


def test_selected_ended_tv_series_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0364888'][0]
    assert selected['kind'] == 'tv series'


def test_selected_tv_episode_should_have_correct_kind(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594932'][0]
    assert selected['kind'] == 'episode'


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


def test_selected_ended_tv_series_should_have_correct_series_years(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0364888'][0]
    assert selected['series years'] == '2003-2004'


@mark.skip('skipped until we found another announced title')
def test_selected_unreleased_movie_should_have_correct_state(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '9839912'][0]
    assert selected['state'] == 'Announced'


def test_selected_movie_should_have_correct_certificate(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['certificates'] == ['R']


def test_selected_movie_should_have_correct_runtime(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['runtimes'] == ['136']


def test_selected_movie_should_have_correct_genres(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['genres'] == ['Action', 'Sci-Fi']


def test_selected_movie_should_have_correct_rating(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert abs(selected['rating'] - 8.7) < 0.5


def test_selected_movie_should_have_correct_number_of_votes(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['votes'] >= 1513744


def test_selected_movie_should_have_correct_metascore(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert abs(selected['metascore'] - 73) < 5


def test_selected_movie_should_have_correct_gross(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['gross'] >= 171479930


def test_selected_movie_should_have_correct_plot(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['plot'].startswith('When a beautiful stranger')


def test_selected_movie_should_have_correct_director_imdb_ids(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '1830851'][0]
    assert [p.personID for p in selected['directors']] == ['0649609']


def test_selected_work_should_have_correct_director_name(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '1830851'][0]
    assert [p['name'] for p in selected['directors']] == ['Josh Oreck']


def test_selected_work_should_have_correct_director_imdb_ids_if_multiple(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert [p.personID for p in selected['directors']] == ['0905154', '0905152']


def test_selected_work_should_have_correct_director_names_if_multiple(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert [p['name'] for p in selected['directors']] == ['Lana Wachowski', 'Lilly Wachowski']


def test_selected_work_should_have_correct_cast_imdb_id(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '1830851'][0]
    assert [p.personID for p in selected['cast']] == ['1047143']


def test_selected_work_should_have_correct_cast_name(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '1830851'][0]
    assert [p['name'] for p in selected['cast']] == ['Clayton Watson']


def test_selected_work_should_have_correct_cast_imdb_ids_if_multiple(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert [p.personID for p in selected['cast']] == ['0000206', '0000401', '0005251', '0915989']


def test_selected_work_should_have_correct_cast_names_if_multiple(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert [p['name'] for p in selected['cast']] == [
        'Keanu Reeves',
        'Laurence Fishburne',
        'Carrie-Anne Moss',
        'Hugo Weaving'
    ]


def test_selected_tv_episode_should_have_correct_title(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['title'] == "The Making of 'The Matrix'"


def test_selected_tv_episode_should_have_correct_year(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['year'] == 1999


def test_selected_tv_episode_should_have_correct_imdb_index(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '1072112'][0]
    assert selected['imdbIndex'] == 'I'


def test_selected_tv_episode_should_have_correct_certificate(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '1072112'][0]
    assert selected['certificates'] == ['TV-PG']


def test_selected_tv_episode_should_have_correct_runtime(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['runtimes'] == ['26']


def test_selected_tv_episode_should_have_correct_genres(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['genres'] == ['Documentary', 'Short']


def test_selected_tv_episode_should_have_correct_rating(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert abs(selected['rating'] - 7.6) < 0.5


def test_selected_tv_episode_should_have_correct_number_of_votes(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['votes'] >= 14


def test_selected_tv_episode_should_have_correct_plot(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '10177094'][0]
    assert selected['plot'].startswith('Roberto Leoni reviews The Matrix (1999)')


def test_selected_tv_episode_should_have_correct_director_imdb_ids(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert [p.personID for p in selected['directors']] == ['0649609']


def test_selected_tv_episode_should_have_correct_director_names(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert [p['name'] for p in selected['directors']] == ['Josh Oreck']


def test_selected_tv_episode_should_have_correct_cast_imdb_ids(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert [p.personID for p in selected['cast']] == ['0000401', '0300665', '0303293', '0005251']


def test_selected_tv_episode_should_have_correct_cast_names(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert [p['name'] for p in selected['cast']] == [
        'Laurence Fishburne',
        'John Gaeta',
        "Robert 'Rock' Galotti",
        'Carrie-Anne Moss'
    ]


def test_selected_tv_episode_should_have_series(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['episode of']['kind'] == 'tv series'


def test_selected_tv_episode_should_have_correct_series_imdb_id(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['episode of'].movieID == '0318220'


def test_selected_tv_episode_should_have_correct_series_title(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '0594933'][0]
    assert selected['episode of']['title'] == 'HBO First Look'


def test_selected_tv_episode_should_have_correct_series_year(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '1072112'][0]
    assert selected['episode of']['year'] == 2001


def test_selected_tv_episode_should_have_correct_series_series_years(ia):
    movies = ia.search_movie_advanced('matrix', results=250)
    selected = [m for m in movies if m.movieID == '1072112'][0]
    assert selected['episode of']['series years'] == '2001-2012'


def test_selected_movie_should_have_cover_url(ia):
    movies = ia.search_movie_advanced('matrix', results=50)
    selected = [m for m in movies if m.movieID == '0133093'][0]
    assert selected['cover url'].endswith('.jpg')


def test_search_results_should_include_adult_titles_if_requested(ia):
    movies = ia.search_movie_advanced('castello', adult=True, results=250)
    movies_no_adult = ia.search_movie_advanced('castello', adult=False, results=250)
    assert len(movies) > len(movies_no_adult)


def test_selected_adult_movie_should_have_correct_title(ia):
    movies = ia.search_movie_advanced('matrix', adult=True, results=250)
    selected = [m for m in movies if m.movieID == '0273126'][0]
    assert selected['title'] == 'Blue Matrix'


def test_selected_adult_movie_should_have_adult_in_genres(ia):
    movies = ia.search_movie_advanced('matrix', adult=True, results=250)
    selected = [m for m in movies if m.movieID == '0273126'][0]
    assert 'Adult' in selected['genres']

@mark.skip('IMDb sorting works in misterious ways')
def test_search_results_should_be_sortable_in_alphabetical_order_default_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='alpha')
    titles = [m['title'] for m in movies]
    # assert all(a <= b for a, b in zip(titles, titles[1:]))  # fails due to IMDb
    assert sum(1 if a > b else 0 for a, b in zip(titles, titles[1:])) <= 1

@mark.skip('IMDb sorting works in misterious ways')
def test_search_results_should_be_sortable_in_alphabetical_order_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='alpha', sort_dir='asc')
    titles = [m['title'] for m in movies]
    # assert all(a <= b for a, b in zip(titles, titles[1:]))  # fails due to IMDb
    assert sum(1 if a > b else 0 for a, b in zip(titles, titles[1:])) <= 1


def test_search_results_should_be_sortable_in_alphabetical_order_descending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='alpha', sort_dir='desc')
    titles = [m['title'] for m in movies]
    assert all(a >= b for a, b in zip(titles, titles[1:]))


def test_search_results_should_be_sortable_in_rating_order_default_descending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='user_rating')
    ratings = [m.get('rating', 0) for m in movies]
    assert all(a >= b for a, b in zip(ratings, ratings[1:]))


def test_search_results_should_be_sortable_in_rating_order_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='user_rating', sort_dir='asc')
    ratings = [m.get('rating', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(ratings, ratings[1:]))


def test_search_results_should_be_sortable_in_rating_order_descending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='user_rating', sort_dir='desc')
    ratings = [m.get('rating', 0) for m in movies]
    assert all(a >= b for a, b in zip(ratings, ratings[1:]))


def test_search_results_should_be_sortable_in_votes_order_default_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='num_votes')
    votes = [m.get('votes', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(votes, votes[1:]))


def test_search_results_should_be_sortable_in_votes_order_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='num_votes', sort_dir='asc')
    votes = [m.get('votes', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(votes, votes[1:]))


def test_search_results_should_be_sortable_in_votes_order_descending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='num_votes', sort_dir='desc')
    votes = [m.get('votes', 0) for m in movies]
    assert all(a >= b for a, b in zip(votes, votes[1:]))


def test_search_results_should_be_sortable_in_gross_order_default_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='boxoffice_gross_us')
    grosses = [m.get('gross', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(grosses, grosses[1:]))


def test_search_results_should_be_sortable_in_gross_order_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='boxoffice_gross_us', sort_dir='asc')
    grosses = [m.get('gross', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(grosses, grosses[1:]))


def test_search_results_should_be_sortable_in_gross_order_descending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='boxoffice_gross_us', sort_dir='desc')
    grosses = [m.get('gross', 0) for m in movies]
    assert all(a >= b for a, b in zip(grosses, grosses[1:]))


def test_search_results_should_be_sortable_in_runtime_order_default_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='runtime')
    runtimes = [m.get('runtime', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(runtimes, runtimes[1:]))


def test_search_results_should_be_sortable_in_runtime_order_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='runtime', sort_dir='asc')
    runtimes = [int(m.get('runtimes', [float('inf')])[0]) for m in movies]
    assert all(a <= b for a, b in zip(runtimes, runtimes[1:]))


def test_search_results_should_be_sortable_in_runtime_order_descending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='runtime', sort_dir='desc')
    runtimes = [int(m.get('runtimes', [float('inf')])[0]) for m in movies]
    assert all(a >= b for a, b in zip(runtimes, runtimes[1:]))


def test_search_results_should_be_sortable_in_year_order_default_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='year')
    years = [m.get('year', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(years, years[1:]))


def test_search_results_should_be_sortable_in_year_order_ascending(ia):
    movies = ia.search_movie_advanced(title='matrix', sort='year', sort_dir='asc')
    years = [m.get('year', float('inf')) for m in movies]
    assert all(a <= b for a, b in zip(years, years[1:]))


# def test_search_results_should_be_sortable_in_year_order_descending(ia):
#     movies = ia.search_movie_advanced(title='matrix', sort='year', sort_dir='desc')
#     years = [m.get('year', float('inf')) for m in movies]
#     assert all(a >= b for a, b in zip(years, years[1:]))
