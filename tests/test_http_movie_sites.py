def test_sites_should_be_lists(ia):
    data = ia.get_movie('0133093', info=['official sites'])     # Matrix
    assert len(data.get('official sites', [])) == 1
    assert len(data.get('sound clips', [])) == 3
