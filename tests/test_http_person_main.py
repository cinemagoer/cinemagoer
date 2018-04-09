import re


def test_headshot_should_be_an_image_link(ia):
    data = ia.get_person('0000206', info=['main'])     # Keanu Reeves
    assert re.match(r'^https?://.*\.jpg$', data['headshot'])


def test_headshot_none_should_be_excluded(ia):
    data = ia.get_person('0330139', info=['main'])     # Deni Gordon
    assert 'headshot' not in data


def test_name_should_not_be_canonical(ia):
    data = ia.get_person('0000206', info=['main'])     # Keanu Reeves
    # XXX: inconsistent with bio page parser
    assert data['name'] == 'Keanu Reeves'


def test_name_should_not_have_year(ia):
    data = ia.get_person('0000001', info=['main'])     # Fred Astaire
    # XXX: inconsistent with bio page parser
    assert data['name'] == 'Fred Astaire'


def test_imdb_index_should_be_a_roman_number(ia):
    data = ia.get_person('0000210', info=['main'])     # Julia Roberts
    assert data['imdbIndex'] == 'I'


def test_imdb_index_none_should_be_excluded(ia):
    data = ia.get_person('0000206', info=['main'])     # Keanu Reeves
    assert 'imdbIndex' not in data
