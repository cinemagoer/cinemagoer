def test_movie_parental_guide_contains_mpaa_rating(ia):
    movie = ia.get_movie('0133093', info=['parents guide'])  # Matrix
    assert movie.get('mpaa') == "Rated R for sci-fi violence and brief language"
