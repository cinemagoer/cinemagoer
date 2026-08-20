Distribution maintainers
========================

Cinemagoer's core runtime dependencies are declared in the ``dependencies``
array of :file:`pyproject.toml`. As of this release, SQLAlchemy is no longer a
core dependency: it is declared in the ``sqlalchemy`` optional-dependency
extra. Maintainers upgrading an existing distribution package should remove
SQLAlchemy from the mandatory dependency set.

The base package supports SQLite without SQLAlchemy. It uses Python's
standard-library :mod:`sqlite3` module for both importing datasets and querying
them. Distribution packages should therefore not make SQLAlchemy a mandatory
dependency, but they must use a Python build with SQLite support enabled.

Non-SQLite databases
--------------------

PostgreSQL, MariaDB, MySQL, and other SQLAlchemy dialects require both:

* the dependencies declared by the ``sqlalchemy`` extra; and
* an appropriate SQLAlchemy DBAPI driver, such as ``psycopg`` for PostgreSQL.

Database drivers are deliberately not included in the extra because the
correct driver depends on the database selected by the user. A distribution
can expose the SQLAlchemy integration according to its normal optional-feature
or subpackage conventions. If extras are supported directly, its upstream
installation form is::

   pip install "cinemagoer[sqlalchemy]"

Do not infer runtime requirements from Cinemagoer's ``dev`` dependency group.
That group includes SQLAlchemy so the complete adapter test suite can run, but
it does not describe the dependencies of the base package.

Adapter selection
-----------------

Canonical ``sqlite:`` URIs, including ``sqlite:///cinemagoer.db``, always use
the native :mod:`sqlite3` implementation, even when SQLAlchemy is installed.
All other database dialects are loaded lazily through SQLAlchemy. An explicit
SQLAlchemy SQLite dialect such as ``sqlite+pysqlite:`` also selects the
optional SQLAlchemy implementation.

This design allows importing ``imdb`` and using SQLite when SQLAlchemy is not
installed. Downstream patches should preserve the lazy import and must not
import :mod:`imdb.parser.s3.sqlalchemy_adapter` from the base SQLite path.

Downstream smoke tests
----------------------

In an environment containing only the base distribution package, verify that
SQLAlchemy is absent and that Cinemagoer selects its native adapter::

   python -c "import importlib.util; assert importlib.util.find_spec('sqlalchemy') is None"
   python -c "from imdb import Cinemagoer; from imdb.parser.s3.adapters import SQLiteAdapter; ia = Cinemagoer('s3', uri='sqlite://'); assert isinstance(ia._adapter, SQLiteAdapter)"

For an optional SQLAlchemy package, install one supported DBAPI driver and run
an integration test against that database. The test should assert the actual
dialect as well as perform a Cinemagoer query; the PostgreSQL Docker example in
:ref:`s3` provides a complete setup.
