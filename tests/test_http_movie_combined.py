from pytest import mark

import re

from imdb.Movie import Movie
from imdb.Person import Person


months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
re_date = re.compile(r'[0-9]{1,2} (%s) [0-9]{4}' % '|'.join(months), re.I)


def test_movie_cover_url_should_be_an_image_link(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert re.match(r'^https?://.*\.jpg$', movie.get('cover url'))


def test_cover_url_if_none_should_be_excluded(ia):
    movie = ia.get_movie('3629794', info=['main'])      # Aslan
    assert 'cover url' not in movie


def test_movie_directors_should_be_a_list_of_persons(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    directors = [p for p in movie.get('directors', [])]
    assert len(directors) == 2
    for p in directors:
        assert isinstance(p, Person)


def test_movie_directors_should_contain_correct_people(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    directorIDs = [p.personID for p in movie.get('directors', [])]
    assert directorIDs == ['0905154', '0905152']


def test_movie_directors_should_contain_person_names(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    director_names = [p.get('name') for p in movie.get('directors', [])]
    assert director_names == ['Lana Wachowski', 'Lilly Wachowski']


def test_movie_writers_should_be_a_list_of_persons(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    writers = [p for p in movie.get('writers', [])]
    assert len(writers) == 2
    for p in writers:
        assert isinstance(p, Person)


def test_movie_writers_should_contain_correct_people(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    writerIDs = [p.personID for p in movie.get('writer', [])]
    assert writerIDs == ['0905152', '0905154']


def test_movie_writers_should_contain_person_names(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    writer_names = [p.get('name') for p in movie.get('writers', [])]
    assert writer_names == ['Lilly Wachowski', 'Lana Wachowski']


def test_movie_title_should_not_have_year(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('title') == 'The Matrix'


def test_movie_title_tv_movie_should_not_include_type(ia):
    movie = ia.get_movie('0389150', info=['main'])      # Matrix (TV)
    assert movie.get('title') == 'The Matrix Defence'


def test_movie_title_video_movie_should_not_include_type(ia):
    movie = ia.get_movie('0109151', info=['main'])      # Matrix (V)
    assert movie.get('title') == 'Armitage III: Polymatrix'


def test_movie_title_video_game_should_not_include_type(ia):
    movie = ia.get_movie('0390244', info=['main'])      # Matrix (VG)
    assert movie.get('title') == 'The Matrix Online'


def test_movie_title_tv_series_should_not_have_quotes(ia):
    movie = ia.get_movie('0436992', info=['main'])      # Doctor Who
    assert movie.get('title') == 'Doctor Who'


def test_movie_title_tv_mini_series_should_not_have_quotes(ia):
    movie = ia.get_movie('0185906', info=['main'])      # Band of Brothers
    assert movie.get('title') == 'Band of Brothers'


def test_movie_title_tv_episode_should_not_be_series_title(ia):
    movie = ia.get_movie('1000252', info=['main'])      # Doctor Who - Blink
    assert movie.get('title') == 'Blink'


def test_movie_year_should_be_an_integer(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('year') == 1999


def test_movie_year_followed_by_kind_in_full_title_should_be_ok(ia):
    movie = ia.get_movie('0109151', info=['main'])      # Matrix (V)
    assert movie.get('year') == 1996


def test_movie_year_if_none_should_be_excluded(ia):
    movie = ia.get_movie('3629794', info=['main'])      # Aslan
    assert 'year' not in movie


@mark.skip(reason="imdb index is not included anymore")
def test_movie_imdb_index_should_be_a_roman_number(ia):
    movie = ia.get_movie('3698420', info=['main'])      # Mother's Day IV
    assert movie.get('imdbIndex') == 'IV'


@mark.skip(reason="imdb index is not included anymore")
def test_movie_imdb_index_none_should_be_excluded(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert 'imdbIndex' not in movie


def test_movie_kind_none_should_be_movie(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('kind') == 'movie'


def test_movie_kind_tv_movie_should_be_tv_movie(ia):
    movie = ia.get_movie('0389150', info=['main'])      # Matrix (TV)
    assert movie.get('kind') == 'tv movie'


def test_movie_kind_video_movie_should_be_video_movie(ia):
    movie = ia.get_movie('0109151', info=['main'])      # Matrix (V)
    assert movie.get('kind') == 'video movie'


def test_movie_kind_video_game_should_be_video_game(ia):
    movie = ia.get_movie('0390244', info=['main'])      # Matrix (VG)
    assert movie.get('kind') == 'video game'


def test_movie_kind_tv_series_should_be_tv_series(ia):
    movie = ia.get_movie('0436992', info=['main'])      # Doctor Who
    assert movie.get('kind') == 'tv series'


def test_movie_kind_tv_mini_series_should_be_tv_mini_series(ia):
    movie = ia.get_movie('0185906', info=['main'])      # Band of Brothers
    assert movie.get('kind') == 'tv mini series'


def test_movie_kind_tv_series_episode_should_be_episode(ia):
    movie = ia.get_movie('1000252', info=['main'])      # Doctor Who - Blink
    assert movie.get('kind') == 'episode'


# def test_movie_kind_short_movie_should_be_short_movie(ia):
#     movie = ia.get_movie('2971344', info=['main'])      # Matrix (Short)
#     assert movie.get('kind') == 'short movie'


# def test_movie_kind_tv_short_movie_should_be_tv_short_movie(ia):
#     movie = ia.get_movie('0274085', info=['main'])      # Matrix (TV Short)
#     assert movie.get('kind') == 'tv short movie'


# def test_movie_kind_tv_special_should_be_tv_special(ia):
#     movie = ia.get_movie('1985970', info=['main'])      # Roast of Charlie Sheen
#     assert movie.get('kind') == 'tv special'


def test_series_years_if_continuing_should_be_open_range(ia):
    movie = ia.get_movie('0436992', info=['main'])      # Doctor Who
    assert movie.get('series years') == '2005-'


def test_series_years_if_ended_should_be_closed_range(ia):
    movie = ia.get_movie('0412142', info=['main'])      # House M.D.
    assert movie.get('series years') == '2004-2012'


def test_series_years_mini_series_ended_in_same_year_should_be_closed_range(ia):
    movie = ia.get_movie('0185906', info=['main'])      # Band of Brothers
    assert movie.get('series years') == '2001-2001'


def test_series_years_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1000252', info=['main'])      # Doctor Who - Blink
    assert 'series years' not in movie


def test_series_number_of_episodes_should_be_an_integer(ia):
    movie = ia.get_movie('2121964', info=['main'])      # House M.D. - 8/21
    assert movie.get('number of episodes') == 176


def test_series_number_of_episodes_if_none_should_be_excluded(ia):
    movie = ia.get_movie('0412142', info=['main'])      # House M.D.
    assert 'number of episodes' not in movie


@mark.skip(reason="total episode number is not included anymore")
def test_episode_number_should_be_an_integer(ia):
    movie = ia.get_movie('2121964', info=['main'])      # House M.D. - 8/21
    assert movie.get('episode number') == 175


@mark.skip(reason="total episode number is not included anymore")
def test_episode_number_if_none_should_be_excluded(ia):
    movie = ia.get_movie('0412142', info=['main'])      # House M.D.
    assert 'episode number' not in movie


def test_episode_previous_episode_should_be_an_imdb_id(ia):
    movie = ia.get_movie('2121964', info=['main'])      # House M.D. - 8/21
    assert movie.get('previous episode') == '2121963'


def test_episode_previous_episode_if_none_should_be_excluded(ia):
    movie = ia.get_movie('0606035', info=['main'])      # House M.D. - 1/1
    assert 'previous episode' not in movie


def test_episode_next_episode_should_be_an_imdb_id(ia):
    movie = ia.get_movie('2121964', info=['main'])      # House M.D. - 8/21
    assert movie.get('next episode') == '2121965'


def test_episode_next_episode_if_none_should_be_excluded(ia):
    movie = ia.get_movie('2121965', info=['main'])      # House M.D. - 8/22
    assert 'next episode' not in movie


def test_episode_of_series_should_have_title_year_and_kind(ia):
    movie = ia.get_movie('2121964', info=['main'])      # House M.D. - 8/21
    series = movie.get('episode of')
    assert isinstance(series, Movie)
    assert series.movieID == '0412142'
    assert series.get('kind') == 'tv series'
    # original title and year are not included anymore
    # assert series.data == {'title': 'House M.D.', 'year': 2004, 'kind': 'tv series'}


def test_episode_of_mini_series_should_have_title_year_and_kind(ia):
    movie = ia.get_movie('1247467', info=['main'])      # Band of Brothers - 4
    series = movie.get('episode of')
    assert isinstance(series, Movie)
    assert series.movieID == '0185906'
    assert series.get('kind') == 'tv series'
    # original title and year are not included anymore
    # assert series.data == {'title': 'Band of Brothers', 'year': 2001, 'kind': 'tv series'}


def test_episode_of_series_if_none_should_be_excluded(ia):
    movie = ia.get_movie('0412142', info=['main'])      # House M.D.
    assert 'episode of' not in movie


def test_movie_rating_should_be_between_1_and_10(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert 1.0 <= movie.get('rating') <= 10.0


def test_movie_rating_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'rating' not in movie


def test_movie_votes_should_be_an_integer(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('votes') > 1000000


def test_movie_votes_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'votes' not in movie


def test_movie_top250_rank_should_be_between_1_and_250(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert 1 <= movie.get('top 250 rank') <= 250


def test_movie_top250_rank_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'top 250 rank' not in movie


def test_movie_bottom100_rank_should_be_between_1_and_100(ia):
    movie = ia.get_movie('0060666', info=['main'])      # Manos
    assert 1 <= movie.get('bottom 100 rank') <= 100


def test_movie_bottom100_rank_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'bottom 100 rank' not in movie


@mark.skip('seasons is an alias for number of seasons')
def test_series_season_titles_should_be_a_list_of_season_titles(ia):
    movie = ia.get_movie('0436992', info=['main'])      # Doctor Who
    assert movie.get('seasons', []) == [str(i) for i in range(1, 12)]
    # unknown doesn't show up in the reference page
    # assert movie.get('seasons', []) == [str(i) for i in range(1, 12)] + ['unknown']


def test_series_season_titles_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1000252', info=['main'])      # Doctor Who - Blink
    assert 'seasons' not in movie


def test_series_number_of_seasons_should_be_numeric(ia):
    movie = ia.get_movie('0412142', info=['main'])      # House M.D.
    assert movie.get('number of seasons') == 8


def test_series_number_of_seasons_should_exclude_non_numeric_season_titles(ia):
    movie = ia.get_movie('0436992', info=['main'])      # Doctor Who
    assert movie.get('number of seasons') == 13


def test_episode_original_air_date_should_be_a_date(ia):
    movie = ia.get_movie('1000252', info=['main'])      # Doctor Who - Blink
    assert re_date.match(movie.get('original air date'))


def test_episode_original_air_date_if_none_should_be_excluded(ia):
    movie = ia.get_movie('0436992', info=['main'])      # Doctor Who
    assert 'original air date' not in movie


def test_season_and_episode_numbers_should_be_integers(ia):
    movie = ia.get_movie('1000252', info=['main'])      # Doctor Who - Blink
    assert movie.get('season') == 3
    assert movie.get('episode') == 10


def test_season_and_episode_numbers_none_should_be_excluded(ia):
    movie = ia.get_movie('0436992', info=['main'])      # Doctor Who
    assert 'season' not in movie
    assert 'episode' not in movie


def test_movie_genres_if_single_should_be_a_list_of_genre_names(ia):
    movie = ia.get_movie('0389150', info=['main'])      # Matrix (TV)
    assert movie.get('genres', []) == ['Documentary']


def test_movie_genres_if_multiple_should_be_a_list_of_genre_names(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('genres', []) == ['Action', 'Sci-Fi']


# TODO: find a movie with no genre


def test_movie_plot_outline_should_be_a_longer_text(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert re.match(r'^Thomas A\. Anderson is a man .* human rebellion.$', movie.get('plot outline'))


def test_movie_plot_outline_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'plot outline' not in movie


@mark.skip(reason="mpaa rating is not included anymore")
def test_movie_mpaa_should_be_a_rating(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('mpaa') == 'Rated R for sci-fi violence and brief language'


@mark.skip(reason="mpaa rating is not included anymore")
def test_movie_mpaa_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'mpaa' not in movie


def test_movie_runtimes_single_should_be_a_list_in_minutes(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('runtimes', []) == ['136']


def test_movie_runtimes_with_countries_should_include_context(ia):
    movie = ia.get_movie('0076786', info=['main'])      # Suspiria
    assert movie.get('runtimes', []) == ['99']


def test_movie_runtimes_if_none_should_be_excluded(ia):
    movie = ia.get_movie('0390244', info=['main'])      # Matrix (VG)
    assert 'runtimes' not in movie


def test_movie_countries_if_single_should_be_a_list_of_country_names(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('countries', []) == ['United States']


def test_movie_countries_if_multiple_should_be_a_list_of_country_names(ia):
    movie = ia.get_movie('0081505', info=['main'])      # Shining
    assert movie.get('countries', []) == ['United Kingdom', 'United States']


# TODO: find a movie with no country


def test_movie_country_codes_if_single_should_be_a_list_of_country_codes(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('country codes', []) == ['us']


def test_movie_country_codes_if_multiple_should_be_a_list_of_country_codes(ia):
    movie = ia.get_movie('0081505', info=['main'])      # Shining
    assert movie.get('country codes', []) == ['gb', 'us']


# TODO: find a movie with no country


def test_movie_languages_if_single_should_be_a_list_of_language_names(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('languages', []) == ['English']


def test_movie_languages_if_multiple_should_be_a_list_of_language_names(ia):
    movie = ia.get_movie('0043338', info=['main'])      # Ace in the Hole
    assert movie.get('languages', []) == ['English', 'Spanish', 'Latin']


def test_movie_languages_none_as_a_language_name_should_be_valid(ia):
    movie = ia.get_movie('2971344', info=['main'])      # Matrix (Short)
    assert movie.get('languages', []) == ['None']


# TODO: find a movie with no language


def test_movie_language_codes_if_single_should_be_a_list_of_language_names(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('language codes', []) == ['en']


def test_movie_language_codes_if_multiple_should_be_a_list_of_language_names(ia):
    movie = ia.get_movie('0043338', info=['main'])      # Ace in the Hole
    assert movie.get('language codes', []) == ['en', 'es', 'la']


def test_movie_language_codes_zxx_as_a_language_code_should_be_valid(ia):
    movie = ia.get_movie('2971344', info=['main'])      # Matrix (Short)
    assert movie.get('language codes', []) == ['zxx']


# TODO: find a movie with no language


def test_movie_colors_if_single_should_be_a_list_of_color_types(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('color info', []) == ['Color']


def test_movie_colors_if_multiple_should_be_a_list_of_color_types(ia):
    # this used to return multiple colors, now it only returns the first
    movie = ia.get_movie('0120789', info=['main'])      # Pleasantville
    assert movie.get('color info', []) == ['Black and White']


def test_movie_cast_can_contain_notes(ia):
    movie = ia.get_movie('0060666', info=['main'])      # Manos
    diane_adelson = movie['cast'][2]
    assert str(diane_adelson.currentRole) == 'Margaret'
    assert diane_adelson.notes == '(as Diane Mahree)'


def test_movie_colors_if_single_with_notes_should_include_notes(ia):
    movie = ia.get_movie('0060666', info=['main'])      # Manos
    assert movie.get('color info', []) == ['Color::(Eastmancolor)']


def test_movie_colors_if_none_should_be_excluded(ia):
    movie = ia.get_movie('0389150', info=['main'])      # Matrix (TV)
    assert 'color info' not in movie


def test_movie_aspect_ratio_should_be_a_number_to_one(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie.get('aspect ratio') == '2.39 : 1'


def test_movie_aspect_ratio_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'aspect ratio' not in movie


def test_movie_sound_mix_if_single_should_be_a_list_of_sound_mix_types(ia):
    movie = ia.get_movie('0063850', info=['main'])      # If....
    assert movie.get('sound mix', []) == ['Mono']


def test_movie_sound_mix_if_multiple_should_be_a_list_of_sound_mix_types(ia):
    movie = ia.get_movie('0120789', info=['main'])      # Pleasantville
    assert movie.get('sound mix', []) == ['DTS', 'Dolby Digital', 'SDDS']


def test_movie_sound_mix_if_single_with_notes_should_include_notes(ia):
    movie = ia.get_movie('0043338', info=['main'])      # Ace in the Hole
    assert movie.get('sound mix', []) == ['Mono::(Western Electric Recording)']


def test_movie_sound_mix_if_multiple_with_notes_should_include_notes(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    expected = set(['DTS::(Digital DTS Sound)', 'Dolby Digital', 'SDDS', 'Dolby Atmos'])
    assert expected.issubset(set(movie.get('sound mix', [])))


def test_movie_sound_mix_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'sound mix' not in movie


def test_movie_certificates_should_be_a_list_of_certificates(ia):
    movie = ia.get_movie('1000252', info=['main'])      # Doctor Who - Blink
    assert movie.get('certificates', []) == [
        'Australia:PG::(most episodes)',
        'Brazil:12',
        'Netherlands:9::(some episodes)',
        'New Zealand:PG',
        'Singapore:PG',
        'South Africa:PG',
        'United Kingdom:PG',
        'United Kingdom:PG::(DVD rating)',
        'United States:TV-PG'
    ]


def test_movie_certificates_if_none_should_be_excluded(ia):
    movie = ia.get_movie('1863157', info=['main'])      # Ates Parcasi
    assert 'certificates' not in movie


def test_movie_cast_must_contain_items(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert len(movie.get('cast', [])) > 20


def test_movie_cast_must_be_in_plain_format(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie['cast'][0].data.get('name') == 'Keanu Reeves'


def test_movie_misc_sections_must_contain_items(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert len(movie.get('casting department', [])) == 2


def test_movie_misc_sections_must_be_in_plain_format(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert movie['casting department'][0].data.get('name') == 'Tim Littleton'


def test_movie_companies_sections_must_contain_items(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert len(movie.get('special effects companies', [])) == 7


def test_movie_box_office_should_be_a_dict(ia):
    movie = ia.get_movie('0133093', info=['main'])      # Matrix
    assert isinstance(movie.get('box office'), dict)
    assert len(movie.get('box office', {})) == 3
