import os
import sys
import glob

import setuptools


# version of the software from imdb/version.py
exec(compile(open('imdb/version.py').read(), 'imdb/version.py', 'exec'))

home_page = 'https://cinemagoer.github.io/'

long_desc = """Cinemagoer is a Python package useful to retrieve and
manage the data of the IMDb movie database about movies, people,
characters and companies.

Cinemagoer and its authors are not affiliated in any way to
Internet Movie Database Inc.; see the DISCLAIMER.txt file for
details about data licenses.

Platform-independent and written in Python 3
it can retrieve data from both the IMDb's web server and a local copy
of the whole database.

Cinemagoer package can be very easily used by programmers and developers
to provide access to the IMDb's data to their programs.

Some simple example scripts - useful for the end users - are included
in this package; other Cinemagoer-based programs are available at the
home page: %s
""" % home_page

dwnl_url = 'https://cinemagoer.github.io/downloads/'

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

scripts = glob.glob('./bin/*.py')

params = {
    # Meta-information.
    'name': 'cinemagoer',
    'version': __version__,
    'description': 'Python package to access the IMDb\'s database',
    'long_description': long_desc,
    'author': 'Davide Alberani',
    'author_email': 'da@mimante.net',
    'maintainer': 'Davide Alberani',
    'maintainer_email': 'da@mimante.net',
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

  Anyway, if you were trying to build a package or install Cinemagoer to your
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
    if 'clean' in args:
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
