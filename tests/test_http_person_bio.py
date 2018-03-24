from pytest import fixture

import re

from imdb.parser.http.personParser import DOMHTMLBioParser


@fixture(scope='module')
def person_bio(url_opener, people):
    """A function to retrieve the main details page of a test person."""
    def retrieve(person_key):
        url = people[person_key] + '/bio'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLBioParser()


def test_headshot_should_be_an_image_link(person_bio):
    page = person_bio('keanu reeves')
    data = parser.parse(page)['data']
    assert re.match(r'^https?://.*\.jpg$', data['headshot'])


def test_headshot_none_should_be_excluded(person_bio):
    page = person_bio('deni gordon')
    data = parser.parse(page)['data']
    assert 'headshot' not in data


def test_birth_date_should_be_in_ymd_format(person_bio):
    page = person_bio('fred astaire')
    data = parser.parse(page)['data']
    assert data['birth date'] == '1899-5-10'


def test_birth_notes_should_contain_birth_place(person_bio):
    page = person_bio('fred astaire')
    data = parser.parse(page)['data']
    assert data['birth notes'] == 'Omaha, Nebraska, USA'


def test_death_date_should_be_in_ymd_format(person_bio):
    page = person_bio('fred astaire')
    data = parser.parse(page)['data']
    assert data['death date'] == '1987-6-22'


def test_death_date_none_should_be_excluded(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert 'death date' not in data


def test_death_notes_should_contain_death_place_and_reason(person_bio):
    page = person_bio('fred astaire')
    data = parser.parse(page)['data']
    assert data['death notes'] == 'in Los Angeles, California, USA (pneumonia)'


def test_death_notes_none_should_be_excluded(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert 'death notes' not in data


def test_birth_name_should_be_canonical(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert data['birth name'] == 'Roberts, Julia Fiona'


def test_nicknames_single_should_be_a_list_with_one_name(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert data['nick names'] == ['Jules']


def test_nicknames_multiple_should_be_a_list_of_names(person_bio):
    page = person_bio('keanu reeves')
    data = parser.parse(page)['data']
    assert data['nick names'] == ['The Wall', 'The One']


def test_height_should_be_in_inches_and_meters(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert data['height'] == '5\' 8" (1.73 m)'


def test_height_none_should_be_excluded(person_bio):
    page = person_bio('georges melies')
    data = parser.parse(page)['data']
    assert 'height' not in data


def test_spouse_should_be_a_list(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert len(data['spouse']) == 2


def test_trade_mark_should_be_a_list(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert len(data['trade mark']) == 2


def test_trivia_should_be_a_list(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert len(data['trivia']) > 90


def test_quotes_should_be_a_list(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert len(data['quotes']) > 30


def test_salary_history_should_be_a_list(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)['data']
    assert len(data['salary history']) > 25
