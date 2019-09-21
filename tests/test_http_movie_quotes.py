def test_movie_quotes(ia):
    movie = ia.get_movie('0133093', info=['quotes'])
    quotes = movie.get('quotes', [])
    assert len(quotes) > 100

