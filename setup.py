#!/usr/bin/env python

import sys
from distutils.core import setup, Extension

home_page = 'http://imdbpy.sourceforge.net/'

long_desc = """IMDbPY is a Python package useful to retrieve and
manage the data of the IMDb movie database.

IMDbPY aims to provide an easy way to access the IMDb's database using
a Python script.
Platform-independent and written in pure Python, it's independent
from the data source (since IMDb provides two or three different
interfaces to their database).
IMDbPY is mainly intended for programmers and developers who want to
build their Python programs using the IMDbPY package, but some
example scripts - useful for the end users - are included. 
Other IMDbPY-based programs are available at the home page:
%s
""" % home_page

dwnl_url = 'http://sourceforge.net/project/showfiles.php?group_id=105998'

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Console
Environment :: Web Environment
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License (GPL)
Natural Language :: English
Programming Language :: Python
Operating System :: OS Independent
Topic :: Database :: Front-Ends
Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries
Topic :: Software Development :: Libraries :: Python Modules
"""

ratober = Extension('imdb.parser.local.ratober',
                    ['imdb/parser/local/ratober.c'])

params = {'name': 'IMDbPY',
      'version': '1.7',
      'description': 'Python package to access the IMDb database',
      'long_description': long_desc,
      'author': 'Davide Alberani',
      'author_email': 'da@erlug.linux.it',
      'maintainer': 'Davide Alberani',
      'maintainer_email': 'da@erlug.linux.it',
      'url': home_page,
      'license': 'GPL',
      'scripts': ['./bin/get_first_movie', './bin/get_movie',
                './bin/search_movie', './bin/get_first_person',
                './bin/get_person', './bin/search_person'],
      'packages': ['imdb', 'imdb.parser',
                    'imdb.parser.http', 'imdb.parser.local'],
      'ext_modules': [ratober]}


if sys.version_info >= (2, 1):
    params['keywords'] = ['imdb', 'movie', 'people', 'database', 'cinema',
                            'film']
    params['platforms'] = 'any'

if sys.version_info >= (2, 3):
    params['download_url'] = dwnl_url
    params['classifiers'] = filter(None, classifiers.split("\n"))


setup(**params)

