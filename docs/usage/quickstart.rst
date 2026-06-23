Quick start
===========

The first thing to do is to import :mod:`imdb` and call the :mod:`imdb.IMDb`
function to get an access object through which IMDb data can be retrieved:

.. code-block:: python

   >>> import imdb
   >>> ia = imdb.Cinemagoer('s3', uri='sqlite:///cinemagoer.db')

This uses the S3 dataset access system. See :ref:`s3` for dataset import and
database setup.

Searching
---------

You can use the :meth:`search_movie <imdb.IMDbBase.search_movie>` method
of the access object to search for movies with a given (or similar) title.
For example, to search for movies with titles like "matrix":

.. code-block:: python

   >>> movies = ia.search_movie('matrix')
   >>> movies[0]
   <Movie id:0133093[s3] title:_The Matrix (1999)_>

Similarly, you can search for people using
the :meth:`search_person <imdb.IMDbBase.search_person>` method:

.. code-block:: python

   >>> people = ia.search_person('angelina')
   >>> people[0]
   <Person id:0001401[s3] name:_Jolie, Angelina_>

As the examples indicate, the results are lists of
:class:`Movie <imdb.Movie.Movie>` and :class:`Person <imdb.Person.Person>`
objects. These behave like
dictionaries, i.e. they can be queried by giving the key of the data
you want to obtain:

.. code-block:: python

   >>> movies[0]['title']
   'The Matrix'
   >>> people[0]['name']
   'Angelina Jolie'

Movie and person objects have id attributes that store the IMDb id of
the object:

.. code-block:: python

   >>> movies[0].movieID
   '0133093'
   >>> people[0].personID
   '0001401'



Retrieving
----------

If you know the IMDb id of a movie, you can use
the :meth:`get_movie <imdb.IMDbBase.get_movie>` method to retrieve its data.
For example, the movie "The Untouchables" by Brian De Palma has the id
"0094226":

.. code-block:: python

   >>> movie = ia.get_movie('0094226')
   >>> movie
   <Movie id:0094226[s3] title:_The Untouchables (1987)_>

Similarly, the :meth:`get_person <imdb.IMDbBase.get_person>` method can be
used for retrieving :class:`Person <imdb.Person.Person>` data:

.. code-block:: python

   >>> person = ia.get_person('0000206')
   >>> person['name']
   'Keanu Reeves'
   >>> person['birth date']
   '1964-9-2'


Exceptions
----------

Any error related to Cinemagoer can be caught by checking for
the :class:`imdb.IMDbError` exception:

.. code-block:: python

   from imdb import Cinemagoer, IMDbError

   try:
       ia = Cinemagoer()
       people = ia.search_person('Mel Gibson')
   except IMDbError as e:
       print(e)
