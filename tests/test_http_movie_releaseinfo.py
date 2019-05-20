def test_movie_release_info_raw_akas_must_be_a_list(ia):
    movie = ia.get_movie('0133093', info=['release info'])    # Matrix
    akas = movie.get('raw akas', [])
    assert len(akas) >= 40
    assert len(akas) == len(movie.get('akas from release info'))


def test_movie_release_info_raw_release_dates_must_be_a_list(ia):
    movie = ia.get_movie('0133093', info=['release info'])    # Matrix
    akas = movie.get('raw release dates', [])
    assert len(akas) >= 56
    assert len(akas) == len(movie.get('release dates'))

