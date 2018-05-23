def test_person_in_movie(ia):
    movie = ia.get_movie('0133093', info=['main'])  # Matrix
    person = ia.get_person('0000206', info=['main'])  # Keanu Reeves
    assert person in movie


def test_key_in_movie(ia):
    movie = ia.get_movie('0133093', info=['main'])  # Matrix
    assert 'cast' in movie


def test_movie_in_person(ia):
    movie = ia.get_movie('0133093', info=['main'])  # Matrix
    person = ia.get_person('0000206', info=['main'])  # Keanu Reeves
    assert movie in person


def test_key_in_person(ia):
    person = ia.get_person('0000206')  # Keanu Reeves
    assert 'filmography' in person


def test_key_in_company(ia):
    company = ia.get_company('0017902', info=['main'])  # Pixar
    assert 'name' in company

