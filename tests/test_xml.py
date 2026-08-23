import xml.etree.ElementTree as ET

from imdb.Character import Character
from imdb.helpers import parseXML
from imdb.Movie import Movie
from imdb.Person import Person


def test_movie_xml(ia):
    movie = ia.get_movie('9')    # Miss Jerry
    movie_xml = movie.asXML()
    movie_xml = movie_xml.encode('utf8', 'ignore')
    assert ET.fromstring(movie_xml) is not None


def test_s3_movie_xml_round_trip(ia):
    movie = ia.get_movie('9')    # Miss Jerry

    parsed = parseXML(movie.asXML())

    assert parsed.movieID == movie.movieID
    assert parsed.accessSystem == movie.accessSystem
    assert parsed['title'] == movie['title']
    assert parsed['adult'] == movie['adult']
    assert parsed['akas'] == movie['akas']
    assert parsed.current_info == movie.current_info
    assert parsed.infoset2keys == movie.infoset2keys
    assert parsed.key2infoset == movie.key2infoset

    parsed_person = parsed['cast'][0]
    original_person = movie['cast'][0]
    assert isinstance(parsed_person, Person)
    assert str(parsed_person.personID) == str(original_person.personID)
    assert parsed_person.get('name') is None
    assert isinstance(parsed_person.currentRole, Character)
    assert parsed_person.currentRole.get('name') == original_person.currentRole.get('name')


def test_person_roles_and_empty_value_xml_round_trip():
    roles = [
        Character(characterID='2', name='Lead', notes='credited'),
        Character(characterID='3', name=''),
    ]
    person = Person(
        personID='1', data={'name': 'Jane Doe', 'empty value': ''},
        currentRole=roles, accessSystem='s3'
    )
    person.add_to_current_info('main', keys=['name', 'empty value'])
    person.add_to_current_info('biography', keys=[])

    parsed = parseXML(person.asXML())

    assert isinstance(parsed, Person)
    assert parsed.personID == '1'
    assert parsed.accessSystem == 's3'
    assert parsed['name'] == 'Jane Doe'
    assert parsed['empty value'] == ''
    assert parsed.current_info == ['main', 'biography']
    assert parsed.infoset2keys == {'main': ['name', 'empty value']}
    assert len(parsed.currentRole) == 2
    assert all(isinstance(role, Character) for role in parsed.currentRole)
    assert [role.characterID for role in parsed.currentRole] == ['2', '3']
    assert parsed.currentRole[0]['name'] == 'Lead'
    assert parsed.currentRole[0].notes == 'credited'
    assert parsed.currentRole[1].get('name') is None


def test_single_empty_role_with_id_xml_round_trip():
    movie = Movie(
        movieID='9', title='Miss Jerry', accessSystem='s3',
        currentRole=Character(name=''), roleID='1'
    )

    parsed = parseXML(movie.asXML())

    assert isinstance(parsed.currentRole, Character)
    assert parsed.currentRole.characterID == '1'
    assert parsed.roleID == '1'
    assert parsed.currentRole.get('name') is None
