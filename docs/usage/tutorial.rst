Tutorial
========

The first thing to do is to import :mod:`imdb` and call the :mod:`imdb.IMDb`
function to get an access object through which IMDb data can be retrieved:

.. code-block:: python

   >>> import imdb
   >>> ia = imdb.IMDb()

By default this will fetch the data from the IMDb web server but there are
other options. See the :ref:`access` document for more information.

On the access object, you can use the
:meth:`search_movie <imdb.IMDbBase.search_movie>` method to search for movies
with a given (or similar) title. For example, to search for movies
with titles like "matrix":

.. code-block:: python

   >>> movies = ia.search_movie('matrix')
   >>> movies[0]
   <Movie id:0133093[http] title:_The Matrix (1999)_>

As the example indicates, the result is a list of :class:`Movie <imdb.Movie>`
objects. These behave like dictionaries, i.e. they can be queried by giving
the key of the data you want to obtain:

.. code-block:: python

   >>> matrix = movies[0]
   >>> matrix['title']
   'The Matrix'
   >>> matrix['year']
   1999

Movies have a ``movieID`` attribute which -when fetched through the IMDb
web server- stores the IMDb id of the movie. For the movie "The Matrix"
in the example above, this value is "0133093":

.. code-block:: python

   >>> matrix.movieID
   '0133093'

If you know the IMDb id of a movie, you can use the
:meth:`get_movie <imdb.IMDbBase.get_movie>` method to retrieve its data.
For example, the movie "The Untouchables" by Brian De Palma has the id
"0094226":

.. code-block:: python

   >>> untouchables = ia.get_movie('0094226')
   >>> untouchables['year']
   1987

Similarly, the :meth:`search_person <imdb.IMDbBase.search_person>` and
:meth:`get_person <imdb.IMDbBase.get_person>` methods can be used for searching
and retrieving :class:`Person <imdb.Person>` data:

.. code-block:: python

   >>> people = ia.search_person('angelina')
   >>> people[0]
   <Person id:0001401[http] name:_Jolie, Angelina_>
   >>> jolie = people[0]
   >>> jolie['name']
   'Angelina Jolie'
   >>> jolie.personID
   '0001401'
   >>> keanu = ia.get_person('0000206')
   >>> keanu['name']
   'Keanu Reeves'
   >>> keanu['birth date']
   '1964-9-2'

And :meth:`search_company <imdb.IMDbBase.search_company>` and
:meth:`get_company <imdb.IMDbBase.get_company>` methods for searching
and retrieving :class:`Company <imdb.Company>` data:

.. code-block:: python

   >>> companies = ia.search_company('rko')
   >>> companies[0]
   <Company id:0226417[http] name:_RKO_>
   >>> rko = companies[0]
   >>> rko['name']
   'RKO'
   >>> rko.companyID
   '0226417'
   >>> pixar = ia.get_company('0017902')
   >>> pixar['name']
   'Pixar Animation Studios'

Search for keywords similar to the one provided, and fetch movies matching
a given keyword:

.. code-block:: python

    keywords = ia.search_keyword(keyword)
    movies = ia.get_keyword(keyword)

Get the top 250 and bottom 100 movies:

.. code-block:: python

    ia.get_top250_movies()
    ia.get_bottom100_movies()

Character associated to a person who starred in a movie, and its notes:

.. code-block:: python

    person_in_cast = movie['cast'][0]
    notes = person_in_cast.notes
    character = person_in_cast.currentRole

Check whether a person worked in a given movie or not:

.. code-block:: python

    person in movie
    movie in person


Get 5 movies tagged with a keyword:

.. code-block:: python

   >>> dystopia = ia.get_keyword('dystopia', results=5)
   >>> dystopia
   [<Movie id:1677720[http] title:_Ready Player One (2018)_>,
    <Movie id:2085059[http] title:_Black Mirror (2011–) (None)_>,
    <Movie id:5834204[http] title:_The Handmaid's Tale (2017–) (None)_>,
    <Movie id:1663662[http] title:_Pacific Rim (2013)_>,
    <Movie id:1856101[http] title:_Blade Runner 2049 (2017)_>]

Get top 250 and bottom 100 movies:

.. code-block:: python

   >>> top250 = ia.get_top250_movies()
   >>> top250[0]
   <Movie id:0111161[http] title:_The Shawshank Redemption (1994)_>
   >>> bottom100 = ia.get_bottom100_movies()
   >>> bottom100[0]
   <Movie id:4458206[http] title:_Code Name: K.O.Z. (2015)_>


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   query
   movie
   person
   character
   company
   role
   infosets
   series
   adult
   info2xml
   l10n
   s3
   ptdf
