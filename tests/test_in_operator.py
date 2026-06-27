def test_person_in_movie(ia):
    movie = ia.get_movie('1')  # Carmencita
    person = movie['cast'][0]
    assert person in movie


def test_key_in_movie(ia):
    movie = ia.get_movie('9')  # Miss Jerry
    assert 'cast' in movie
    assert 'director' in movie


def test_movie_in_person(ia):
    person = ia.get_person('1')  # Fred Astaire
    movie = person['known for'][0]
    assert movie in person


def test_key_in_person(ia):
    person = ia.get_person('1')  # Fred Astaire
    assert 'known for' in person
    assert 'primary profession' in person
