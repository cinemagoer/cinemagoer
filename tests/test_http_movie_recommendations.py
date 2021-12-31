from pytest import mark


@mark.skip("FIXME: this section changed name to 'More Like This' and divs/classes have changed too")
def test_movie_contains_recommendations(ia):
    movie = ia.get_movie('0133093', info=['recommendations'])      # Matrix
    assert len(movie.get('recommendations', [])) == 12


