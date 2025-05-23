def test_movie_reviews_should_be_a_list(ia):
    movie = ia.get_movie('0104155', info=['reviews'])   # Dust Devil
    reviews = movie.get('reviews', [])
    assert len(reviews) == 25


def test_movie_reviews_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['reviews'])   # Ates Parcasi
    assert 'reviews' not in movie


def test_movie_critic_reviews_metascore(ia):
    movie = ia.get_movie('0133093', info=['critic reviews'])   # The Matrix
    assert 65 < movie.get('metascore') < 80
    assert 'metacritic.com' in movie.get('metacritic url', '')
