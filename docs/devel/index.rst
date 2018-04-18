Development
===========

If you intend to do development on the IMDbPY package, it's recommended
that you create a virtual environment for it. For example::

   python -m venv ~/.virtualenvs/imdbpy
   . ~/.virtualenvs/imdbpy/bin/activate

In the virtual environment, install IMDbPY in editable mode and include
the extra packages. In the top level directory of the project (where
the :file:`setup.py` file resides), run::

   pip install -e .[dev,doc,test]


.. packages
  linguistics
        Defines some functions and data useful to smartly guess the language
        of a movie title (internally used).
  parser (package)
        A package containing a package for every data access system implemented.
  http (package)
        Contains the IMDbHTTPAccessSystem class which is a subclass
        of the imdb.IMDbBase class; it provides the methods used to retrieve and
        manage data from the web server (using, in turn, the other modules in
        the package). It defines methods to get a movie and to search for a title.
  The parser.sql package manages the access to the data in the SQL database,
  created with the imdbpy2sql.py script; see the README.sqldb file.
  The dbschema module contains tables definitions and some useful functions.
  The helpers module contains functions and other goodies not directly used
  by the IMDbPY package, but that can be useful to develop IMDbPY-based programs.


I wanted to stay independent from the source of the data for a given
movie/person/character/company, so the :func:`imdb.IMDb` function returns
an instance of a class that provides specific methods to access a given
data source (web server, SQL database, etc.).

Unfortunately this means that the ``movieID``
in the :class:`Movie <imdb.Movie.Movie>` class, the ``personID``
in the :class:`Person <imdb.Person.Person>` class, and the ``characterID``
in the :class:`Character <imdb.Character.Character>` class depend on
the data access system being used. So, when a movie, person, or character
object is instantiated, the ``accessSystem`` instance variable is set
to a string used to identify the used data access system.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   extend
   test
   translate
   release
