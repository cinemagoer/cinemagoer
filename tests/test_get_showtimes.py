def test_get_showtimes_num_cinemas(ia):
    data = ia.get_showtimes()

    # minus 2 two elimate keys 'num_cinemas', 'num_movies'
    assert len(data.keys()) - 2 == data['num_cinemas']
