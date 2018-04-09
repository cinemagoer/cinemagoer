def test_search_person_should_list_default_number_of_people(ia):
    people = ia.search_person('julia')
    assert len(people) == 20


def test_search_person_limited_should_list_requested_number_of_people(ia):
    people = ia.search_person('julia', results=11)
    assert len(people) == 11


def test_search_person_unlimited_should_list_correct_number_of_people(ia):
    people = ia.search_person('engelbart', results=-1)
    assert 120 <= len(people) <= 150


def test_search_person_if_too_many_should_list_upper_limit_of_people(ia):
    people = ia.search_person('john', results=-1)
    assert len(people) == 200


def test_search_person_if_none_result_should_be_empty(ia):
    people = ia.search_person('%e3%82%a2')
    assert people == []
