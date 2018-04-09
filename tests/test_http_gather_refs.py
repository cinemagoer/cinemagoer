def test_movie_and_person_refs_should_be_lists(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert len(data.namesRefs) > 100
    assert len(data.titlesRefs) > 70
