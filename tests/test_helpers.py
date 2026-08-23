from imdb.helpers import akasLanguages, getAKAsInLanguage, sortAKAsBySimilarity
from imdb.Movie import Movie


def test_aka_helpers_support_structured_and_legacy_records():
    movie = Movie(
        data={
            'title': 'Original',
            'akas': [
                {'title': 'English title', 'language': 'en', 'region': 'US'},
                {'title': 'Titolo italiano', 'region': 'Italy'},
                {'title': 'English title', 'language': 'en', 'region': 'GB'},
            ],
            'akas from release info': [
                'Legacy title (Italian title)',
                'Unannotated title',
            ],
        }
    )

    assert akasLanguages(movie) == [
        ('en', 'English title'),
        ('Italian', 'Titolo italiano'),
        ('Italian', 'Legacy title'),
        (None, 'Unannotated title'),
    ]
    assert getAKAsInLanguage(movie, 'en') == ['English title']
    assert getAKAsInLanguage(
        movie, 'Italian', _searchedTitle='Legacy title'
    ) == ['Legacy title', 'Titolo italiano']


def test_sort_akas_handles_equal_titles_with_different_languages():
    movie = Movie(
        data={
            'title': 'Same title',
            'akas': [
                {'title': 'Same title', 'language': 'en'},
                {'title': 'Same title', 'language': 'it'},
            ],
        }
    )

    scores = sortAKAsBySimilarity(movie, 'Same title', _titlesOnly=False)

    assert scores == [
        (1.0, 'Same title', None),
        (1.0, 'Same title', 'en'),
        (1.0, 'Same title', 'it'),
    ]
    assert sortAKAsBySimilarity(
        movie, 'Same title', _preferredLang='it'
    )[0] == 'Same title'
