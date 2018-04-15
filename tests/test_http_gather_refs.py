def test_references_to_titles_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    titles_refs = person.get_titlesRefs()
    assert 70 < len(titles_refs) < 100


def test_references_to_names_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])  # Julia Roberts
    names_refs = person.get_namesRefs()
    assert 100 < len(names_refs) < 150
