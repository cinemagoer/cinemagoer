Adult movies
============

*IMDbPY for (too) sensitive people.*

Since version 2.0 (shame on me! I've noticed this only after more than a year
of development!!!) adult movies are included by default in search results.

If for some unintelligible reason you don't want classics like
"Debbie Does Dallas" to show up in your searches, you can disable this feature
by initializing the :class:`IMDb <imdb.IMDb>` class with the ``adultSearch``
argument set to ``False``:

.. code-block:: python

   >>> ia = IMDb(accessSystem='http', adultSearch=False)


This behavior can also be modified at runtime by calling the
:meth:`do_adult_search <imdb.IMDb.do_adult_search>` method:

.. code-block:: python

   >>> ia = IMDb(accessSystem='http')   # by default in horny mode
   >>> movies = ia.search_movie('debby does dallas', results=5)
   >>> movieIDs = [m.movieID for m in movies]
   >>> '0077415' in movieIDs            # Debbie Does Dallas (1978)
   True
   >>> ia.do_adult_search(False)        # switch to puritan behavior
   >>> movies = ia.search_movie('debby does dallas', results=5)
   >>> movieIDs = [m.movieID for m in movies]
   >>> '0077415' in movieIDs            # Debbie Does Dallas (1978)
   False


The :meth:`do_adult_search <imdb.parser.http.IMDbHTTPAccessSystem.do_adult_search>`
method of the HTTP data access system can take two more arguments:
``cookie_id`` and ``cookie_uu``, so that you can select *your own*
IMDb account; if cookie id is set to None, no cookies are sent.
These parameters can also be set in the :file:`imdbpy.cfg` configuration file.
To find the strings you need to use, see your "cookie" or "cookie.txt" files.
Obviously, you'll need to activate the "adult movies" option for your account;
see http://imdb.com/find/preferences?_adult=1

Since version 2.2 all data access systems (sql) support
the same behavior (i.e.: you can set the ``adultSearch`` argument and
use the ``do_adult_search`` method).

Note that for the sql data access system, only results from
the ``search_movie()`` and ``search_episode()`` methods are filtered:
there's no easy (and fast) way to tell whether an actor/actress
is a porn star or not.
