from pytest import mark


def test_series_episodes_should_be_a_map_of_seasons_and_episodes(ia):
    movie = ia.get_movie('0412142', info=['episodes'])      # House M.D.
    assert list(sorted(movie.get('episodes'))) == list(range(1, 9))


def test_series_episodes_with_unknown_season_should_have_placeholder_at_end(ia):
    movie = ia.get_movie('0436992', info=['episodes'])      # Doctor Who
    assert list(sorted(movie.get('episodes'))) == [-1] + list(range(1, 13))


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
