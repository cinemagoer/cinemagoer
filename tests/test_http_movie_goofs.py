def test_movie_goofs(ia):
    movie = ia.get_movie('0133093', info=['goofs'])
    goofs = movie.get('goofs', [])
    assert len(goofs) > 120

