def test_references_to_titles_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    assert 70 < len(person.get_titlesRefs()) < 100


def test_references_to_names_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])  # Julia Roberts
    assert 100 < len(person.get_namesRefs()) < 150
