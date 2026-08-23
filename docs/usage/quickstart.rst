Quick start
===========

The first thing to do is to import :mod:`imdb` and call the :mod:`imdb.IMDb`
function to get an access object through which IMDb data can be retrieved:

.. important::

   Before creating the access object, download IMDb non-commercial datasets
   from https://datasets.imdbws.com/ (or run ``download-from-s3``)
   and import them into SQLite:

   .. code-block:: bash

      s32cinemagoer.py /path/to/imdb-tsv-files/ sqlite:///cinemagoer.db

   All examples on this page assume that this database is already populated.
   SQLite is used here for simplicity. Other database engines require the
   ``sqlalchemy`` extra and a suitable DBAPI driver.

.. code-block:: python

   >>> import imdb
   >>> ia = imdb.Cinemagoer('s3', uri='sqlite:///cinemagoer.db')

This uses the S3 dataset access system. See :ref:`s3` for dataset import and
database setup.

Searching
---------

You can use the :meth:`search_movie <imdb.IMDbBase.search_movie>` method
of the access object to search for movies with a given (or similar) title.
For example, search with the complete title and year when they are known:

.. code-block:: python

   >>> movies = ia.search_movie('Miss Jerry (1894)')
   >>> movies[0]
   <Movie id:0000009[s3] title:_Miss Jerry (1894)_>

Similarly, you can search for people using
the :meth:`search_person <imdb.IMDbBase.search_person>` method:

.. code-block:: python

   >>> people = ia.search_person('Fred Astaire')
   >>> people[0]
   <Person id:0000001[s3] name:_Fred Astaire_>

As the examples indicate, the results are lists of
:class:`Movie <imdb.Movie.Movie>` and :class:`Person <imdb.Person.Person>`
objects. These behave like
dictionaries, i.e. they can be queried by giving the key of the data
you want to obtain:

.. code-block:: python

   >>> movies[0]['title']
   'Miss Jerry'
   >>> people[0]['name']
   'Fred Astaire'

Movie and person objects have ID attributes containing the canonical numeric
part of the IMDb ID: a string padded to at least seven digits, without the
``tt`` or ``nm`` prefix. This representation is the same for search results,
retrieved objects, and nested objects:

.. code-block:: python

   >>> movies[0].movieID
   '0000009'
   >>> people[0].personID
   '0000001'



Retrieving
----------

If you know the IMDb id of a movie, you can use
the :meth:`get_movie <imdb.IMDbBase.get_movie>` method to retrieve its data.
Retrieval accepts an integer, a digit string with or without zero padding, or
the matching ``tt``/``nm`` prefix. For example:

.. code-block:: python

   >>> movie = ia.get_movie('tt0000009')
   >>> movie
   <Movie id:0000009[s3] title:_Miss Jerry (1894)_>

Similarly, the :meth:`get_person <imdb.IMDbBase.get_person>` method can be
used for retrieving :class:`Person <imdb.Person.Person>` data:

.. code-block:: python

   >>> person = ia.get_person('nm0000001')
   >>> person['name']
   'Fred Astaire'
   >>> person['birth date']
   1899

The downloadable name dataset contains a birth year, not a complete date, so
``birth date`` is an integer year when it is present.


Exceptions
----------

Any error related to Cinemagoer can be caught by checking for
the :class:`imdb.IMDbError` exception:

.. code-block:: python

   from imdb import Cinemagoer, IMDbError

   try:
      ia = Cinemagoer('s3', uri='sqlite:///cinemagoer.db')
      people = ia.search_person('Mel Gibson')
   except IMDbError as e:
       print(e)


See also
--------

For more details about available methods and objects, see
:doc:`query`, :doc:`data-interface`, :doc:`role`, and :doc:`series`.
