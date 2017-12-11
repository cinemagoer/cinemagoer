from pytest import fixture, mark

from imdb.parser.http.searchKeywordParser import DOMHTMLSearchKeywordParser


@fixture(scope='module')
def search_keyword(url_opener, search):
    """A function to retrieve the search result for a keyword."""
    def retrieve(term):
        url = search + '?s=kw&q=' + term.replace(' ', '+')
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLSearchKeywordParser()


@mark.fragile
def test_found_one_result_should_be_list_with_one_keyword(search_keyword):
    page = search_keyword('zoolander')
    data = parser.parse(page)['data']
    assert data == ['colander']


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_keywords(search_keyword):
    page = search_keyword('messiah')
    data = parser.parse(page)['data']
    assert 40 < len(data) < 50


def test_found_too_many_result_should_contain_200_keywords(search_keyword):
    page = search_keyword('computer')
    data = parser.parse(page)['data']
    assert len(data) == 200


def test_found_none_result_should_be_empty(search_keyword):
    page = search_keyword('%e3%82%a2')
    data = parser.parse(page)['data']
    assert data == []
