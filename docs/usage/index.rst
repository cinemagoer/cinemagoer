Usage
=====

Here you can find information about how to use IMDbPY to write your own scripts
or programs.

.. warning::

   This document is far from complete: the code is the final documentation! ;-)


To use the IMDbPY package, you have to import :mod:`imdb` and call
the :mod:`imdb.IMDb` function:

.. code-block:: python

   >>> import imdb
   >>> imdb_access = imdb.IMDb()


IMDbPY supports different ways of accessing the IMDb data:

- Fetching data directly from the web server.

- Getting the data from a SQL database that can be created from
  the downloadable data sets provided by the IMDb.

+------------------+-------------+----------------------+
| access system    | aliases     | data source          |
+==================+=============+======================+
| (default) 'http' | 'web'       | imdb.com web server  |
|                  |             |                      |
|                  | 'html'      |                      |
+------------------+-------------+----------------------+
|            's3'  | 's3dataset' | downloadable dataset |
|                  |             |                      |
|                  |             | after Dec 2017       |
+------------------+-------------+----------------------+
|            'sql' | 'db'        | downloadable dataset |
|                  |             |                      |
|                  | 'database'  | before Dec 2017      |
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

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   query
   movie
   person
   character
   company
   role
   infosets
   series
   adult
   info2xml
   l10n
   s3
   ptdf


Other sources of information
----------------------------

Once the IMDbPY package is installed, you can read the docstrings for packages,
modules, functions, classes, objects, methods using the pydoc program;
e.g.: "pydoc imdb.IMDb" will show the documentation about the imdb.IMDb class.

The code contains a lot of comments, try reading it, if you can understand
my English!
