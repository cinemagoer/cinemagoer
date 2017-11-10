from pytest import fixture, mark

from urllib.request import urlopen

from imdb.parser.http.searchCharacterParser import DOMHTMLSearchCharacterParser


@fixture(scope='module')
def search_character(search):
    """A function to retrieve the search result for a character."""
    def retrieve(term):
        url = search + '?s=ch&q=' + term.replace(' ', '+')
        return urlopen(url).read().decode('utf-8')
    return retrieve


parser = DOMHTMLSearchCharacterParser()


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_characters(search_character):
    page = search_character('jesse james')
    data = parser.parse(page)['data']
    assert len(data) == 11
