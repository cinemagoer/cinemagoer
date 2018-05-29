Data interface
==============

The IMDbPY objects that represent movies, people and companies provide
a dictionary-like interface where the key identifies the information
you want to get out of the object.

At this point, I have really bad news: what the keys are is a little unclear!

In general, the key is the label of the section as used by the IMDb web server
to present the data. If the information is grouped into subsections,
such as cast members, certifications, distributor companies, etc.,
the subsection label in the HTML page is used as the key.

The key is almost always lowercase; underscores and dashes are replaced
with spaces. Some keys aren't taken from the HTML page, but are defined
within the respective class.


Information sets
----------------

IMDbPY can retrieve almost every piece of information of a movie, person or
company. This can be a problem, because (at least for the "http" data access
system) it means that a lot of web pages must be fetched and parsed.
This can be both time- and bandwidth-consuming, especially if you're interested
in only a small part of the information.

The :meth:`get_movie <imdb.IMDbBase.get_movie>`,
:meth:`get_person <imdb.IMDbBase.get_person>` and
:meth:`get_company <imdb.IMDbBase.get_company>` methods take an optional
``info`` parameter, which can be used to specify the kinds of data to fetch.
Each group of data that gets fetched together is called an "information set".

Different types of objects have their own available information sets.
For example, the movie objects have a set called "vote details" for
the number of votes and their demographic breakdowns, whereas person objects
have a set called "other works" for miscellaneous works of the person.
Available information sets for each object type can be queried
using the access object:

.. code-block:: python

   >>> from imdb import IMDb
   >>> ia = IMDb()
   >>> ia.get_movie_infoset()
   ['airing', 'akas', ..., 'video clips', 'vote details']
   >>> ia.get_person_infoset()
   ['awards', 'biography', ..., 'other works', 'publicity']
   >>> ia.get_company_infoset()
   ['main']

For each object type, only the important information will be retrieved
by default:

- for a movie: "main", "plot"
- for a person: "main", "filmography", "biography"
- for a company: "main"

These defaults can be retrieved from the ``default_info`` attributes
of the classes:

.. code-block:: python

   >>> from imdb.Person import Person
   >>> Person.default_info
   ('main', 'filmography', 'biography')

Each instance also has a ``current_info`` attribute for tracking
the information sets that have already been retrieved:

.. code-block:: python

   >>> movie = ia.get_movie('0133093')
   >>> movie.current_info
   ['main', 'plot', 'synopsis']

The list of retrieved information sets and the keys they provide can be
taken from the ``infoset2keys`` attribute:

.. code-block:: python

   >>> movie = ia.get_movie('0133093')
   >>> movie.infoset2keys
   {'main': ['cast', 'genres', ..., 'top 250 rank'], 'plot': ['plot', 'synopsis']}
   >>> movie = ia.get_movie('0094226', info=['taglines', 'plot'])
   >>> movie.infoset2keys
   {'taglines': ['taglines'], 'plot': ['plot', 'synopsis']}
   >>> movie.get('title')
   >>> movie.get('taglines')[0]
   'The Chicago Dream is that big'

Search operations retrieve a fixed set of data and don't have the concept
of information sets. Therefore objects listed in searches will have even less
information than the defaults. For example, if you do a movie search operation,
the movie objects in the result won't have many of the keys that would be
available on a movie get operation:

.. code-block:: python

   >>> movies = ia.search_movie('matrix')
   >>> movie = movies[0]
   >>> movie
   <Movie id:0133093[http] title:_The Matrix (1999)_>
   >>> movie.current_info
   []
   >>> 'genres' in movie
   False

Once an object is retrieved (through a get or a search), its data can be
updated using the :meth:`update <imdb.IMDbBase.update>` method with the desired
information sets. Continuing from the example above:

.. code-block:: python

   >>> 'median' in movie
   False
   >>> ia.update(movie, info=['taglines', 'vote details'])
   >>> movie.current_info
   ['taglines', 'vote details']
   >>> movie['median']
   9
   >>> ia.update(movie, info=['plot'])
   >>> movie.current_info
   ['taglines', 'vote details', 'plot', 'synopsis']

Beware that the information sets vary between access systems:
locally not every piece of data is accessible, whereas -for example for SQL-
accessing one set of data means automatically accessing a number of other
information (without major performance drawbacks).


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
of the ``get_movie``, ``get_person``, and ``get_character`` methods:

.. code-block:: python

   import imdb
   i = imdb.IMDb(defaultModFunct=imdb.utils.modHtmlLinks)

or:

.. code-block:: python

   import imdb
   i = imdb.IMDb()
   i.get_person('0000154', modFunct=imdb.utils.modHtmlLinks)
