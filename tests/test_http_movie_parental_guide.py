def test_movie_parental_guide_contains_mpaa_rating(ia):
    movie = ia.get_movie('0133093', info=['parents guide'])  # Matrix
    assert movie.get('mpaa') == "Rated R for sci-fi violence and brief language"

def test_movie_certificates_from_parental_guide(ia):
    movie = ia.get_movie('0133093', info=['parents guide'])      # Matrix
    arCert = {'country_code': 'AR', 'country': 'Argentina', 'certificate': '13', 'note': '', 'full': 'Argentina:13'}
    assert arCert in movie.get('certificates', [])

def test_movie_advisories(ia):
    movie = ia.get_movie('0133093', info=['parents guide'])      # Matrix
    assert any(['Mouse gets shot' in x for x in movie.get('advisory spoiler violence')])
