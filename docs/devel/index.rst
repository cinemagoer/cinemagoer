Development
===========

If you intend to do development on the Cinemagoer package, it's recommended
that you create a virtual environment for it. For example::

   python -m venv ~/.virtualenvs/cinemagoer
   . ~/.virtualenvs/cinemagoer/bin/activate

In the virtual environment, install Cinemagoer in editable mode. In the top
level directory of the project (where the :file:`pyproject.toml` file resides),
run::

      pip install -e .


.. packages
  linguistics
        Defines some functions and data useful to smartly guess the language
        of a movie title (internally used).
  parser (package)
        Contains the S3 dataset data access implementation in parser.s3.
  parser.s3 (package)
        Contains the IMDbS3AccessSystem class, a subclass of imdb.IMDbBase.
        It retrieves and manages data from a SQL database populated from IMDb
        downloadable datasets.
  The helpers module contains functions and other goodies not directly used
  by the Cinemagoer package, but that can be useful to develop
  Cinemagoer-based programs.


The :func:`imdb.IMDb` function returns an instance of the S3 data access
system, which provides methods to query a database created from IMDb
downloadable datasets.

Unfortunately this means that the ``movieID``
in the :class:`Movie <imdb.Movie.Movie>` class and the ``personID``
in the :class:`Person <imdb.Person.Person>` class depend on
the data access system. So, when a movie or person object is instantiated,
the ``accessSystem`` instance variable is set to identify the active system.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   test
   translate
   release
