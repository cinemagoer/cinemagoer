.. _access:

Access systems
==============

IMDbPY supports different ways of accessing the IMDb data:

- Fetching data directly from the web server.

- Getting the data from a SQL database that can be created from
  the downloadable data sets provided by the IMDb.

+------------------+-------------+----------------------+
| access system    | aliases     | data source          |
+==================+=============+======================+
| (default) 'http' | 'https'     | imdb.com web server  |
|                  |             |                      |
|                  | 'web'       |                      |
|                  |             |                      |
|                  | 'html'      |                      |
+------------------+-------------+----------------------+
|            's3'  | 's3dataset' | downloadable dataset |
|                  |             |                      |
|                  |             | *after Dec 2017*     |
+------------------+-------------+----------------------+
|            'sql' | 'db'        | downloadable dataset |
|                  |             |                      |
|                  | 'database'  | *until Dec 2017*     |
+------------------+-------------+----------------------+

.. note::

   Since release 3.4, the :file:`imdbpy.cfg` configuration file is available,
   so that you can set a system-wide (or per-user) default. The file is
   commented with indication of the location where it can be put,
   and how to modify it.

   If no :file:`imdbpy.cfg` file is found (or is not readable or
   it can't be parsed), 'http' will be used the default.

See the :ref:`s3` and :ref:`ptdf` documents for more information about
SQL based access systems.
