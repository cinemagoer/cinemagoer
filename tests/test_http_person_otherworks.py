def test_multiple_works_should_contain_correct_number_of_works(ia):
    data = ia.get_person('0000206', info=['other works'])   # Keanu Reeves
    assert len(data['other works']) == 42


def test_multiple_works_should_contain_correct_work(ia):
    data = ia.get_person('0000206', info=['other works'])   # Keanu Reeves
    assert data['other works'][0].startswith('(1995) Stage: Appeared')


def test_works_none_should_be_excluded(ia):
    data = ia.get_person('0330139', info=['other works'])   # Deni Gordon
    assert 'other works' not in data
