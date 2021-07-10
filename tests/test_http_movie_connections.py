def test_movie_followed_by_connections(ia):
    movie = ia.get_movie('0133093', info=['connections'])
    quotes = movie.get('connections', {}).get('followed by', [])
    assert len(quotes) >= 8

def test_movie_spinoff_connections(ia):
    movie = ia.get_movie('0133093', info=['connections'])
    quotes = movie.get('connections', {}).get('spin-off', [])
    assert len(quotes) >= 4
