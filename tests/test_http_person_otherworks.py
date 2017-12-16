from pytest import fixture

from imdb.parser.http.personParser import DOMHTMLOtherWorksParser


@fixture(scope='module')
def person_other_works(url_opener, people):
    """A function to retrieve the other works page of a test person."""
    def retrieve(person_key):
        url = people[person_key] + '/otherworks'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLOtherWorksParser()


def test_multiple_works_should_contain_correct_number_of_works(person_other_works):
    page = person_other_works('keanu reeves')
    data = parser.parse(page)['data']
    assert len(data['other works']) == 42


def test_multiple_works_should_contain_correct_work(person_other_works):
    page = person_other_works('keanu reeves')
    data = parser.parse(page)['data']
    assert data['other works'][0].startswith('(1995) Stage: Appeared')


def test_works_none_should_be_excluded(person_other_works):
    page = person_other_works('deni gordon')
    data = parser.parse(page)['data']
    assert 'other works' not in data
