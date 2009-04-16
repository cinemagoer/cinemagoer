#!/usr/bin/env python

import os
import ez_setup
ez_setup.use_setuptools()

import setuptools

# version of the software; in SVN this represents the _next_ release.
# setuptools will automatically add 'dev-rREVISION'.
version = '4.1'

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

keywords = ['imdb', 'movie', 'people', 'database', 'cinema', 'film', 'person',
            'cast', 'actor', 'actress', 'director', 'sql', 'character',
            'company', 'svn', 'package', 'plain text data files',
            'keywords', 'top250', 'bottom100', 'xml']


cutils = setuptools.Extension('imdb.parser.common.cutils',
                                ['imdb/parser/common/cutils.c'])

scripts = ['./bin/get_first_movie.py',
            './bin/get_movie.py', './bin/search_movie.py',
            './bin/get_first_person.py', './bin/get_person.py',
            './bin/search_person.py', './bin/get_character.py',
            './bin/get_first_character.py', './bin/get_company.py',
            './bin/search_character.py', './bin/search_company.py',
            './bin/get_first_company.py', './bin/get_keyword.py',
            './bin/search_keyword.py', './bin/get_top_bottom_movies.py']

# XXX: I'm not sure that 'etc' is a good idea.  Making it an absolute
#      path seems a recipe for a disaster (with bdist_egg, at least).
data_files = [('doc', [f for f in setuptools.findall('docs')
                if '.svn' not in f]), ('etc', ['docs/imdbpy.cfg'])]


# Defining these 'features', it's possible to run commands like:
# python ./setup.py --without-sql --without-local bdist
# having (in this example) imdb.parser.sql, imdb.parser.local (and
# their shared code in imdb.parser.common) removed.

featCutils = setuptools.dist.Feature('compile the C module', standard=True,
        ext_modules=[cutils])

featCommon = setuptools.dist.Feature('common code for "sql" and "local"',
        standard=False, remove='imdb.parser.common')

localScripts = ['./bin/characters4local.py', './bin/companies4local.py',
                './bin/misc-companies4local.py', './bin/mpaa4local.py',
                './bin/topbottom4local.py']
featLocal = setuptools.dist.Feature('access to local mkdb data', standard=True,
        require_features='common', remove='imdb.parser.local',
        scripts=localScripts)

featLxml = setuptools.dist.Feature('add lxml dependency', standard=True,
        install_requires=['lxml'])


# XXX: it seems there's no way to specify that we need EITHER
#      SQLObject OR SQLAlchemy.
featSQLObject = setuptools.dist.Feature('add SQLObject dependency',
        standard=True, install_requires=['SQLObject'],
        require_features='sql')

featSQLAlchemy = setuptools.dist.Feature('add SQLAlchemy dependency',
        standard=True, install_requires=['SQLAlchemy'],
        require_features='sql')

sqlScripts = ['./bin/imdbpy2sql.py']
featSQL = setuptools.dist.Feature('access to SQL databases', standard=False,
        require_features='common', remove='imdb.parser.sql', scripts=sqlScripts)

features = {
    'common': featCommon,
    'cutils': featCutils,
    'sql': featSQL,
    'local': featLocal,
    'lxml': featLxml,
    'sqlobject': featSQLObject,
    'sqlalchemy': featSQLAlchemy
}


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
        'classifiers': filter(None, classifiers.split("\n")),
        'zip_safe': True, # XXX: I guess, at least...
        # Download URLs.
        'url': home_page,
        'download_url': dwnl_url,
        # Scripts.
        'scripts': scripts,
        # Documentation files.
        'data_files': data_files,
        # C extensions.
        #'ext_modules': [cutils],
        # Requirements.  XXX: maybe we can use extras_require?
        #'install_requires': install_requires,
        #'extras_require': extras_require,
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
      --without-cutils      don't compile the C module (speeds up 'local/sql')
      --without-sqlobject   exclude SQLObject  (you need at least one of)
      --without-sqlalchemy  exclude SQLAlchemy (SQLObject or SQLAlchemy,)
                                               (if you want to access a )
                                               (local SQL database      )

  The following arguments exclude altogether some features of IMDbPY,
  in case you don't need them (if both are specified, the cutils C module
  is not compiled, either):
      --without-local       no access to local (mkdb generated) data.
      --without-sql         no access to SQL databases (implied if both
                            --without-sqlobject and --without-sqlalchemy
                            are used)

  Example:
      python ./setup.py --without-lxml --without-local --without-sql install

  The caught exception, is re-raise below:
"""


REBUILDMO_DIR = os.path.join('imdb', 'locale')
REBUILDMO_NAME = 'rebuildmo'

def runRebuildmo():
    """Call the function to rebuild the locales."""
    cwd = os.getcwd()
    import sys
    path = list(sys.path)
    try:
        import imp
        scriptPath =  os.path.dirname(__file__)
        modulePath = os.path.join(cwd, scriptPath, REBUILDMO_DIR)
        sys.path += [modulePath, '.', cwd]
        modInfo = imp.find_module(REBUILDMO_NAME, [modulePath, '.', cwd])
        rebuildmo = imp.load_module('rebuildmo', *modInfo)
        os.chdir(modulePath)
        languages = rebuildmo.rebuildmo()
        print 'Created locale for: %s.' % ' '.join(languages)
    except Exception, e:
        print 'ERROR: unable to rebuild .mo files; caught exception %s' % e
    sys.path = path
    os.chdir(cwd)


try:
    runRebuildmo()
    setuptools.setup(**params)
except SystemExit:
    print ERR_MSG
    raise

