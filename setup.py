import distutils.sysconfig
import os
import sys

import setuptools


# version of the software; in the code repository this represents
# the _next_ release.  setuptools will automatically add 'dev-rREVISION'.
version = '6.0'

home_page = 'https://imdbpy.sourceforge.io/'

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

dwnl_url = 'https://imdbpy.sourceforge.io/downloads.html'

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
Programming Language :: C
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
    './bin/get_movie.py',
    './bin/search_movie.py',
    './bin/get_first_person.py',
    './bin/get_person.py',
    './bin/search_person.py',
    './bin/get_character.py',
    './bin/get_first_character.py',
    './bin/get_company.py',
    './bin/search_character.py',
    './bin/search_company.py',
    './bin/get_first_company.py',
    './bin/get_keyword.py',
    './bin/search_keyword.py',
    './bin/get_top_bottom_movies.py'
]

# XXX: I'm not sure that 'etc' is a good idea.  Making it an absolute
#      path seems a recipe for a disaster (with bdist_egg, at least).
data_files = [('doc', setuptools.findall('docs')), ('etc', ['docs/imdbpy.cfg'])]


params = {
    # Meta-information.
    'name': 'IMDbPY',
    'version': version,
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
    'data_files': data_files,
    'install_requires': ['sqlalchemy-migrate', 'SQLAlchemy', 'lxml'],
    'extras_require': {
        'dev': ['flake8', 'flake8-isort'],
        'test': ['pytest', 'pytest-cov'],
    },
    'packages': setuptools.find_packages(),
    'package_data': {'imdb.parser.http': ['*.json']}
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
        import imp
        scriptPath = os.path.dirname(__file__)
        modulePath = os.path.join(cwd, scriptPath, REBUILDMO_DIR)
        sys.path += [modulePath, '.', cwd]
        modInfo = imp.find_module(REBUILDMO_NAME, [modulePath, '.', cwd])
        rebuildmo = imp.load_module('rebuildmo', *modInfo)
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
        languages = runRebuildmo()
    else:
        languages = []
    if languages:
        data_files.append((os.path.join(distutils.sysconfig.get_python_lib(), 'imdb/locale'),
                           ['imdb/locale/imdbpy.pot']))
    for lang in languages:
        files_found = setuptools.findall('imdb/locale/%s' % lang)
        if not files_found:
            continue
        base_dir = os.path.dirname(files_found[0])
        data_files.append((os.path.join(distutils.sysconfig.get_python_lib(), 'imdb/locale'),
                           ['imdb/locale/imdbpy-%s.po' % lang]))
        if not base_dir:
            continue
        data_files.append((os.path.join(distutils.sysconfig.get_python_lib(), base_dir),
                           files_found))
except SystemExit:
    print(ERR_MSG)

setuptools.setup(**params)
