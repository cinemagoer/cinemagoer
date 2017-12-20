from pytest import fixture

import re

from imdb.parser.http.personParser import DOMHTMLMaindetailsParser


@fixture(scope='module')
def person_main_details(url_opener, people):
    """A function to retrieve the main details page of a test person."""
    def retrieve(person_key):
        url = people[person_key]
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLMaindetailsParser()


def test_headshot_should_be_an_image_link(person_main_details):
    page = person_main_details('keanu reeves')
    data = parser.parse(page)['data']
    assert re.match(r'^https?://.*\.jpg$', data['headshot'])


def test_headshot_none_should_be_excluded(person_main_details):
    page = person_main_details('deni gordon')
    data = parser.parse(page)['data']
    assert 'headshot' not in data


def test_name_should_be_canonical(person_main_details):
    page = person_main_details('keanu reeves')
    data = parser.parse(page)['data']
    assert data['name'] == 'Reeves, Keanu'


def test_name_should_not_have_year(person_main_details):
    page = person_main_details('fred astaire')
    data = parser.parse(page)['data']
    assert data['name'] == 'Astaire, Fred'


def test_imdb_index_should_be_a_roman_number(person_main_details):
    page = person_main_details('julia roberts')
    data = parser.parse(page)['data']
    assert data['imdbIndex'] == 'I'


def test_imdb_index_none_should_be_excluded(person_main_details):
    page = person_main_details('keanu reeves')
    data = parser.parse(page)['data']
    assert 'imdbIndex' not in data
