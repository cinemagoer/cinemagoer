def test_company_name_should_not_include_country(ia):
    data = ia.get_company('0017902', info=['main'])
    assert data.get('name') == 'Pixar Animation Studios'
