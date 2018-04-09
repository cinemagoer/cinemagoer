from pytest import mark


@mark.fragile
def test_search_person_unlimited_should_list_contain_correct_number_of_people(ia):
    people = ia.search_person('engelbart', results=-1)
    assert 120 <= len(people) <= 150
