Command-line interface
======================

The installed :command:`cinemagoer` command searches and retrieves movies and
people from a populated dataset database. Select the database with ``--uri``,
the ``CINEMAGOER_S3_URI`` environment variable, or the normal Cinemagoer
configuration file::

  cinemagoer --uri sqlite:///cinemagoer.db search movie "Miss Jerry" -n 5
  cinemagoer --uri sqlite:///cinemagoer.db search person "Fred Astaire" --first
  cinemagoer --uri sqlite:///cinemagoer.db get movie tt0000009
  cinemagoer --uri sqlite:///cinemagoer.db get person nm0000001

The repository also provides :file:`bin/cinemagoer-cli`, a thin executable
wrapper around the same implementation. It is useful when working from a
source checkout and is installed as :command:`cinemagoer-cli` for distributors
that use the declared script files. The :command:`cinemagoer` console entry
point remains the preferred installed command::

  uv run ./bin/cinemagoer-cli --uri sqlite:///cinemagoer.db get movie tt0000009

Help is available without a configured database. Use ``help``, ``--help``, or
``-h`` for an overview, database setup guidance, and examples. For details of a
command, use ``help COMMAND``, ``COMMAND help``, or put ``--help`` (or ``-h``)
after its name::

  cinemagoer --help
  cinemagoer help search
  cinemagoer search -h
  cinemagoer help get
  cinemagoer search help
  cinemagoer get help

The same help forms work with :command:`cinemagoer-cli`. Help exits with status
``0``; an unknown help topic exits with status ``2``. Global options such as
``--uri`` and ``--debug`` go before the command.

``-n`` must be a positive integer. Movie and person IDs can be supplied as
digits or with their usual ``tt`` and ``nm`` prefixes.

When an item is displayed on its own, either through ``search ... --first`` or
``get``, the command appends the IMDb id and the IMDb web page URL after the
item summary, so the selected record can be identified without guessing::

  $ cinemagoer --uri sqlite:///cinemagoer.db get movie tt0000009
  Movie
  =====
  Title: Miss Jerry (1894)
  ...
  IMDb ID: tt0000009
  IMDb page: https://www.imdb.com/title/tt0000009/

The plain ``search`` listing already shows the IMDb id for every result.

Exit status
-----------

The command uses these exit statuses:

* ``0`` when the search or retrieval succeeds;
* ``1`` when a search has no results, an ID is not present, or Cinemagoer
  reports an expected database/runtime error; and
* ``2`` when command-line arguments are invalid.

Expected failures print one concise message to standard error. Add the global
``--debug`` option before the command to retain the exception traceback while
diagnosing a failure::

  cinemagoer --debug --uri sqlite:///cinemagoer.db get movie tt0000009
