from pytest import mark

@mark.skip('creator parser is still broken see #275')
def test_series_has_creator(ia):
    movie = ia.get_movie('0412142')
    assert '0794914' in [p.personID for p in movie.get('creator')]

def test_series_full_cast_has_ids(ia):
    movie = ia.get_movie('0412142', info=['full cast'])      # House M.D.
    # all persons must have a personID
    assert [p for p in movie.get('cast', []) if p.personID is None] == []
