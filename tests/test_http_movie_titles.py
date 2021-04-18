from pytest import mark

@mark.skip('obviously this depends on your country of origin')
def test_movie_localized_title(ia):
    movie = ia.get_movie('2991224', info=['main'])
    title = movie.get('localized title', '')
    assert title in ('Tangerines - Mandarini', 'Tangerines')


def test_movie_original_title(ia):
    movie = ia.get_movie('2991224', info=['main'])
    title = movie.get('original title', '')
    assert title == 'Mandariinid'


def test_movie_title(ia):
    movie = ia.get_movie('2991224', info=['main'])
    title = movie.get('title', '')
    assert title == 'Tangerines'

