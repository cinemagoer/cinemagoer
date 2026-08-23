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

For example, a person's ``name`` is kept in the form supplied by the IMDb
dataset. The ``first name`` and ``last name`` keys provide a best-effort split
for applications that need separate values:

.. code-block:: python

   >>> person['name']
   'Frederick Austerlitz Jr.'
   >>> person['first name']
   'Frederick'
   >>> person['last name']
   'Austerlitz'

Name conventions vary between cultures, so these computed components can be
ambiguous. The original ``name`` value should be preferred when an exact
representation is required.


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
   ['main', 'plot', 'episodes']
   >>> ia.get_person_infoset()
   ['main', 'biography', 'filmography']

In the S3 backend, ``plot`` for movies and ``biography``/``filmography`` for
people are compatibility aliases of ``main``. They do not add plots,
biographies, or filmographies because those fields are not present in the
downloadable datasets. The ``episodes`` movie infoset expands series episodes.

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
   ['main', 'plot']

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


Legacy text helpers
-------------------

The public containers retain compatibility support for ``TEXT::NOTE`` strings
and ``(qv)`` title/name references. The
:func:`imdb.helpers.makeTextNotes` helper can format caller-provided composite
strings, and ``defaultModFunct``/``modFunct`` can transform references stored
in manually constructed or deserialized objects.

The current S3 backend does not populate the legacy plot, biography, or
reference-map fields used by older examples. Consequently these helpers do
not transform ordinary objects retrieved from the downloadable datasets.
