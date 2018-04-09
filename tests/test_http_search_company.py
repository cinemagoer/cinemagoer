def test_default_search_should_return_default_number_of_companies(ia):
    data = ia.search_company('pixar')
    assert len(data) == 20


def test_limited_search_should_return_given_number_of_companies(ia):
    data = ia.search_company('pixar', results=7)
    assert len(data) == 7


def test_unlimited_search_should_contain_correct_number_of_companies(ia):
    data = ia.search_company('pixar', results=-1)
    assert len(data) >= 38
