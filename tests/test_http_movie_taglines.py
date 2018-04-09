def test_movie_taglines_if_single_should_be_a_list_of_phrases(ia):
    movie = ia.get_movie('0063850', info=['taglines'])  # If....
    taglines = movie.get('taglines', [])
    assert taglines == ['Which side will you be on?']


def test_movie_taglines_if_multiple_should_be_a_list_of_phrases(ia):
    movie = ia.get_movie('0060666', info=['taglines'])  # Manos
    taglines = movie.get('taglines', [])
    assert len(taglines) == 3
    assert taglines[0] == "It's Shocking! It's Beyond Your Imagination!"


def test_movie_taglines_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['taglines'])  # Ates Parcasi
    assert 'taglines' not in movie
