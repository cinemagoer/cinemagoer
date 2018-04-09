def test_keywords_multiple_should_be_parsed_correctly(ia):
    data = ia.get_movie('0133093', info=['keywords'])   # Matrix
    assert {'computer-hacker', 'messiah', 'artificial-reality'}.issubset(set(data['keywords']))


def test_keywords_none_should_be_excluded(ia):
    data = ia.get_movie('1863157', info=['keywords'])   # Ates Parcasi
    assert 'keywords' not in data
