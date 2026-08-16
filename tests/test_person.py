import pytest

import xml.etree.ElementTree as ET

from imdb.Person import Person


@pytest.mark.parametrize(
    ('name', 'first_name', 'last_name'),
    [
        ('Fred Astaire', 'Fred', 'Astaire'),
        ('Julia Fiona Roberts', 'Julia Fiona', 'Roberts'),
        ('Robert De Niro', 'Robert', 'De Niro'),
        ('Frederick Austerlitz Jr.', 'Frederick', 'Austerlitz'),
        ('Frank Sinatra III', 'Frank', 'Sinatra'),
        ('Sinatra Jr., Frank', 'Frank', 'Sinatra'),
        ('Cher', '', 'Cher'),
    ],
)
def test_person_name_components(name, first_name, last_name):
    person = Person(data={'name': name})

    assert person['first name'] == first_name
    assert person['last name'] == last_name
    assert person.data['name'] == name
    assert 'first name' in person.keys()
    assert 'last name' in person.keys()


def test_person_name_components_are_serialized_as_xml():
    person = Person(data={'name': 'Frederick Austerlitz Jr.'}, personID='1')

    root = ET.fromstring(person.asXML())

    assert root.findtext('first-name') == 'Frederick'
    assert root.findtext('last-name') == 'Austerlitz'
