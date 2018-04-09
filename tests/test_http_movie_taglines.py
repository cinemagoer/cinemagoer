def test_movie_taglines_single_should_be_a_list_of_phrases(ia):
    data = ia.get_movie('0063850', info=['taglines'])   # If....
    assert data['taglines'] == ['Which side will you be on?']


def test_movie_taglines_multiple_should_be_a_list_of_phrases(ia):
    data = ia.get_movie('0060666', info=['taglines'])   # Manos
    assert len(data['taglines']) == 3
    assert data['taglines'][0] == "It's Shocking! It's Beyond Your Imagination!"


def test_summary_none_should_be_excluded(ia):
    data = ia.get_movie('1863157', info=['taglines'])   # Ates Parcasi
    assert 'taglines' not in data
