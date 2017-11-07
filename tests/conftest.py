from pytest import fixture
from unittest import mock

import logging
import os
import urllib.request
from hashlib import md5
from io import BytesIO
from urllib.request import urlopen as orig_urlopen


logging.raiseExceptions = False


cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


def mock_urlopen(url):
    key = md5(url.encode('utf-8')).hexdigest()
    cache_file = os.path.join(cache_dir, key)
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            content = f.read()
    else:
        content = orig_urlopen(url).read()
        with open(cache_file, 'wb') as f:
            f.write(content)
    return BytesIO(content)


urllib.request.urlopen = mock.Mock(wraps=mock_urlopen)


BASE_URL = 'http://akas.imdb.com'

MOVIES = {
    'ace_in_the_hole':  '0043338',  # multiple languages
    'aslan':            '3629794',  # no cover url
    'ates_parcasi':     '1863157',  # no rating, no votes, no rank, no plot, no mpaa
    'band_of_brothers': '0185906',  # tv mini-series, ended series years
    'band_ep4':         '1247467',  # episode in mini-series
    'dr_who':           '0436992',  # tv series, continuing series years
    'dr_who_blink':     '1000252',  # tv episode
    'house':            '0412142',  # multiple seasons
    'house_first':      '0606035',  # first episode
    'house_middle':     '2121964',  # intermediate episode
    'house_last':       '2121965',  # last episode
    'if':               '0063850',  # one genre, multiple color info with notes
    'manos':            '0060666',  # bottom 100, single color info with notes
    'matrix':           '0133093',  # top 250
    'matrix_short':     '2971344',  # short movie, language "None"
    'matrix_tv':        '0389150',  # tv movie, no color info
    'matrix_tv_short':  '0274085',  # tv short movie
    'matrix_vg':        '0390244',  # video game
    'matrix_video':     '0109151',  # video movie
    'mothers_day4':     '3698420',  # IMDb index
    'pleasantville':    '0120789',  # multiple color info
    'roast_sheen':      '1985970',  # tv special
    'shining':          '0081505',  # multiple runtimes, multiple countries
    'suspiria':         '0076786'   # multiple country runtimes
}

PEOPLE = {
    'deni_gordon':   '0330139',  # no headshot
    'fred_astaire':  '0000001',  # name with dates
    'julia_roberts': '0000210',  # IMDb index
    'keanu_reeves':  '0000206'   # no IMDb index
}


@fixture(scope='session')
def movies():
    """Base addresses of all test movies."""
    return {k: '%(base)s/title/tt%(key)s' % {'base': BASE_URL, 'key': v}
            for k, v in MOVIES.items()}


@fixture(scope='session')
def people():
    """Base addresses of all test people."""
    return {k: '%(base)s/name/nm%(key)s' % {'base': BASE_URL, 'key': v}
            for k, v in PEOPLE.items()}
