import os
import sys

import setuptools


# version of the software from imdb/version.py
exec(compile(open('imdb/version.py').read(), 'imdb/version.py', 'exec'))

home_page = 'https://imdbpy.github.io/'

long_desc = """IMDbPY is a Python package useful to retrieve and
manage the data of the IMDb movie database about movies, people,
characters and companies.

Platform-independent and written in Python 3
it can retrieve data from both the IMDb's web server and a local copy
of the whole database.

IMDbPY package can be very easily used by programmers and developers
to provide access to the IMDb's data to their programs.

Some simple example scripts - useful for the end users - are included
in this package; other IMDbPY-based programs are available at the
home page: %s
""" % home_page

dwnl_url = 'https://imdbpy.github.io/downloads/'

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Console
Environment :: Web Environment
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License (GPL)
Natural Language :: English
Natural Language :: Italian
Natural Language :: Turkish
Programming Language :: Python
Programming Language :: Python :: 3.9
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.5
Programming Language :: Python :: 2.7
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Operating System :: OS Independent
Topic :: Database :: Front-Ends
Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries
Topic :: Software Development :: Libraries :: Python Modules
"""

keywords = ['imdb', 'movie', 'people', 'database', 'cinema', 'film', 'person',
            'cast', 'actor', 'actress', 'director', 'sql', 'character',
            'company', 'package', 'plain text data files',
            'keywords', 'top250', 'bottom100', 'xml']

scripts = [
    './bin/get_first_movie.py',
    './bin/imdbpy2sql.py',
    './bin/s32imdbpy.py',
    './bin/get_movie.py',
    './bin/search_movie.py',
    './bin/get_first_person.py',
    './bin/get_person.py',
    './bin/search_person.py',
    './bin/get_company.py',
    './bin/search_company.py',
    './bin/get_first_company.py',
    './bin/get_keyword.py',
    './bin/search_keyword.py',
    './bin/get_top_bottom_movies.py'
]

params = {
    # Meta-information.
    'name': 'IMDbPY',
    'version': __version__,
    'description': 'Python package to access the IMDb\'s database',
    'long_description': long_desc,
    'author': 'Davide Alberani',
    'author_email': 'da@erlug.linux.it',
    'contact': 'IMDbPY-devel mailing list',
    'contact_email': 'imdbpy-devel@lists.sourceforge.net',
    'maintainer': 'Davide Alberani',
    'maintainer_email': 'da@erlug.linux.it',
    'license': 'GPL',
    'platforms': 'any',
    'keywords': keywords,
    'classifiers': [_f for _f in classifiers.split("\n") if _f],
    'url': home_page,
    'download_url': dwnl_url,
    'scripts': scripts,
    'package_data': {
        # Here, the "*" represents any possible language ID.
        'imdb.locale': [
            'imdbpy.pot',
            'imdbpy-*.po',
            '*/LC_MESSAGES/imdbpy.mo',
        ],
    },
    'install_requires': ['SQLAlchemy', 'lxml'],
    'extras_require': {
        'dev': [
            'flake8',
            'flake8-isort',
            'readme_renderer'
        ],
        'doc': [
            'sphinx',
            'sphinx_rtd_theme'
        ],
        'test': [
            'pytest',
            'pytest-cov',
            'pytest-profiling'
        ]
    },
    'packages': setuptools.find_packages(),
    'entry_points': """
        [console_scripts]
        imdbpy=imdb.cli:main
    """
}


ERR_MSG = """
====================================================================
  ERROR
  =====

  Aaargh!  An error!  An error!
  Curse my metal body, I wasn't fast enough.  It's all my fault!

  Anyway, if you were trying to build a package or install IMDbPY to your
  system, looks like we're unable to fetch or install some dependencies.

  The best solution is to resolve these dependencies (maybe you're
  not connected to Internet?)

  The caught exception, is re-raise below:
"""


REBUILDMO_DIR = os.path.join('imdb', 'locale')
REBUILDMO_NAME = 'rebuildmo'


def runRebuildmo():
    """Call the function to rebuild the locales."""
    cwd = os.getcwd()
    path = list(sys.path)
    languages = []
    try:
        import importlib
        scriptPath = os.path.dirname(__file__)
        modulePath = os.path.join(cwd, scriptPath, REBUILDMO_DIR)
        sys.path += [modulePath, '.', cwd]
        rebuildmo = importlib.import_module(os.path.join(REBUILDMO_DIR, REBUILDMO_NAME).replace(os.path.sep, '.'))
        os.chdir(modulePath)
        languages = rebuildmo.rebuildmo()
        print('Created locale for: %s.' % ' '.join(languages))
    except Exception as e:
        print('ERROR: unable to rebuild .mo files; caught exception %s' % e)
    sys.path = path
    os.chdir(cwd)
    return languages


def hasCommand():
    """Return true if at least one command is found on the command line."""
    args = sys.argv[1:]
    if '--help' in args:
        return False
    if '-h' in args:
        return False
    for arg in args:
        if arg and not arg.startswith('-'):
            return True
    return False


try:
    if hasCommand():
        runRebuildmo()
except SystemExit:
    print(ERR_MSG)

setuptools.setup(**params)
