from pytest import fixture

import logging
import os
from pathlib import Path

from imdb import Cinemagoer

logging.raiseExceptions = False

DELAY = 0

cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

partial_db = Path(__file__).with_name('partial.db').resolve()
s3_uri = os.getenv('CINEMAGOER_S3_URI', f'sqlite:///{partial_db}')

@fixture(params=['s3'])
def ia(request):
    """Access to IMDb data."""
    if request.param == 's3':
        yield Cinemagoer('s3', uri=s3_uri)
