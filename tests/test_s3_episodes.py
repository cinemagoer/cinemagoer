import sqlite3
from contextlib import closing

from imdb import Cinemagoer
from imdb.helpers import sortedEpisodes, sortedSeasons


def test_get_all_series_episodes_from_partial_database(ia):
    series = ia.get_movie('989125', info=['episodes'])

    assert 'episodes' in ia.get_movie_infoset()
    assert series.current_info == ['episodes']
    assert series['number of episodes'] == 13
    assert sortedSeasons(series) == [1, 2, 3, 4, 5, 6, 9, 'unknown season']
    assert sorted(series['episodes'][2]) == [8, 16]

    episode = series['episodes'][2][8]
    assert episode.movieID == 43693
    assert episode['seasonNr'] == 2
    assert episode['episodeNr'] == 8
    assert episode['episode of'].movieID == 989125

    unknown_episode = series['episodes']['unknown season']['tt0042889']
    assert unknown_episode.movieID == 42889
    assert unknown_episode.get('seasonNr') is None
    assert unknown_episode.get('episodeNr') is None

    season_six = sortedEpisodes(series, season=6)
    assert [episode['episodeNr'] for episode in season_six] == [5, 11, 42]
    assert len(sortedEpisodes(series)) == 13


def test_get_episode_links_to_its_parent_series(ia):
    episode = ia.get_movie('42816')

    assert episode['episode of'].movieID == 989125
    assert episode['seasonNr'] == 1
    assert episode['episodeNr'] == 17


def test_update_selected_series_seasons_from_partial_database(ia):
    series = ia.get_movie('989125', info=[])

    ia.update_series_seasons(series, [2])

    assert series['number of episodes'] == 2
    assert list(series['episodes']) == [2]
    assert sorted(series['episodes'][2]) == [8, 16]


def test_episode_titles_years_ratings_and_duplicate_numbers(tmp_path):
    database = tmp_path / 'episodes.db'
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript(
            '''
            CREATE TABLE title_basics (
                tconst INTEGER,
                primaryTitle TEXT,
                titleType TEXT,
                startYear INTEGER
            );
            CREATE TABLE title_episode (
                tconst INTEGER,
                parentTconst INTEGER,
                seasonNumber INTEGER,
                episodeNumber INTEGER
            );
            CREATE TABLE title_ratings (
                tconst INTEGER,
                averageRating FLOAT,
                numVotes INTEGER
            );
            INSERT INTO title_basics VALUES
                (100, 'Example Series', 'tv series', 2020),
                (101, 'Pilot', 'episode', 2020),
                (102, 'Special', 'episode', 2021),
                (103, 'Alternate Pilot', 'episode', 2020);
            INSERT INTO title_episode VALUES
                (101, 100, 1, 1),
                (102, 100, NULL, NULL),
                (103, 100, 1, 1);
            INSERT INTO title_ratings VALUES (101, 8.5, 42);
            '''
        )

    with Cinemagoer('s3', uri=f'sqlite:///{database}') as ia:
        series = ia.get_movie('100', info=['episodes'])

    assert series['number of episodes'] == 3
    pilot = series['episodes'][1][1]
    assert pilot['title'] == 'Pilot'
    assert pilot['year'] == '2020'
    assert pilot['rating'] == 8.5
    assert pilot['votes'] == 42
    assert pilot['episode of']['title'] == 'Example Series'

    duplicate = series['episodes'][1]['tt0000103']
    assert duplicate['title'] == 'Alternate Pilot'
    assert duplicate['episodeNr'] == 1

    special = series['episodes']['unknown season']['tt0000102']
    assert special['title'] == 'Special'
    assert special['year'] == '2021'
