from pytest import mark


@mark.fragile
def test_found_many_result_should_contain_correct_number_of_people(ia):
    data = ia.search_person('keanu reeves')
    assert len(data) == 4
