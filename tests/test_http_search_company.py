def test_search_company_should_list_20_companies_by_default(ia):
    companies = ia.search_company('pixar')
    assert len(companies) == 20


def test_search_company_limited_should_list_requested_number_of_companies(ia):
    companies = ia.search_company('pixar', results=7)
    assert len(companies) == 7


def test_search_company_unlimited_should_list_correct_number_of_companies(ia):
    companies = ia.search_company('pixar', results=-1)
    assert len(companies) >= 38
