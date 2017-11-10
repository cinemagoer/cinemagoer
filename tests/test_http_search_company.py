from pytest import fixture, mark

from urllib.request import urlopen

from imdb.parser.http.searchCompanyParser import DOMHTMLSearchCompanyParser


@fixture(scope='module')
def search_company(search):
    """A function to retrieve the search result for a company."""
    def retrieve(term):
        url = search + '?s=co&q=' + term.replace(' ', '+')
        return urlopen(url).read().decode('utf-8')
    return retrieve


parser = DOMHTMLSearchCompanyParser()


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_companies(search_company):
    page = search_company('pixar')
    data = parser.parse(page)['data']
    assert len(data) == 38
