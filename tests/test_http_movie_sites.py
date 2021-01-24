def test_movie_official_sites_should_be_a_list(ia):
    movie = ia.get_movie('0133093', info=['official sites'])    # Matrix
    official_sites = movie.get('official sites', [])
    assert len(official_sites) == 3


def test_movie_official_sites_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['official sites'])    # Ates Parcasi
    assert 'official sites' not in movie


def test_movie_sound_clips_should_be_a_list(ia):
    movie = ia.get_movie('0133093', info=['official sites'])    # Matrix
    sound_clips = movie.get('sound clips', [])
    assert len(sound_clips) == 3


def test_movie_sound_clips_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['official sites'])    # Ates Parcasi
    assert 'sound clips' not in movie
