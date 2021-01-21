from pytest import mark


def test_series_episodes_should_be_a_map_of_seasons_and_episodes(ia):
    movie = ia.get_movie('0412142', info=['episodes'])      # House M.D.
    assert list(sorted(movie.get('episodes'))) == list(range(1, 9))


def test_series_episodes_with_unknown_season_should_have_placeholder_at_end(ia):
    movie = ia.get_movie('0436992', info=['episodes'])      # Doctor Who
    assert list(sorted(movie.get('episodes'))) == [-1] + list(range(1, 14))


@mark.skip('episodes is {} instead of None')
def test_series_episodes_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1000252', info=['episodes'])      # Doctor Who - Blink
    assert 'episodes' not in movie


def test_series_episodes_should_contain_rating_and_votes(ia):
    movie = ia.get_movie('0185906', info=['episodes'])      # Band of Brothers
    episodes = movie.get('episodes')
    rating = episodes[1][1]['rating']
    votes = episodes[1][1]['votes']
    assert 8.3 <= rating <= 9.0
    assert votes > 4400

def test_update_series_seasons_single_int(ia):
    movie = ia.get_movie('0264235')                         # Curb Your Enthusiasm
    ia.update_series_seasons(movie, season_nums=10)
    assert 'episodes' in movie
    assert list(movie['episodes']) == [10]

def test_update_series_seasons_range(ia):
    movie = ia.get_movie('0264235')                         # Curb Your Enthusiasm
    ia.update_series_seasons(movie, season_nums=range(3, 10))
    assert 'episodes' in movie
    assert list(sorted(movie['episodes'])) == list(range(3, 10))

def test_update_series_seasons_list(ia):
    movie = ia.get_movie('0264235')                         # Curb Your Enthusiasm
    ia.update_series_seasons(movie, season_nums=[1, 3, 5])
    assert 'episodes' in movie
    assert list(sorted(movie['episodes'])) == [1, 3, 5]

def test_update_series_seasons_tuple(ia):
    movie = ia.get_movie('0264235')                         # Curb Your Enthusiasm
    ia.update_series_seasons(movie, season_nums=(1, 3, 5))
    assert 'episodes' in movie
    assert list(sorted(movie['episodes'])) == [1, 3, 5]

def test_update_series_seasons_set(ia):
    movie = ia.get_movie('0264235')                         # Curb Your Enthusiasm
    ia.update_series_seasons(movie, season_nums={1, 3, 5})
    assert 'episodes' in movie
    assert list(sorted(movie['episodes'])) == [1, 3, 5]

def test_update_series_seasons_iterable(ia):
    movie = ia.get_movie('0264235')                         # Curb Your Enthusiasm
    ia.update_series_seasons(movie, season_nums=(i for i in range(6) if i % 2))
    assert 'episodes' in movie
    assert list(sorted(movie['episodes'])) == [1, 3, 5]

def test_update_series_seasons_less_season_available(ia):
    movie = ia.get_movie('0185906')                         # Band of Brothers
    # Only 1 season but request 9
    ia.update_series_seasons(movie, season_nums=range(1, 10))
    assert 'episodes' in movie
    assert list(movie['episodes']) == [1]
