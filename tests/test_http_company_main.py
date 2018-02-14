from pytest import fixture

from imdb.parser.http.companyParser import DOMCompanyParser


@fixture(scope='module')
def company_main_details(url_opener, companies):
    """A function to retrieve the main details page of a test company."""
    def retrieve(company_key):
        url = companies[company_key]
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMCompanyParser()


def test_name_should_not_include_country(company_main_details):
    page = company_main_details('pixar')
    data = parser.parse(page)['data']
    assert data['name'] == 'Pixar Animation Studios'
