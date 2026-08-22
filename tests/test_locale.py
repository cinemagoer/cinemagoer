import os
import subprocess
import sys


def test_missing_translation_catalogs_fall_back(tmp_path):
    script = '''
import gettext
import os

translation = gettext.translation


def use_empty_locale_dir(domain, localedir=None, *args, **kwargs):
    return translation(
        domain, os.environ['EMPTY_LOCALE_DIR'], *args, **kwargs
    )


gettext.translation = use_empty_locale_dir

from imdb.locale import _

assert _('untranslated text') == 'untranslated text'
'''
    environment = os.environ.copy()
    environment['EMPTY_LOCALE_DIR'] = str(tmp_path)

    subprocess.run(
        [sys.executable, '-c', script],
        check=True,
        env=environment,
    )
