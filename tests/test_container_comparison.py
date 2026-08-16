"""Regression tests for https://github.com/cinemagoer/cinemagoer/issues/387

Container.__eq__ must return a real bool and respect the equality
contract (reflexive, symmetric, consistent with total_ordering).
"""

from imdb.Character import Character
from imdb.Company import Company
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import _Container, _last


def test_eq_returns_bool():
    m1 = Movie(movieID='0783644', data={'title': 'Pom Poko', 'year': 1994})
    m2 = Movie(movieID='1321512', data={'title': 'Arrietty', 'year': 2010})
    assert isinstance(m1 == m2, bool)
    assert isinstance(m1 != m2, bool)


def test_eq_is_symmetric():
    m1 = Movie(movieID='0783644', data={'title': 'Pom Poko', 'year': 1994})
    m2 = Movie(movieID='1321512', data={'title': 'Arrietty', 'year': 2010})
    assert (m1 == m2) == (m2 == m1)
    assert m1 != m2
    assert m2 != m1


def test_eq_is_reflexive():
    movie = Movie(movieID='0783644', data={'title': 'Pom Poko', 'year': 1994})
    assert movie == movie
    same = Movie(movieID='0783644', data={'title': 'Pom Poko', 'year': 1994})
    assert movie == same
    assert not (movie != same)


def test_eq_with_other_types():
    movie = Movie(movieID='0783644', data={'title': 'Pom Poko', 'year': 1994})
    assert (movie == 'Pom Poko') is False
    assert (movie != 'Pom Poko') is True


def test_ordering_is_consistent_with_eq():
    m1 = Movie(movieID='0783644', data={'title': 'Pom Poko', 'year': 1994})
    m2 = Movie(movieID='1321512', data={'title': 'Arrietty', 'year': 2010})
    assert m2 < m1  # newer movies sort first
    assert m1 > m2
    assert m1 <= m1 and m1 >= m1
    assert sorted([m1, m2]) == [m2, m1]


def test_last_sentinel_compares_greater_than_anything():
    assert (_last == _last) is True
    assert (_last == 'anything') is False
    assert (_last < _last) is False
    assert (_last > _last) is False
    assert 'anything' < _last
    assert _last > 'anything'


def test_person_eq():
    p1 = Person(personID='0001', data={'name': 'Fred Astaire'})
    p2 = Person(personID='0002', data={'name': 'Ginger Rogers'})
    assert isinstance(p1 == p2, bool)
    assert p1 != p2
    assert p1 == Person(personID='0001', data={'name': 'Fred Astaire'})
    # a billing position sorts before a missing one for different objects
    billed = Person(personID='0003', data={'name': 'Fred Astaire'})
    billed.billingPos = 1
    assert billed < p1
    assert p1 > billed


def test_company_eq():
    c1 = Company(companyID='0001', data={'name': 'Studio Ghibli'})
    c2 = Company(companyID='0002', data={'name': 'Disney'})
    assert isinstance(c1 == c2, bool)
    assert c1 != c2
    assert c1 == Company(companyID='0001', data={'name': 'Studio Ghibli'})


def test_character_eq():
    c1 = Character(characterID='0001', data={'name': 'R2-D2'})
    c2 = Character(characterID='0002', data={'name': 'C-3PO'})
    assert isinstance(c1 == c2, bool)
    assert c1 != c2
    assert c1 == Character(characterID='0001', data={'name': 'R2-D2'})


def test_container_without_cmp_function_is_never_equal():
    container = _Container()
    assert (container == container) is True
    assert (container != container) is False
    assert container != _Container()


def test_same_description_with_different_ids_is_not_equal():
    people = (
        Person(personID='0001', data={'name': 'Alex Smith'}),
        Person(personID='0002', data={'name': 'Alex Smith'}),
    )
    companies = (
        Company(companyID='0001', data={'name': 'Acme'}),
        Company(companyID='0002', data={'name': 'Acme'}),
    )
    characters = (
        Character(characterID='0001', data={'name': 'Alex'}),
        Character(characterID='0002', data={'name': 'Alex'}),
    )

    for first, second in (people, companies, characters):
        assert first != second
        assert second != first


def test_equal_containers_have_equal_hashes():
    with_string_id = Person(
        personID='1', accessSystem='s3', data={'name': 'Fred Astaire'}
    )
    with_integer_id = Person(
        personID=1, accessSystem='s3', data={'name': 'Fred Astaire'}
    )
    assert with_string_id == with_integer_id
    assert hash(with_string_id) == hash(with_integer_id)
    assert len({with_string_id, with_integer_id}) == 1

    partial = Movie(
        movieID='1', accessSystem='s3', data={'title': 'Example'}
    )
    complete = Movie(
        movieID=1,
        accessSystem='s3',
        data={'title': 'Example', 'year': 2000, 'genres': ['drama']},
    )
    assert partial == complete
    assert hash(partial) == hash(complete)
    assert not partial < complete
    assert not complete < partial

    without_id_1 = Company(data={'name': 'Acme'})
    without_id_2 = Company(data={'name': 'Acme'})
    assert without_id_1 == without_id_2
    assert hash(without_id_1) == hash(without_id_2)


def test_access_system_is_part_of_identity():
    from_s3 = Movie(
        movieID='1', accessSystem='s3', data={'title': 'Example', 'year': 2000}
    )
    from_other = Movie(
        movieID='1', accessSystem='other', data={'title': 'Example', 'year': 2000}
    )
    assert from_s3 != from_other


def test_comparison_when_only_one_movie_has_an_id():
    without_id = Movie(data={'title': 'Example', 'year': 2000})
    with_id = Movie(movieID='1', data={'title': 'Example', 'year': 2000})

    assert isinstance(without_id == with_id, bool)
    assert without_id != with_id
    assert with_id != without_id
    assert (without_id < with_id) != (with_id < without_id)
