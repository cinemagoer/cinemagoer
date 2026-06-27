Data interface
==============

The Cinemagoer objects that represent movies and people provide
a dictionary-like interface where the key identifies the information
you want to get out of the object.

At this point, I have really bad news: what the keys are is a little unclear!

In general, keys follow the naming used by Cinemagoer data structures.
If the information is grouped into subsections,
such as cast members and certifications, the subsection label is used
as the key.

The key is almost always lowercase; underscores and dashes are replaced
with spaces. Some keys are computed by Cinemagoer and are not direct fields
from the datasets.


Information sets
----------------

Cinemagoer retrieves data grouped in "information sets". In the current
S3-only backend, the guaranteed infoset is ``main`` for both movies and
people.

The :meth:`get_movie <imdb.IMDbBase.get_movie>` and
:meth:`get_person <imdb.IMDbBase.get_person>` methods accept an optional
``info`` parameter. Each requested group of data is an "information set".

Available information sets can be queried using the access object:

.. code-block:: python

   >>> from imdb import Cinemagoer
   >>> ia = Cinemagoer('s3', uri='sqlite:///cinemagoer.db')
   >>> ia.get_movie_infoset()
   ['main', 'plot']
   >>> ia.get_person_infoset()
   ['main', 'biography', 'filmography']

In the S3 backend, ``plot`` for movies and ``biography``/``filmography`` for
people are compatibility aliases of ``main``.

By default, only ``main`` is requested:

- for a movie: ``main``
- for a person: ``main``

These defaults can be retrieved from the ``default_info`` attributes
of the classes:

.. code-block:: python

   >>> from imdb.Person import Person
   >>> Person.default_info
   ('main',)

Each instance also has a ``current_info`` attribute for tracking
the information sets that have already been retrieved:

.. code-block:: python

   >>> movie = ia.get_movie('0133093')
   >>> movie.current_info
   ['main']

The list of retrieved information sets and the keys they provide can be
taken from the ``infoset2keys`` attribute:

.. code-block:: python

   >>> movie = ia.get_movie('0133093')
   >>> sorted(movie.infoset2keys)
   ['main']
   >>> movie.get('title')
   'The Matrix'

Search operations retrieve a fixed set of data and don't have the concept
of information sets. Therefore objects listed in searches will have even less
information than the defaults. For example, if you do a movie search operation,
the movie objects in the result won't have many of the keys that would be
available on a movie get operation:

.. code-block:: python

   >>> movies = ia.search_movie('matrix')
   >>> movie = movies[0]
   >>> movie
   <Movie id:0133093[s3] title:_The Matrix (1999)_>
   >>> movie.current_info
   []
   >>> 'genres' in movie
   False

Once an object is retrieved (through a get or a search), its data can be
updated using :meth:`update <imdb.IMDbBase.update>`. In the S3 backend,
this is mainly useful for expanding search results from basic fields to
the ``main`` infoset:

.. code-block:: python

   >>> 'cast' in movie
   False
   >>> ia.update(movie)
   >>> movie.current_info
   ['main']
   >>> 'cast' in movie
   True

Only data present in IMDb non-commercial datasets is available through
the S3 access system. Legacy infosets like trivia, quotes, goofs,
full credits, vote details, and publicity are not available.


Composite data
--------------

In some data, the (not-so) universal ``::`` separator is used to delimit
parts of the data inside a string, like the plot of a movie and its author:

.. code-block:: python

   >>> movie = ia.get_movie('0094226')
   >>> plot = movie['plot'][0]
   >>> plot
   "1920's prohibition ... way to get him.::Jeremy Perkins <jwp@aber.ac.uk>"

As a rule, there's at most one such separator inside a string. Splitting
the string will result in two logical pieces as in ``TEXT::NOTE``.
The :func:`imdb.helpers.makeTextNotes` function can be used to create a custom
function to pretty-print this kind of information.


References
----------

Sometimes the collected data contains strings with references to other movies
or persons, e.g. in the plot of a movie or the biography of a person.
These references are stored in the Movie, Person, and Character instances;
in the strings you will find values like _A Movie (2003)_ (qv)
or 'A Person' (qv) or '#A Character# (qv)'. When these strings are accessed
(like movie['plot'] or person['biography']), they will be modified using
a provided function, which must take the string and two dictionaries
containing titles and names references as parameters.

By default the (qv) strings are converted in the "normal" format
("A Movie (2003)", "A Person" and "A Character").

You can find some examples of these functions in the
imdb.utils module.

The function used to modify the strings can be set with the ``defaultModFunct``
parameter of the IMDb class or with the ``modFunct`` parameter
of the ``get_movie`` and ``get_person`` methods:

.. code-block:: python

   import imdb
   i = imdb.Cinemagoer(
       accessSystem='s3',
       uri='sqlite:///cinemagoer.db',
       defaultModFunct=imdb.utils.modHtmlLinks
   )

or:

.. code-block:: python

   import imdb
   i = imdb.Cinemagoer(accessSystem='s3', uri='sqlite:///cinemagoer.db')
   i.get_person('0000154', modFunct=imdb.utils.modHtmlLinks)
