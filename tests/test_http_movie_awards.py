def test_movie_awards(ia):
    movie = ia.get_movie('0133093', info=['awards'])
    awards = movie.get('awards', [])
    assert len(awards) > 80

