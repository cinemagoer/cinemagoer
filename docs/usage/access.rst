.. _access:

Access systems
==============

Cinemagoer uses a single access system based on IMDb downloadable datasets.
Before querying data, download IMDb non-commercial datasets and import them
with :file:`s32cinemagoer.py` into a local database (for example,
``sqlite:///cinemagoer.db``).

The database can be SQLite or any other engine supported by SQLAlchemy.

+------------------+-------------+----------------------+
| access system    | aliases     | data source          |
+==================+=============+======================+
| (default) 's3'   | 's3dataset' | downloadable dataset |
|                  |             |                      |
|                  | 'imdbws'    |                      |
|                  |             |                      |
|                  | 'dataset'   |                      |
|                  |             |                      |
|                  | 'datasets'  |                      |
+------------------+-------------+----------------------+

.. note::

   The :file:`cinemagoer.cfg` configuration file lets you set a system-wide,
   per-user, or current-directory default. The legacy :file:`imdbpy.cfg` name
   is also recognized, but :file:`cinemagoer.cfg` takes precedence at each
   searched location. See the commented sample configuration for the complete
   discovery order and available options.

   If no configuration file is found (or no file can be read and parsed),
   ``s3`` is used by default. Exceptions are re-raised by default; set
   ``reraiseExceptions = off`` to retain errors only in the log. Configuration
   comments start with ``#`` or ``;``.

See :ref:`s3` for setup and usage details.
