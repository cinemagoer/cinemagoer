#!/usr/bin/env python

from __future__ import print_function, unicode_literals
import distutils.sysconfig
import os
import sys
import ez_setup
ez_setup.use_setuptools()

import setuptools

# version of the software; in the code repository this represents
# the _next_ release.  setuptools will automatically add 'dev-rREVISION'.
version = '0.1'

home_page = 'https://github.com/abhiravk/imdbpy3'

long_desc = """IMDbPY is a Python package useful to retrieve and
manage the data of the IMDb movie database about movies.
"""

dwnl_url = 'https://github.com/abhiravk/imdbpy3'

classifiers = """\
Development Status :: 1 - Development
Environment :: Console
Environment :: Web Environment
Environment :: Handhelds/PDA's
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License (GPL)
Natural Language :: English
Natural Language :: Italian
Natural Language :: Turkish
Programming Language :: Python
Operating System :: OS Independent
Topic :: Database :: Front-Ends
Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries
Topic :: Software Development :: Libraries :: Python Modules
"""

keywords = ['imdb', 'movie', 'people', 'database', 'cinema', 'film', 'person',
            'cast', 'actor', 'actress', 'director', 'sql', 'character',
            'company', 'package', 'plain text data files',
            'keywords', 'top250', 'bottom100', 'xml']


# XXX: I'm not sure that 'etc' is a good idea.  Making it an absolute
#      path seems a recipe for a disaster (with bdist_egg, at least).
data_files = [('doc', setuptools.findall('docs')), ('etc', ['docs/imdbpy.cfg'])]


# Defining these 'features', it's possible to run commands like:
# python ./setup.py --without-sql bdist
# having (in this example) imdb.parser.sql removed.

featLxml = setuptools.dist.Feature('add lxml dependency', standard=True,
        install_requires=['lxml'])

# XXX: it seems there's no way to specify that we need EITHER
#      SQLObject OR SQLAlchemy.
featSQLAlchemy = setuptools.dist.Feature('add SQLAlchemy dependency',
        standard=True, install_requires=['SQLAlchemy', 'sqlalchemy-migrate'],
        require_features='sql')

features = {
    'lxml': featLxml,
    'sqlalchemy': featSQLAlchemy
}

params = {
        # Meta-information.
        'name': 'IMDbPY3',
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
        'classifiers': filter(None, classifiers.split("\n")),
        #'zip_safe': False, # XXX: I guess, at least...
        # Download URLs.
        'url': home_page,
        'download_url': dwnl_url,
        # Documentation files.
        'data_files': data_files,
        'features': features,
        # Packages.
        'packages': setuptools.find_packages()
}

ERR_MSG = """
====================================================================
  ERROR
  =====

  Aaargh!  An error!  An error!
  Curse my metal body, I wasn't fast enough.  It's all my fault!

  Anyway, if you were trying to build a package or install IMDbPY to your
  system, looks like we're unable to fetch or install some dependencies,
  or to compile the C module.

  The best solution is to resolve these dependencies (maybe you're
  not connected to Internet?) and/or install a C compiler.

  You may, however, go on without some optional pieces of IMDbPY;
  try re-running this script with the corresponding optional argument:

      --without-lxml        exclude lxml (speeds up 'http')
      --without-sqlalchemy  exclude SQLAlchemy (SQLObject or SQLAlchemy,)
                                               (if you want to access a )
                                               (local SQL database      )
  Example:
      python ./setup.py --without-lxml install

  The caught exception, is re-raise below:
"""

REBUILDMO_DIR = os.path.join('imdb', 'locale')
REBUILDMO_NAME = 'rebuildmo'

def runRebuildmo():
    """Call the function to rebuild the locales."""
    cwd = os.getcwd()
    import sys
    path = list(sys.path)
    languages = []
    try:
        import imp
        scriptPath =  os.path.dirname(__file__)
        modulePath = os.path.join(cwd, scriptPath, REBUILDMO_DIR)
        sys.path += [modulePath, '.', cwd]
        modInfo = imp.find_module(REBUILDMO_NAME, [modulePath, '.', cwd])
        rebuildmo = imp.load_module('rebuildmo', *modInfo)
        os.chdir(modulePath)
        languages = rebuildmo.rebuildmo()
        print('Created locale for: {}'.format(languages))
    except Exception as e:
        print('ERROR: unable to rebuild .mo files; caught exception {}'.format(e))
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
        data_files.append((os.path.join(distutils.sysconfig.get_python_lib(), 'imdb/locale'), ['imdb/locale/imdbpy.pot']))
    for lang in languages:
        files_found = setuptools.findall('imdb/locale/%s' % lang)
        if not files_found:
            continue
        base_dir = os.path.dirname(files_found[0])
        data_files.append((os.path.join(distutils.sysconfig.get_python_lib(), 'imdb/locale'), ['imdb/locale/imdbpy-%s.po' % lang]))
        if not base_dir:
            continue
        data_files.append((os.path.join(distutils.sysconfig.get_python_lib(), base_dir), files_found))
    setuptools.setup(**params)
except SystemExit:
    print(ERR_MSG)
    raise
