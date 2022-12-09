from pytest import mark


def test_search_company_should_list_default_number_of_companies(ia):
    companies = ia.search_company('pixar')
    assert len(companies) == 12


@mark.skip(reason="number of results limit is not honored anymore")
def test_search_company_limited_should_list_requested_number_of_companies(ia):
    companies = ia.search_company('pixar', results=7)
    assert len(companies) == 7


def test_search_company_unlimited_should_list_correct_number_of_companies(ia):
    companies = ia.search_company('pixar', results=500)
    assert len(companies) == 12


def test_search_company_too_many_should_list_upper_limit_of_companies(ia):
    companies = ia.search_company('pictures', results=500)
    assert len(companies) == 25


def test_search_company_if_none_result_should_be_empty(ia):
    companies = ia.search_company('%e3%82%a2')
    assert companies == []


def test_search_company_entries_should_include_company_id(ia):
    companies = ia.search_company('pixar')
    assert companies[0].companyID in ('0348691', '0017902')


def test_search_company_entries_should_include_company_name(ia):
    companies = ia.search_company('pixar')
    assert companies[0]['name'] == 'Pixar Animation Studios'


def test_search_company_entries_should_include_company_country(ia):
    companies = ia.search_company('pixar')
    assert companies[0]['country'] == '[United States]'    # shouldn't this be just 'ca'?


@mark.skip(reason="tested company always has a country: find another one")
def test_search_company_entries_missing_country_should_be_excluded(ia):
    companies = ia.search_company('pixar', results=500)
    company_without_country = [c for c in companies if c.companyID == '0115838']
    assert len(company_without_country) == 1
    assert 'country' not in company_without_country[0]
