def test_person_awards(ia):
    person = ia.get_person('0000206', info=['awards'])
    awards = person.get('awards', [])
    assert len(awards) > 20

