import re


def test_person_headshot_should_be_an_image_link(ia):
    person = ia.get_person('0000206', info=['biography'])   # Keanu Reeves
    assert re.match(r'^https?://.*\.jpg$', person['headshot'])


def test_person_full_size_headshot_should_be_an_image_link(ia):
    person = ia.get_person('0000206', info=['biography'])   # Keanu Reeves
    assert re.match(r'^https?://.*\.jpg$', person['full-size headshot'])


def test_person_headshot_if_none_should_be_excluded(ia):
    person = ia.get_person('0330139', info=['biography'])   # Deni Gordon
    assert 'headshot' not in person


def test_person_bio_is_present(ia):
    person = ia.get_person('0000206', info=['biography'])   # Keanu Reeves
    assert 'mini biography' in person


def test_person_birth_date_should_be_in_ymd_format(ia):
    person = ia.get_person('0000001', info=['biography'])   # Fred Astaire
    assert person.get('birth date') == '1899-05-10'


def test_person_birth_date_without_month_and_date_should_be_in_y00_format(ia):
    person = ia.get_person('0565883', info=['biography'])   # Belinda McClory
    assert person.get('birth date') == '1968-00-00'


def test_person_birth_date_without_itemprop_should_be_in_ymd_format(ia):
    person = ia.get_person('0000007', info=['biography'])   # Humphrey Bogart
    assert person.get('birth date') == '1899-12-25'


def test_person_birth_notes_should_contain_birth_place(ia):
    person = ia.get_person('0000001', info=['biography'])   # Fred Astaire
    assert person.get('birth notes') == 'Omaha, Nebraska, USA'


def test_person_death_date_should_be_in_ymd_format(ia):
    person = ia.get_person('0000001', info=['biography'])   # Fred Astaire
    assert person.get('death date') == '1987-06-22'


def test_person_death_date_without_itemprop_should_be_in_ymd_format(ia):
    person = ia.get_person('0000007', info=['biography'])   # Humphrey Bogart
    assert person.get('death date') == '1957-01-14'


def test_person_death_date_if_none_should_be_excluded(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    assert 'death date' not in person


def test_person_death_notes_should_contain_death_place_and_reason(ia):
    person = ia.get_person('0000001', info=['biography'])   # Fred Astaire
    assert person['death notes'] == 'in Los Angeles, California, USA (pneumonia)'


def test_person_death_notes_if_none_should_be_excluded(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    assert 'death notes' not in person


def test_person_birth_name_should_be_normalized(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert data.get('birth name') == 'Julia Fiona Roberts'


def test_person_nicknames_if_single_should_be_a_list_of_names(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    assert person.get('nick names') == ['Jules']


def test_person_nicknames_if_multiple_should_be_a_list_of_names(ia):
    person = ia.get_person('0000206', info=['biography'])   # Keanu Reeves
    assert person.get('nick names') == ['The Wall', 'The One']


def test_person_height_should_be_in_inches_and_meters(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    assert person.get('height') == '5\' 8" (1.73 m)'


def test_person_height_if_none_should_be_excluded(ia):
    person = ia.get_person('0617588', info=['biography'])   # Georges Melies
    assert 'height' not in person


def test_person_spouse_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    spouses = person.get('spouse', [])
    assert len(spouses) == 2


def test_person_trade_mark_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    trade_mark = person.get('trade mark', [])
    assert len(trade_mark) == 3


def test_person_trivia_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    trivia = person.get('trivia', [])
    assert len(trivia) > 90


def test_person_quotes_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    quotes = person.get('quotes', [])
    assert len(quotes) > 30


def test_person_salary_history_should_be_a_list(ia):
    person = ia.get_person('0000210', info=['biography'])   # Julia Roberts
    salary = person.get('salary history', [])
    assert len(salary) > 25
