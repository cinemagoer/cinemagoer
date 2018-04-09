from pytest import mark


@mark.fragile
def test_found_one_result_should_be_list_with_one_keyword(ia):
    data = ia.search_keyword('zoolander')
    assert data == ['colander']


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_keywords(ia):
    data = ia.search_keyword('messiah')
    assert 40 < len(data) < 50


def test_found_too_many_result_should_contain_upper_limit_of_keywords(ia):
    data = ia.search_keyword('computer')
    assert len(data) == 200


def test_found_none_result_should_be_empty(ia):
    data = ia.search_keyword('%e3%82%a2')
    assert data == []
