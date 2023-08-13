def test_movie_trivia(ia):
    movie = ia.get_movie('0133093', info=['trivia'])
    trivia = movie.get('trivia', [])
    assert len(trivia) >= 5
