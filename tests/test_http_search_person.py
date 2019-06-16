from pytest import mark

def test_search_person_should_list_default_number_of_people(ia):
    people = ia.search_person('julia')
    assert len(people) == 20


def test_search_person_limited_should_list_requested_number_of_people(ia):
    people = ia.search_person('julia', results=11)
    assert len(people) == 11


def test_search_person_unlimited_should_list_correct_number_of_people(ia):
    people = ia.search_person('engelbart', results=500)
    assert 120 <= len(people) <= 150


def test_search_person_if_too_many_should_list_upper_limit_of_people(ia):
    people = ia.search_person('john', results=500)
    assert len(people) == 200


def test_search_person_if_none_result_should_be_empty(ia):
    people = ia.search_person('%e3%82%a2')
    assert people == []


def test_search_person_entries_should_include_person_id(ia):
    people = ia.search_person('julia roberts')
    assert people[0].personID == '0000210'


def test_search_person_entries_should_include_person_name(ia):
    people = ia.search_person('julia roberts')
    assert people[0]['name'] == 'Julia Roberts'

def test_search_person_entries_should_include_headshot_if_available(ia):
    people = ia.search_person('julia roberts')
    assert 'headshot' in people[0]

def test_search_person_entries_with_aka_should_exclude_name_in_aka(ia):
    people = ia.search_person('julia roberts')
    robertson = None
    for person in people:
        if person['name'] == 'Julia Robertson':
            robertson = person
            break
    assert robertson
    assert robertson['name'] == 'Julia Robertson'


def test_search_person_entries_should_include_person_index(ia):
    people = ia.search_person('julia roberts')
    assert people[0]['imdbIndex'] == 'I'


@mark.skip(reason="no persons without imdbIndex in the first 20 results")
def test_search_person_entries_missing_index_should_be_excluded(ia):
    people = ia.search_person('julia roberts')
    assert 'imdbIndex' not in people[3]


@mark.skip(reason="AKAs no longer present in results?")
def test_search_person_entries_should_include_akas(ia):
    people = ia.search_person('julia roberts')
    person_with_aka = [p for p in people if p.personID == '4691618']
    assert len(person_with_aka) == 1
    assert person_with_aka[0]['akas'] == ['Julia Robertson']


def test_search_person_entries_missing_akas_should_be_excluded(ia):
    people = ia.search_person('julia roberts')
    assert 'akas' not in people[0]
