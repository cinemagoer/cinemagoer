def test_name_should_not_include_country(ia):
    data = ia.get_company('0017902')
    assert data['name'] == 'Pixar Animation Studios'
