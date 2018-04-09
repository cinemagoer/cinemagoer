def test_references_to_titles_and_names_should_be_lists(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    assert len(person.get_namesRefs()) > 100
    assert len(person.get_titlesRefs()) > 70
