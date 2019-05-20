def test_person_other_works_should_contain_correct_number_of_works(ia):
    person = ia.get_person('0000206', info=['other works'])     # Keanu Reeves
    other_works = person.get('other works', [])
    assert len(other_works) == 42


def test_person_other_works_should_contain_correct_work(ia):
    person = ia.get_person('0000206', info=['other works'])     # Keanu Reeves
    other_works = person.get('other works', [])
    assert other_works[0].startswith('(1995) Stage: Appeared')


def test_person_other_works_if_none_should_be_excluded(ia):
    person = ia.get_person('0330139', info=['other works'])     # Deni Gordon
    assert 'other works' not in person
