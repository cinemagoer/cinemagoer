def test_number_of_reviews_should_be_correct(ia):
    data = ia.get_movie('0104155', info=['reviews'])    # Dust Devil
    assert len(data.get('reviews', [])) == 25
