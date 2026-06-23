.. _access:

Access systems
==============

Cinemagoer uses a single access system based on IMDb downloadable datasets.

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

   Since release 3.4, the :file:`imdbpy.cfg` configuration file is available,
   so that you can set a system-wide (or per-user) default. The file is
   commented with indication of the location where it can be put,
   and how to modify it.

  If no :file:`imdbpy.cfg` file is found (or is not readable or
  it can't be parsed), 's3' will be used as the default.

See :ref:`s3` for setup and usage details.
