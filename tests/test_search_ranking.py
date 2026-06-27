from imdb.parser.s3.utils import scan_titles


def test_exact_movie_title_ranks_before_aka_and_no_year_noise():
    candidates = [
        (40123928, {'title': 'The Matrix', 'kind': 'short', 'year': '2022'}),
        (31444806, {'title': 'The Matrix'}),
        (133093, {'title': 'The Matrix', 'kind': 'movie', 'year': '1999'}),
        (9851526, {'title': 'The Matrix', 'kind': 'short', 'year': '2004'}),
    ]

    ranked = scan_titles(candidates, 'The Matrix', results=10)

    assert [item[1][0] for item in ranked[:3]] == [133093, 40123928, 9851526]