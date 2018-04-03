Adult movies
============

IMDbPY for (too) sensitive people.

Since version 2.0 (shame on me! I've noticed this only after more than a year
of development!!!) adult movies are included by default in the result
of the ``search_movie()``, ``search_episode()``, and ``search_person()``
methods.

If for some unintelligible reason you don't want classics like
"Debbie Does Dallas" to show up in your list of results, you can disable
this feature by initializing the IMDb class with the ``adultSearch`` argument
set to ``False`` (or any other "falsy" value).

e.g.:

.. code-block:: python

    from imdb import IMDb

    ia = IMDb(accessSystem='http', adultSearch=False)


The behavior of an IMDb class's instance can be modified at runtime,
by calling the ``do_adult_search()`` method.

e.g.:

.. code-block:: python

    from imdb import IMDb

    # By default in horny-mode.
    ia = IMDb(accessSystem='http')

    # Just for this example, be sure to exclude the proxy.
    ia.set_proxy(None)

    results = ia.search_movie('debby does dallas', results=5)
    for movie in results:
        print(movie['long imdb title'], movie.movieID)
    # This will print:
    # Debbie Does Dallas (1978) 0077415
    # Debbie Does Dallas Part II (1981) 0083807
    # Debbie Does Dallas: The Next Generation (1997) (V) 0160174
    # Debbie Does Dallas '99 (1999) (V) 0233539
    # Debbie Does Dallas 3 (1985) 0124352

    # You can now switch to puritan behavior.
    ia.do_adult_search(False)

    results = ia.search_movie('debby does dallas', results=5)
    for movie in results:
       print(movie['long imdb title'], movie.movieID)
    # This will print only:
    # Pauly Does Dallas (1993) (TV) 0208347


The ``do_adult_search()`` method of the http data access system can take
two more arguments: ``cookie_id`` and ``cookie_uu``, so that you can select
*your own* IMDb account; if cookie id is set to None, no cookies are sent.
These parameters can also be set in the ``imdbpy.cfg`` configuration file.
To find the strings you need to use, see your "cookie" or "cookie.txt" files.
Obviously, you'll need to activate the "adult movies" option for your account;
see http://imdb.com/find/preferences?_adult=1


Other data access systems
-------------------------

Since version 2.2 every other data access system (sql) supports
the same behavior of the http data access system (i.e.: you can set
the ``adultSearch`` argument and use the ``do_adult_search`` method).

Note that for the sql data access system, only results from
the ``search_movie()`` and ``search_episode()`` methods are filtered:
there's no easy (and fast) way to tell whether an actor/actress
is a porn-star or not.
