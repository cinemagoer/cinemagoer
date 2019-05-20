import re


def test_person_headshot_should_be_an_image_link(ia):
    person = ia.get_person('0000206', info=['main'])    # Keanu Reeves
    assert re.match(r'^https?://.*\.jpg$', person['headshot'])


def test_person_headshot_if_none_should_be_excluded(ia):
    person = ia.get_person('0330139', info=['main'])    # Deni Gordon
    assert 'headshot' not in person


def test_person_name_should_not_be_canonicalized(ia):
    person = ia.get_person('0000206', info=['main'])    # Keanu Reeves
    assert person.get('name') == 'Keanu Reeves'


def test_person_name_should_not_have_birth_and_death_years(ia):
    person = ia.get_person('0000001', info=['main'])    # Fred Astaire
    assert person.get('name') == 'Fred Astaire'


def test_person_imdb_index_should_be_a_roman_number(ia):
    person = ia.get_person('0000210', info=['main'])    # Julia Roberts
    assert person.get('imdbIndex') == 'I'


def test_person_imdb_index_if_none_should_be_excluded(ia):
    person = ia.get_person('0000206', info=['main'])    # Keanu Reeves
    assert 'imdbIndex' not in person
