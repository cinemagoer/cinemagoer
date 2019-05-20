from pytest import fixture

import logging
import os
from hashlib import md5

from imdb import IMDb
from imdb.parser.http import IMDbURLopener


logging.raiseExceptions = False


cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


retrieve_unicode_orig = IMDbURLopener.retrieve_unicode


def retrieve_unicode_cached(self, url, size=-1):
    key = md5(url.encode('utf-8')).hexdigest()
    cache_file = os.path.join(cache_dir, key)
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            content = f.read()
    else:
        content = retrieve_unicode_orig(self, url, size=size)
        with open(cache_file, 'w') as f:
            f.write(content)
    return content


s3_uri = os.getenv('IMDBPY_S3_URI')


@fixture(params=['http'] + (['s3'] if s3_uri is not None else []))
def ia(request):
    """Access to IMDb data."""
    if request.param == 'http':
        IMDbURLopener.retrieve_unicode = retrieve_unicode_cached
        yield IMDb('http')
        IMDbURLopener.retrieve_unicode = retrieve_unicode_orig
    elif request.param == 's3':
        yield IMDb('s3', uri=s3_uri)
