from pytest import fixture

import hashlib
import logging
import os
import time

from imdb import Cinemagoer
from imdb.parser.http import IMDbURLopener

logging.raiseExceptions = False

DELAY = 0


cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


retrieve_unicode_orig = IMDbURLopener.retrieve_unicode


def retrieve_unicode_cached(self, url, size=-1, timeout=None):
    key = "_".join(url.split("/")[3:])
    # Sanitize filename for Windows - replace invalid characters
    key = key.replace('?', '_Q_').replace('&', '_A_').replace('=', '_E_')
    key = key.replace(':', '_C_').replace('*', '_S_').replace('<', '_L_')
    key = key.replace('>', '_G_').replace('"', '_D_').replace('|', '_P_')
    # Windows has a 260 char path limit; if key is too long, hash it
    if len(key) > 150:
        key = hashlib.md5(key.encode('utf-8')).hexdigest()
    cache_file = os.path.join(cache_dir, key)
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        time.sleep(DELAY)
        content = retrieve_unicode_orig(self, url, size=size, timeout=timeout)
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(content)
    return content


s3_uri = os.getenv('CINEMAGOER_S3_URI')


@fixture(params=['http'] + (['s3'] if s3_uri is not None else []))
def ia(request):
    """Access to IMDb data."""
    if request.param == 'http':
        IMDbURLopener.retrieve_unicode = retrieve_unicode_cached
        yield Cinemagoer('http')
        IMDbURLopener.retrieve_unicode = retrieve_unicode_orig
    elif request.param == 's3':
        yield Cinemagoer('s3', uri=s3_uri)
