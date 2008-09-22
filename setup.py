#!/usr/bin/env python

import sys
from distutils.core import setup, Extension

# --- CONFIGURE

# XXX NOTE: if you _really_ don't want to install the "local data access
# system", set DO_LOCAL to 0.
# The local access system requires the _whole_ IMDb's database installed
# in your computer; this not useful/possible in small devices like
# hand-held computers, where it makes sense to also save the little space
# taken by the local interface package.
# When possible it's _always safer_ to leave it to 1.
DO_LOCAL = 1

# XXX NOTE: the "sql data access system" requires the MySQLdb python
# module and a connection to a database with the whole IMDb data,
# that must be create using the imdbpy2sql.py script.
# Setting this to 1 will always install at least the imdbpy2sql.py script.
DO_SQL = 1

# XXX NOTE: setting at least one of DO_LOCAL and DO_SQL to 1,
# the "cutils" C module will be compiled; if you don't have a C compiler
# in your environment, pure-python versions of the functions in the
# C module will be used.  Beware the they are extremely slow, especially
# using the "local" data access system.

# Install some very simple example scripts.
DO_SCRIPTS = 1


# --- NOTHING TO CONFIGURE BELOW, GO AWAY! ;-)

# version of the software; CVS releases contain a string
# like ".cvsYearMonthDay(OptionalChar)".
version = '3.7'

home_page = 'http://imdbpy.sf.net/'

long_desc = """IMDbPY is a Python package useful to retrieve and
manage the data of the IMDb movie database about movies, people,
characters and companies.

Platform-independent and written in pure Python (and few C lines),
it can retrieve data from both the IMDb's web server and a local copy
of the whole database.

IMDbPY package can be very easily used by programmers and developers
to provide access to the IMDb's data to their programs.

Some simple example scripts - useful for the end users - are included
in this package; other IMDbPY-based programs are available at the
home page: %s
""" % home_page

dwnl_url = 'http://imdbpy.sf.net/?page=download'

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Console
Environment :: Web Environment
Environment :: Handhelds/PDA's
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License (GPL)
Natural Language :: English
Programming Language :: Python
Programming Language :: C
Operating System :: OS Independent
Topic :: Database :: Front-Ends
Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries
Topic :: Software Development :: Libraries :: Python Modules
"""

params = {'name': 'IMDbPY',
      'version': version,
      'description': 'Python package to access the IMDb\'s database',
      'long_description': long_desc,
      'author': 'Davide Alberani',
      'author_email': 'da@erlug.linux.it',
      'contact': 'IMDbPY-devel mailing list',
      'contact_email': 'imdbpy-devel@lists.sourceforge.net',
      'maintainer': 'Davide Alberani',
      'maintainer_email': 'da@erlug.linux.it',
      'url': home_page,
      'license': 'GPL',
      'packages': ['imdb', 'imdb.parser', 'imdb.parser.http',
                    'imdb.parser.mobile']}


if DO_LOCAL or DO_SQL:
    params['packages'] = params['packages'] + ['imdb.parser.common']
    cutils = Extension('imdb.parser.common.cutils',
                        ['imdb/parser/common/cutils.c'])
    params['ext_modules'] = [cutils]
    params['scripts'] = []

if DO_LOCAL:
    params['packages'] = params['packages'] + ['imdb.parser.local']
    params['scripts'] = params['scripts'] + ['./bin/characters4local.py',
                                            './bin/companies4local.py',
                                            './bin/mpaa4local.py',
                                            './bin/misc-companies4local.py']

if DO_SQL:
    params['packages'] = params['packages'] + ['imdb.parser.sql']
    params['scripts'] = params['scripts'] + ['./bin/imdbpy2sql.py']

if DO_SCRIPTS:
    if not params.has_key('scripts'): params['scripts'] = []
    params['scripts'] = params['scripts'] + ['./bin/get_first_movie.py',
                        './bin/get_movie.py', './bin/search_movie.py',
                        './bin/get_first_person.py', './bin/get_person.py',
                        './bin/search_person.py', './bin/get_character.py',
                        './bin/get_first_character.py', './bin/get_company.py',
                        './bin/search_character.py', './bin/search_company.py',
                        './bin/get_first_company.py']


if sys.version_info >= (2, 1):
    params['keywords'] = ['imdb', 'movie', 'people', 'database', 'cinema',
                            'film', 'person', 'cast', 'actor', 'actress',
                            'director', 'sql', 'character', 'company']
    params['platforms'] = 'any'

if sys.version_info >= (2, 3):
    params['download_url'] = dwnl_url
    params['classifiers'] = filter(None, classifiers.split("\n"))


try:
    setup(**params)
except SystemExit, e:
    print '    WARNING ! WARNING ! WARNING ! WARNING ! WARNING'
    print '    WARNING: '
    print '    WARNING: Unable to compile the "cutils" C module.'
    print '    WARNING: Error message:'
    print '    WARNING:     "%s"' % str(e)
    print '    WARNING: '
    print '    WARNING: Restarting the setup process excluding the C module.'
    print '    WARNING: Beware that the "sql" data access system will be'
    print '    WARNING: slow, and the "local" data access system will be'
    print '    WARNING: _really_ slow.'
    print '    WARNING: '
    print '    WARNING ! WARNING ! WARNING ! WARNING ! WARNING'
    del params['ext_modules']
    setup(**params)


