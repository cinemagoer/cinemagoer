# -*- coding: utf-8 -*-
from pytest import mark


def test_search_movie_if_single_should_list_one_movie(ia):
    movies = ia.search_movie('od instituta do proizvodnje')
    assert len(movies) == 1
    assert movies[0].movieID == '0483758'
    assert movies[0]['kind'] == 'short'
    assert movies[0]['title'] == 'Od instituta do proizvodnje'
    assert movies[0]['year'] == 1971


def test_search_movie_should_list_default_number_of_movies(ia):
    movies = ia.search_movie('movie')
    assert len(movies) == 20


@mark.skip(reason="number of results limit is not honored anymore")
def test_search_movie_limited_should_list_requested_number_of_movies(ia):
    movies = ia.search_movie('ace in the hole', results=98)
    assert len(movies) == 98


def test_search_movie_unlimited_should_list_correct_number_of_movies(ia):
    movies = ia.search_movie('ace in the hole', results=500)
    assert len(movies) == 25


def test_search_movie_if_too_many_result_should_list_upper_limit_of_movies(ia):
    movies = ia.search_movie('matrix', results=500)
    assert len(movies) == 25


def test_search_movie_if_none_should_be_empty(ia):
    movies = ia.search_movie('ᚣ', results=500)
    assert movies == []


def test_search_movie_entries_should_include_movie_id(ia):
    movies = ia.search_movie('matrix')
    assert movies[0].movieID == '0133093'


def test_search_movie_entries_should_include_movie_title(ia):
    movies = ia.search_movie('matrix')
    assert movies[0]['title'] == 'The Matrix'


def test_search_movie_entries_should_include_cover_url_if_available(ia):
    movies = ia.search_movie('matrix')
    assert 'cover url' in movies[0]


def test_search_movie_entries_should_include_movie_kind(ia):
    movies = ia.search_movie('matrix')
    assert movies[0]['kind'] == 'movie'


def test_search_movie_entries_should_include_movie_kind_if_other_than_movie(ia):
    movies = ia.search_movie('matrix')
    tv_series = [m for m in movies if m.movieID == '0106062']
    assert len(tv_series) == 1
    assert tv_series[0]['kind'] == 'tv series'


def test_search_movie_entries_should_include_movie_year(ia):
    movies = ia.search_movie('matrix')
    assert movies[0]['year'] == 1999


@mark.skip(reason="index is no longer shown on search results")
def test_search_movie_entries_should_include_imdb_index(ia):
    movies = ia.search_movie('blink')
    movie_with_index = [m for m in movies if m.movieID == '6544524']
    assert len(movie_with_index) == 1
    assert movie_with_index[0]['imdbIndex'] == 'XXIV'


def test_search_movie_entries_missing_imdb_index_should_be_excluded(ia):
    movies = ia.search_movie('matrix')
    assert 'imdbIndex' not in movies[0]


@mark.skip(reason="AKAs are no longer shown on search results")
def test_search_movie_entries_should_include_akas(ia):
    movies = ia.search_movie('Una calibro 20 per lo specialista')
    movie_with_aka = [m for m in movies if m.movieID == '0072288']
    assert len(movie_with_aka) == 1
    assert movie_with_aka[0]['akas'] == ['Una calibro 20 per lo specialista']


def test_search_movie_entries_missing_akas_should_be_excluded(ia):
    movies = ia.search_movie('matrix')
    assert 'akas' not in movies[0]


@mark.skip(reason="episode title are no longer shown on search results")
def test_search_movie_episodes_should_include_season_and_number(ia):
    movies = ia.search_movie('swarley')  # How I Met Your Mother S02E07
    movie_with_season_and_episode = [m for m in movies if m.movieID == '0875360']
    assert len(movie_with_season_and_episode) == 1
    assert movie_with_season_and_episode[0]['season'] == 2
    assert movie_with_season_and_episode[0]['episode'] == 7


def test_search_movie_entries_tv_mini_series_should_have_correct_kind(ia):
    movies = ia.search_movie('capture 2019')  # The Capture (2019)
    miniseries = [m for m in movies if m.movieID == '8201186']
    assert len(miniseries) == 1
    miniseries[0]['kind'] == 'tv mini series'
