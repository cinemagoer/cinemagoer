import re


def test_headshot_should_be_an_image_link(ia):
    data = ia.get_person('0000206', info=['biography'])     # Keanu Reeves
    assert re.match(r'^https?://.*\.jpg$', data['headshot'])


def test_headshot_none_should_be_excluded(ia):
    data = ia.get_person('0330139', info=['biography'])     # Deni Gordon
    assert 'headshot' not in data


def test_birth_date_should_be_in_ymd_format(ia):
    data = ia.get_person('0000001', info=['biography'])     # Fred Astaire
    assert data['birth date'] == '1899-5-10'


def test_birth_notes_should_contain_birth_place(ia):
    data = ia.get_person('0000001', info=['biography'])     # Fred Astaire
    assert data['birth notes'] == 'Omaha, Nebraska, USA'


def test_death_date_should_be_in_ymd_format(ia):
    data = ia.get_person('0000001', info=['biography'])     # Fred Astaire
    assert data['death date'] == '1987-6-22'


def test_death_date_none_should_be_excluded(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert 'death date' not in data


def test_death_notes_should_contain_death_place_and_reason(ia):
    data = ia.get_person('0000001', info=['biography'])     # Fred Astaire
    assert data['death notes'] == 'in Los Angeles, California, USA (pneumonia)'


def test_death_notes_none_should_be_excluded(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert 'death notes' not in data


def test_birth_name_should_be_canonical(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert data['birth name'] == 'Roberts, Julia Fiona'


def test_nicknames_single_should_be_a_list_with_one_name(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert data['nick names'] == ['Jules']


def test_nicknames_multiple_should_be_a_list_of_names(ia):
    data = ia.get_person('0000206', info=['biography'])     # Keanu Reeves
    assert data['nick names'] == ['The Wall', 'The One']


def test_height_should_be_in_inches_and_meters(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert data['height'] == '5\' 8" (1.73 m)'


def test_height_none_should_be_excluded(ia):
    data = ia.get_person('0617588', info=['biography'])     # Georges Melies
    assert 'height' not in data


def test_spouse_should_be_a_list(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert len(data['spouse']) == 2


def test_trade_mark_should_be_a_list(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert len(data['trade mark']) == 2


def test_trivia_should_be_a_list(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert len(data['trivia']) > 90


def test_quotes_should_be_a_list(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert len(data['quotes']) > 30


def test_salary_history_should_be_a_list(ia):
    data = ia.get_person('0000210', info=['biography'])     # Julia Roberts
    assert len(data['salary history']) > 25
