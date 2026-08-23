import pytest

from pathlib import Path

import imdb.helpers as helpers
from imdb._exceptions import IMDbError
from imdb.Character import Character
from imdb.Company import Company
from imdb.helpers import (
    akasLanguages,
    get_byURL,
    getAKAsInLanguage,
    makeModCGILinks,
    makeObject2Txt,
    makeTextNotes,
    resizeImage,
    sortAKAsBySimilarity,
)
from imdb.Movie import Movie
from imdb.Person import Person

PARTIAL_DB = Path(__file__).with_name('partial.db').resolve()


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


def test_text_and_container_formatters_work_with_caller_data():
    text_notes = makeTextNotes(
        '%(text)s<if notes> [%(notes)s]</if notes>'
    )
    assert text_notes('A summary::A source') == 'A summary [A source]'
    assert text_notes('A summary') == 'A summary'

    formatter = makeObject2Txt(
        movieTxt='%(title)s [%(movieID)s]',
        personTxt='%(name)s [%(personID)s]',
        characterTxt='%(name)s [%(characterID)s]',
        companyTxt='%(name)s [%(companyID)s]',
    )
    objects = [
        Movie(movieID='0000009', data={'title': 'Miss Jerry'}),
        Person(personID='0000001', data={'name': 'Fred Astaire'}),
        Character(characterID='1', data={'name': 'Hero'}),
        Company(companyID='2', data={'name': 'Example Studio'}),
    ]

    assert formatter(objects) == (
        'Miss Jerry [0000009] / Fred Astaire [0000001] / '
        'Hero [1] / Example Studio [2]'
    )


def test_reference_link_formatter_works_with_explicit_reference_maps():
    formatter = makeModCGILinks(
        movieTxt='<movie id="%(movieID)s">%(title)s</movie>',
        personTxt='<person id="%(personID)s">%(name)s</person>',
    )
    titles = {
        'Miss Jerry (1894)': Movie(
            movieID='0000009', data={'title': 'Miss Jerry', 'year': 1894}
        ),
    }
    names = {
        'Fred Astaire': Person(
            personID='0000001', data={'name': 'Fred Astaire'}
        ),
    }

    formatted = formatter(
        "_Miss Jerry (1894)_ (qv) and 'Fred Astaire' (qv)",
        titles,
        names,
    )

    assert formatted == (
        '<movie id="0000009">Miss Jerry (1894)</movie> and '
        '<person id="0000001">Fred Astaire</person>'
    )


@pytest.mark.parametrize(
    ('url', 'attribute', 'expected'),
    [
        ('https://www.imdb.com/title/tt0000009/', 'movieID', '0000009'),
        ('https://www.imdb.com/name/nm0000001/', 'personID', '0000001'),
        ('https://www.imdb.com/title/tt123456789/', 'movieID', '123456789'),
    ],
)
def test_get_by_url_uses_current_s3_retrieval(url, attribute, expected):
    item = get_byURL(
        url,
        kwds={'accessSystem': 's3', 'uri': f'sqlite:///{PARTIAL_DB}'},
    )

    assert getattr(item, attribute) == expected


def test_get_by_url_rejects_unsupported_container_urls():
    with pytest.raises(
        IMDbError,
        match='unsupported IMDb URL type for S3 access system: ch',
    ):
        get_byURL('https://www.imdb.com/character/ch0000001/')


def test_resize_image_operates_on_a_caller_provided_url():
    image = 'https://m.media-amazon.com/images/M/MV5Bexample._V1_.jpg'

    assert resizeImage(image, width=320) == (
        'https://m.media-amazon.com/images/M/MV5Bexample._V1_SX320_.jpg'
    )


def test_web_parser_only_full_size_cover_helper_was_removed():
    assert not hasattr(helpers, 'fullSizeCoverURL')


def test_character_and_company_remain_usable_compatibility_containers():
    movie = Movie(movieID='0000009', data={'title': 'Miss Jerry'})
    character = Character(
        characterID='1',
        data={
            'name': 'The Hero',
            'akas': ['Hero'],
            'filmography': [movie],
        },
    )
    company = Company(
        companyID='2',
        data={
            'name': 'Example Studio',
            'production companies': [movie],
        },
    )

    assert character['also known as'] == ['Hero']
    assert character['long imdb name'] == 'The Hero'
    assert movie in character
    assert company['production company'] == [movie]
    assert company['long imdb name'] == 'Example Studio'
    assert movie in company
