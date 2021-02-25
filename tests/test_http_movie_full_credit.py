
def test_movie_full_credits(ia):
    movie = ia.get_movie('0133093', info=['full credits']) # Matrix
    assert 'cast' in movie
    assert len(movie['cast']) == 41

def test_movie_full_credits_for_tv_show(ia):
    movie = ia.get_movie('0098904', info=['full credits']) # Seinfeld
    assert 'cast' in movie
    assert len(movie['cast']) > 1300 and len(movie['cast']) < 1350

def test_movie_full_credits_contains_headshot(ia):
    movie = ia.get_movie('0133093', info=['main', 'full credits'])      # Matrix
    assert 'headshot' in movie['cast'][0] # Keanu Reeves
    assert 'nopicture' not in movie['cast'][0]['headshot'] # is real headshot, not default
