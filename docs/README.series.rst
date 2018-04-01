Series
======

Summary of this file:

- Managing series episodes
- Titles
- Series
- FULL CREDITS
- RATINGS
- PEOPLE
- GOODIES


Managing series episodes
------------------------

Since January 2006, IMDb changed the way it handles TV episodes:
now every episode is treated as full title. Starting with version 2.5,
IMDbPY also supports this behavior.


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


Series
------

You can retrieve information about seasons and episodes for a TV series
or a mini-series:

.. code-block:: python

   >>> from imdb import IMDb
   >>> i = IMDb()
   >>> m = i.get_movie('0389564')   # The 4400
   >>> m['kind']                    # kind is 'tv series'
   >>> i.update(m, 'episodes')      # retrieves episodes information.
   >>> m['episodes']    # a dictionary with the format:
                        #    {#season_number: {
                        #                      #episode_number: Movie object,
                        #                      #episode_number: Movie object,
                        #                      ...
                        #                     },
                        #     ...
                        #    }
                        # season_number always starts with 1, episode_number
                        # depends on the series' numbering schema: some series
                        # have a 'episode 0', while others starts counting from 1
   >>> m['episodes'][1][1] # <Movie id:0502803[http] title:_"The 4400" Pilot (2004)_>
   >>> e = m['episodes'][1][2]      # second episode of the first season
   >>> e['kind']                    # kind is 'episode'
   >>> e['season'], e['episode']    # return 1, 2
   >>> e['episode of']  # <Movie id:0389564[http] title:_"4400, The" (2004)_>
                        # XXX: beware that e['episode of'] and m _are not_ the
                        #      same object, while both represents the same series.
                        #      This is to avoid circular references; the
                        #      e['episode of'] object only contains basics
                        #      information (title, movieID, year, ....)
   >>> i.update(e)      # retrieve normal information about this episode (cast, ...)

   >>> e['title']                   # 'The New and Improved Carl Morrissey'
   >>> e['series title']            # 'The 4400'
   >>> e['long imdb episode title'] # '"The 4400" The New and Improved Carl Morrissey (2004)'


Summary of keys of the Movie object for a series episode:

- ``kind``: Set to 'episode'.
- ``episode of``: Set to a movie object, this is a reference to the series.
- ``season``: Number of the season (int).
- ``episode``: Number of the episode in the season (int).
- ``long imdb episode title``: Combines series and episode title.
- ``series title``: Title of the series.
- ``canonical series title``: Title of the series, in canonical format.

Summary of keys of the Movie object for a series:

- ``kind``: Set to 'tv series'.
- ``episodes``: Dictionary (seasons) of dictionary (episodes in the season).


Full credits
------------

Retrieving credits for a TV series or mini-series, you may notice that
many long lists (like "cast", "writers", ...) are incomplete.
You can fetch the complete list of cast and crew with the "full credits"
data set; e.g.:

.. code-block:: python

   from imdb import IMDb
   i = IMDb()
   m = i.get_movie('0285331')  # 24.
   print(len(m['cast'])) # wooah!  Only 7 person in the cast of 24?!?!
   i.update(m, 'full credits')
   print(len(m['cast'])) # yup!  More than 300 persons!

If you prefer, you can retrieve the complete cast of every episode,
keeping the lists separated for every episode; instead of retrieving
the list of episodes with::

  i.update(m, 'episodes')

use instead::

  i.update('episodes cast')

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
