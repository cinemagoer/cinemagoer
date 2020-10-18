def test_search_keyword_check_list_of_keywords(ia):
    keywords = ia.search_keyword('zoolander')
    assert 'reference-to-zoolander' in keywords


def test_search_keyword_if_multiple_should_list_correct_number_of_keywords(ia):
    keywords = ia.search_keyword('messiah')
    assert 50 <= len(keywords) <= 80


def test_search_keyword_if_too_many_should_list_upper_limit_of_keywords(ia):
    keywords = ia.search_keyword('computer')
    assert len(keywords) == 200


def test_search_keyword_if_none_result_should_be_empty(ia):
    keywords = ia.search_keyword('%e3%82%a2')
    assert keywords == []


def test_get_keyword_pagination(ia):
    superheroes_without_page_param = ia.get_keyword('superhero')
    superheroes_page_one = ia.get_keyword('superhero', page=1)
    superheroes_page_two = ia.get_keyword('superhero', page=2)
    for i in range(50):
        assert superheroes_without_page_param[i]['title'] == superheroes_page_one[i]['title']
        assert superheroes_without_page_param[i]['title'] != superheroes_page_two[i]['title']

    
