import gettext
import os

LOCALE_DIR = os.path.dirname(__file__)

gettext.bindtextdomain('imdbpy', LOCALE_DIR)
