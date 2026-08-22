import pytest

import logging
import os
from pathlib import Path

import imdb
from imdb import Cinemagoer
from imdb._exceptions import IMDbError
from imdb._logging import imdbpyLogger


def _write_config(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[imdbpy]\n%s\n' % content, encoding='utf-8')


def test_default_configuration_candidate_order(tmp_path, monkeypatch):
    current = tmp_path / 'current'
    home = tmp_path / 'home'
    current.mkdir()
    home.mkdir()
    monkeypatch.chdir(current)
    monkeypatch.setenv('HOME', str(home))

    candidates = imdb._config_file_candidates()

    assert candidates[:8] == [
        str(current / 'cinemagoer.cfg'),
        str(current / 'imdbpy.cfg'),
        str(current / '.cinemagoer.cfg'),
        str(current / '.imdbpy.cfg'),
        str(home / 'cinemagoer.cfg'),
        str(home / 'imdbpy.cfg'),
        str(home / '.cinemagoer.cfg'),
        str(home / '.imdbpy.cfg'),
    ]
    if os.name == 'posix':
        assert candidates[8:] == [
            '/etc/cinemagoer.cfg',
            '/etc/imdbpy.cfg',
            '/etc/conf.d/cinemagoer.cfg',
            '/etc/conf.d/imdbpy.cfg',
        ]


def test_discovery_prefers_location_then_current_filename(tmp_path, monkeypatch):
    current = tmp_path / 'current'
    home = tmp_path / 'home'
    current.mkdir()
    home.mkdir()
    monkeypatch.chdir(current)
    monkeypatch.setenv('HOME', str(home))
    _write_config(home / 'cinemagoer.cfg', 'results = 10')
    _write_config(current / 'imdbpy.cfg', 'results = 20')

    assert imdb.ConfigParserWithCase().get('imdbpy', 'results') == '20'

    _write_config(current / 'cinemagoer.cfg', 'results = 30')

    assert imdb.ConfigParserWithCase().get('imdbpy', 'results') == '30'


@pytest.mark.parametrize('path_type', [str, Path])
def test_explicit_configuration_accepts_string_and_pathlike(tmp_path, path_type):
    config = tmp_path / 'explicit.cfg'
    _write_config(config, 'results = 7')

    parser = imdb.ConfigParserWithCase(confFile=path_type(config))

    assert parser.get('imdbpy', 'results') == '7'


def test_configuration_converts_boolean_and_none_values(tmp_path):
    config = tmp_path / 'values.cfg'
    _write_config(
        config,
        'enabled = YES\ndisabled = off\nmissing = NoNe',
    )

    values = imdb.ConfigParserWithCase(confFile=config).getDict('imdbpy')

    assert values == {'enabled': True, 'disabled': False, 'missing': None}


def test_malformed_configuration_is_ignored_without_partial_state(
        tmp_path, caplog):
    malformed = tmp_path / 'malformed.cfg'
    malformed.write_text('[imdbpy]\nbroken line\n', encoding='utf-8')
    valid = tmp_path / 'valid.cfg'
    _write_config(valid, 'results = 12')

    with caplog.at_level(logging.WARNING, logger='imdbpy.aux'):
        parser = imdb.ConfigParserWithCase(confFile=[malformed, valid])

    assert parser.get('imdbpy', 'results') == '12'
    assert 'Troubles reading config file' in caplog.text


def test_configuration_applies_logging_level_and_exception_boolean(tmp_path):
    database = tmp_path / 'config.db'
    database.touch()
    config = tmp_path / 'cinemagoer.cfg'
    _write_config(
        config,
        'uri = sqlite:///%s\nloggingLevel = debug\nreraiseExceptions = off'
        % database,
    )
    previous_level = imdbpyLogger.level

    try:
        access = Cinemagoer(confFile=config)
        assert imdbpyLogger.level == logging.DEBUG
        assert access._reraise_exceptions is False
    finally:
        imdbpyLogger.setLevel(previous_level)


def test_invalid_logging_level_is_actionable(tmp_path):
    config = tmp_path / 'invalid-level.cfg'
    _write_config(config, 'loggingLevel = verbose')

    with pytest.raises(
            IMDbError,
            match=r"invalid loggingLevel 'verbose'; expected one of:.*warning"):
        Cinemagoer(confFile=config)


def test_exceptions_are_reraised_by_default(tmp_path):
    database = tmp_path / 'default.db'
    database.touch()

    access = Cinemagoer('s3', uri=f'sqlite:///{database}')

    assert access._reraise_exceptions is True
