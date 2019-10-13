from pytest import mark

def test_movie_contains_recommendations(ia):
    movie = ia.get_movie('0133093', info=['recommendations'])      # Matrix
    assert len(movie.get('recommendations', [])) == 12


