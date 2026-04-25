from pytest import fixture

import hashlib
import logging
import os
import time

from imdb import Cinemagoer

logging.raiseExceptions = False

DELAY = 0

cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

s3_uri = os.getenv('CINEMAGOER_S3_URI')

@fixture(params=['s3'] if s3_uri is not None else [])
def ia(request):
    """Access to IMDb data."""
    if request.param == 's3':
        yield Cinemagoer('s3', uri=s3_uri)
