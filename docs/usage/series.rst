Series
======

As on the IMDb site, each TV series and also each of a TV series' episodes is
treated as a regular title, just like a movie. The ``kind`` key can be used
to distinguish series and episodes from movies:

.. code-block:: python

   >>> series = ia.get_movie('0389564')
   >>> series
   <Movie id:0389564[http] title:_"The 4400" (2004)_>
   >>> series['kind']
   'tv series'
   >>> episode = ia.get_movie('0502803')
   >>> episode
   <Movie id:0502803[http] title:_"The 4400" Pilot (2004)_>
   >>> episode['kind']
   'episode'

The episodes of a series can be fetched using the "episodes" infoset. This
infoset adds an ``episodes`` key which is a dictionary from season numbers
to episodes. And each season is a dictionary from episode numbers within
the season to the episodes. Note that the season and episode numbers don't
start from 0; they are the numbers given by the IMDb:

.. code-block:: python

   >>> ia.update(series, 'episodes')
   >>> sorted(series['episodes'].keys())
   [1, 2, 3, 4]
   >>> season4 = series['episodes'][4]
   >>> len(season4)
   13
   >>> episode = series['episodes'][4][2]
   >>> episode
   <Movie id:1038701[http] title:_"The 4400" Fear Itself (2007)_>
   >>> episode['season']
   4
   >>> episode['episode']
   2

The title of the episode doesn't contain the title of the series:

.. code-block:: python

   >>> episode['title']
   'Fear Itself'
   >>> episode['series title']
   'The 4400'

The episode also contains a key that refers to the series, but beware that,
to avoid circular references, it's not the same object as the series object
we started with:

.. code-block:: python

   >>> episode['episode of']
   <Movie id:0389564[http] title:_"The 4400" (None)_>
   >>> series
   <Movie id:0389564[http] title:_"The 4400" (2004)_>


Titles
------

The ``analyze_title()`` and ``build_title()`` functions now support
TV episodes. You can pass a string to the ``analyze_title`` function
in the format used by the web server (``"The Series" The Episode (2005)``)
or in the format of the plain text data files
(``"The Series" (2004) {The Episode (#ser.epi)}``).

For example, if you call the function::

  analyze_title('"The Series" The Episode (2005)')

the result will be::

  {
      'kind': 'episode',        # kind is set to 'episode'
      'year': '2005',           # release year of this episode
      'title': 'The Episode',   # episode title
      'episode of': {           # 'episode of' will contain
          'kind': 'tv series',  # information about the series
          'title': 'The Series'
      }
  }


The ``episode of`` key can be a dictionary or a ``Movie`` instance
with the same information.

The ``build_title()`` function takes an optional argument: ``ptdf``,
which when set to false (the default) returns the title of the episode
in the format used by the IMDb's web server
("The Series" An Episode (2006)); otherwise, it uses the format used
by the plain text data files (something like
"The Series" (2004) {An Episode (#2.5)})


Full credits
------------

When retrieving credits for a TV series or mini-series, you may notice that
many long lists (like "cast" and "writers") are incomplete. You can fetch
the complete list of cast and crew with the "full credits" data set:

.. code-block:: python

   >>> series = ia.get_movie('0285331')
   >>> series
   <Movie id:0285331[http] title:_"24" (2001)_>
   >>> len(series['cast'])
   50
   >>> ia.update(series, 'full credits')
   >>> len(series['cast'])
   2514

If you prefer, you can retrieve the complete cast of every episode, keeping
the lists separated for each episode. Instead of retrieving with::

  ia.update(series, 'episodes')

use::

  ia.update(series, 'episodes cast')

or the equivalent::

  i.update(m, 'guests')

Now you end up having the same information as if you have updated
the 'episodes' info set, but every Movie object inside the dictionary
of dictionary has the complete cast, e.g.::

  cast = m['episodes'][1][2]['cast']  # cast list for the second episode
                                      # of the first season.

Beware that both 'episodes cast' and 'guests' will update the
keyword 'episodes' (and not 'episodes cast' or 'guests').


Ratings
-------

You can retrieve rating information about every episode in a TV series
or mini series using the 'episodes rating' data set.


People
------

You can retrieve information about single episodes acted/directed/...
by a person.

.. code-block:: python

   from imdb import IMDb
   i = IMDb()
   p = i.get_person('0005041')  # Laura Innes
   p['actress'][0]   # <Movie id:0568152[http] title:_"ER" (????)_>

   # At this point you have an entry (in keys like 'actor', 'actress',
   # 'director', ...) for every series the person starred/worked in, but
   # you knows nothing about singles episodes.
   i.update(p, 'episodes')  # updates information about single episodes.

   p['episodes']    # a dictionary with the format:
                    #    {<TV Series Movie Object>: [
                    #                                <Episode Movie Object>,
                    #                                <Episode Movie Object>,
                    #                                ...
                    #                               ],
                    #     ...
                    #    }

   er = p['actress'][0]  # ER tv series
   p['episodes'][er]     # list of Movie objects; one for every ER episode
                         # she starred/worked in

   p['episodes'][er][0]  # <Movie id:0568154[http] title:_"ER" Welcome Back Carter! (1995)_>
   p['episodes'][er]['kind']   # 'episode'
   p['episodes'][er][0].currentRole   # 'Dr. Kerry Weaver'


Goodies
-------

In the ``imdb.helpers`` module there are some functions useful to manage
lists of episodes:

- ``sortedSeasons(m)`` returns a sorted list of seasons of the given series, e.g.:

  .. code-block:: python

     >>> from imdb import IMDb
     >>> i = IMDb()
     >>> m = i.get_movie('0411008')
     >>> i.update(m, 'episodes')
     >>> sortedSeasons(m)
     [1, 2]

- ``sortedEpisodes(m, season=None)`` returns a sorted list of episodes of the
  the given series for only the specified season(s) (if None, every season),
  e.g.:

  .. code-block:: python

     >>> from imdb import IMDb
     >>> i = IMDb()
     >>> m = i.get_movie('0411008')
     >>> i.update(m, 'episodes')
     >>> sortedEpisodes(m, season=1)
     [<Movie id:0636289[http] title:_"Lost" Pilot: Part 1 (2004)_>, <Movie id:0636290[http] title:_"Lost" Pilot: Part 2 (2004)_>, ...]
