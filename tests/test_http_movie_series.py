from pytest import mark

def test_series_full_cast_has_ids(ia):
    movie = ia.get_movie('0412142', info=['full cast'])      # House M.D.
    # all persons must have a personID
    assert [p for p in movie.get('cast', []) if p.personID is None] == []
