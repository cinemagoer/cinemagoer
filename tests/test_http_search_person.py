from pytest import fixture, mark

from urllib.request import urlopen

from imdb.parser.http.searchPersonParser import DOMHTMLSearchPersonParser


@fixture(scope='module')
def search_person(search):
    """A function to retrieve the search result for a person."""
    def retrieve(term):
        url = search + '?s=nm&q=' + term.replace(' ', '+')
        return urlopen(url).read().decode('utf-8')
    return retrieve


parser = DOMHTMLSearchPersonParser()


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_people(search_person):
    page = search_person('keanu reeves')
    data = parser.parse(page)['data']
    assert len(data) == 4
