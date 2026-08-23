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

``-n`` must be a positive integer. Movie and person IDs can be supplied as
digits or with their usual ``tt`` and ``nm`` prefixes.

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
