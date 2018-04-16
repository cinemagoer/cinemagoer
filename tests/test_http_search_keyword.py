def test_search_keyword_if_single_should_list_one_keyword(ia):
    keywords = ia.search_keyword('zoolander')
    assert keywords == ['colander']


def test_search_keyword_if_multiple_should_list_correct_number_of_keywords(ia):
    keywords = ia.search_keyword('messiah')
    assert 40 <= len(keywords) <= 50


def test_search_keyword_if_too_many_should_list_upper_limit_of_keywords(ia):
    keywords = ia.search_keyword('computer')
    assert len(keywords) == 200


def test_search_keyword_if_none_result_should_be_empty(ia):
    keywords = ia.search_keyword('%e3%82%a2')
    assert keywords == []
