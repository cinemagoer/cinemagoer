def test_get_showtimes_contains_data(ia):
    data = ia.get_showtimes()
    assert len(data) > 0
    for cinema_info in data:
        assert 'cinema' in cinema_info
        assert 'movies' in cinema_info
        assert len(cinema_info['movies']) > 0
        for movie in cinema_info['movies']:
            assert 'movie' in movie
            assert 'showtimes' in movie
