from pytest import fixture, mark

from imdb.parser.http.searchCharacterParser import DOMHTMLSearchCharacterParser


@fixture(scope='module')
def search_character(url_opener, search):
    """A function to retrieve the search result for a character."""
    def retrieve(term):
        url = search + '?s=ch&q=' + term.replace(' ', '+')
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLSearchCharacterParser()


@mark.skip(reason='no search for characters anymore')
@mark.fragile
def test_found_many_result_should_contain_correct_number_of_characters(search_character):
    page = search_character('jesse james')
    data = parser.parse(page)['data']
    assert len(data) == 11
