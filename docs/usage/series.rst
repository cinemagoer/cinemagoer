Series
======

As on the IMDb site, each TV series and also each of a TV series' episodes is
treated as a regular title, just like a movie. The ``kind`` key can be used
to distinguish series and episodes from movies:

.. code-block:: python

   >>> series = ia.get_movie('0389564')
   >>> series
   <Movie id:0389564[s3] title:_"The 4400" (2004)_>
   >>> series['kind']
   'tv series'
   >>> episode = ia.get_movie('0502803')
   >>> episode
   <Movie id:0502803[s3] title:_"The 4400" Pilot (2004)_>
   >>> episode['kind']
   'episode'

With the current S3 dataset backend, Cinemagoer does not provide the legacy
``episodes`` infoset that expands a whole series into nested season/episode
dictionaries.

If you already know an episode IMDb id, you can retrieve it directly and read
its episode metadata fields from ``title.episode.tsv.gz`` (for example,
``seasonNr`` and ``episodeNr`` when present).

The title of the episode doesn't contain the title of the series:

.. code-block:: python

   >>> episode['title']
   'Fear Itself'
   >>> episode.get('kind')
   'episode'

Depending on imported rows, episode objects can also include a reference to
their parent series.


Titles
------

The ``analyze_title()`` and ``build_title()`` functions now support
TV episodes. You can pass a string to the ``analyze_title`` function
in the format used by Cinemagoer episode titles (``"The Series" The Episode (2005)``)
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
in the default Cinemagoer display format
("The Series" An Episode (2006)); otherwise, it uses the format used
by the plain text data files (something like
"The Series" (2004) {An Episode (#2.5)})


Full-series episode expansion, per-series episode ratings, and person-level
episode breakdown infosets are not available in the S3 dataset backend.
