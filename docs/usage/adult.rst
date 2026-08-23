Adult movies
============

Use :meth:`search_movie_advanced <imdb.IMDbBase.search_movie_advanced>` with
``adult=True`` to return only adult titles, or ``adult=False`` to return only
non-adult titles:

Before running the example, make sure you have imported IMDb non-commercial
datasets into SQLite with :file:`s32cinemagoer.py`.

.. code-block:: python

   >>> import imdb
   >>> ia = imdb.Cinemagoer(accessSystem='s3', uri='sqlite:///cinemagoer.db')
   >>> movies = ia.search_movie_advanced('debby does dallas', adult=True)

The ``adultSearch`` constructor option controls searches where ``adult`` is
not specified. Its historical default, ``adultSearch=True``, applies no adult
filter. Set it to ``False`` to exclude adult titles by default:

.. code-block:: python

   >>> ia = imdb.Cinemagoer(
   ...     accessSystem='s3',
   ...     uri='sqlite:///cinemagoer.db',
   ...     adultSearch=False,
   ... )

An explicit ``adult`` argument on ``search_movie_advanced`` overrides this
instance default. The S3 backend does not currently support custom sorting;
passing ``sort`` or ``sort_dir`` raises :class:`imdb.IMDbError` instead of
silently ignoring the request.
