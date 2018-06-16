.. _ptdf:

Old data files
==============

.. warning::

   Since the end of 2017, IMDb is no longer updating the data files which are
   described in this document. For working with the updated
   -but less comprehensive- downloadable data, check the :ref:`s3` document.

Until the end of 2017, IMDb used to distribute some of its data as downloadable
text files. IMDbPY can import this data into a database and make it
accessible through its API.

For this, you will first need to install `SQLAlchemy`_ and the libraries
that are needed for the database server you want to use. Check out
the `SQLAlchemy dialects`_ documentation for more detail.

Then, follow these steps:

#. Download the files from the following address and put all of them
   in the same directory:
   ftp://ftp.funet.fi/pub/mirrors/ftp.imdb.com/pub/frozendata/

   You can just download the files you need instead of downloading all files.
   The files that are not downloaded will be skipped during import.
   This feature is still quite untested, so please report any bugs.

   .. warning::

      Beware that the :file:`diffs` subdirectory contains
      **a lot** of files you **don't** need, so don't start mirroring
      everything!

#. Create a database. Use a collation like ``utf8_unicode_ci``.

#. Import the data using the :file:`imdbpy2sql.py` script::

     imdbpy2sql.py -d /path/to/the/data_files_dir/ -u URI

   *URI* is the identifier used to access the SQL database. For example::

      imdbpy2sql.py -d ~/Download/imdb-frozendata/ \
          -u postgres://user:password@localhost/imdb

Once the import is finished, you will have a SQL database with all
the information and you can use the normal IMDbPY API:

.. code-block:: python

   from imdb import IMDb

   ia = IMDb('sql', uri='postgres://user:password@localhost/imdb')

   results = ia.search_movie('the matrix')
   for result in results:
       print(result.movieID, result)

   matrix = results[0]
   ia.update(matrix)
   print(matrix.keys())


.. note::

   It should be noted that the :file:`imdbpy2sql.py` script will not create
   any foreign keys, but only indexes. If you need foreign keys, try using
   the version in the "imdbpy-legacy" branch.

   If you need instructions on how to manually build the foreign keys,
   see `this comment by Andrew D Bate`_.


Performance
-----------

The import performance hugely depends on the underlying module used to access
the database. The :file:`imdbpy2sql.py` script has a number of command line
arguments for choosing presets that can improve performance in specific
database servers.

The fastest database appears to be MySQL, with about 200 minutes to complete
on my test system (read below). A lot of memory (RAM or swap space)
is required, in the range of at least 250/500 megabytes (plus more
for the database server). In the end, the database requires between
2.5GB and 5GB of disk space.

As said, the performance varies greatly using one database server or another.
MySQL, for instance, has an ``executemany()`` method of the cursor object
that accepts multiple data insertion with a single SQL statement; other
databases require a call to the ``execute()`` method for every single row
of data, and they will be much slower -2 to 7 times slower than MySQL.

There are generic suggestions that can lead to better performance, such as
turning off your filesystem journaling (so it can be a good idea to remount
an ext3 filesystem as ext2 for example). Another option is using
a ramdisk/tmpfs, if you have enough RAM. Obviously these have effect only at
insert-time; during day-to-day use, you can turn journaling on again.
You can also consider using CSV output as explained below, if your database
server can import CSV files.

I've done some tests, using an AMD Athlon 1800+, 1GB of RAM, over a complete
plain text data files set (as of 11 Apr 2008, with more than 1.200.000 titles
and over 2.200.000 names):

+----------------------+------------------------------------------------------+
|     database         |  time in minutes: total (insert data/create indexes) |
+======================+======================================================+
|  MySQL 5.0 MyISAM    |  205 (160/45)                                        |
+----------------------+------------------------------------------------------+
|  MySQL 5.0 InnoDB    |  _untested_, see NOTES below                         |
+----------------------+------------------------------------------------------+
|  PostgreSQL 8.1      |  560 (530/30)                                        |
+----------------------+------------------------------------------------------+
|  SQLite 3.3          |  ??? (150/???) -very slow building indexes           |
|                      |                                                      |
|                      |  Timed with the "--sqlite-transactions" command      |
|                      |                                                      |
|                      |  line option; otherwise it's _really_ slow:          |
|                      |                                                      |
|                      |  even 35 hours or more                               |
+----------------------+------------------------------------------------------+
|  SQLite 3.7          |  65/13 - with --sqlite-transactions                  |
|                      |  and using an SSD disk                               |
+----------------------+------------------------------------------------------+
|  SQL Server          |  about 3 or 4 hours                                  |
+----------------------+------------------------------------------------------+

If you have different experiences, please tell me!

As expected, the most important things that you can do to improve performance
are:

#. Use an in-memory filesystem or an SSD disk.
#. Use the ``-c /path/to/empty/dir`` argument to use CSV files.
#. Follow the specific notes about your database server.


Notes
-----

[save the output]

The imdbpy2sql.py will print a lot of debug information on standard output;
you can save it in a file, appending (without quotes) "2>&1 | tee output.txt"


[Microsoft Windows paths]

It's much safer, in a Microsoft Windows environment, to use full paths
for the values of the '-c' and '-d' arguments, complete with drive letter.
The best thing is to use _UNIX_ path separator, and to add a leading
separator, e.g.::

  -d C:/path/to/imdb_files/ -c C:/path/to/csv_tmp_files/


[MySQL]

In general, if you get an annoyingly high number of "TOO MANY DATA
... SPLITTING" lines, consider increasing max_allowed_packet
(in the configuration of your MySQL server) to at least 8M or 16M.
Otherwise, inserting the data will be very slow, and some data may
be lost.


[MySQL InnoDB and MyISAM]

InnoDB is abysmal slow for our purposes: my suggestion is to always use
MyISAM tables and -if you really want to use InnoDB- convert the tables
later. The imdbpy2sql.py script provides a simple way to manage these cases,
see ADVANCED FEATURES below.

In my opinion, the cleaner thing to do is to set the server to use
MyISAM tables or -if you can't modify the server-
use the ``--mysql-force-myisam`` command line option of imdbpy2sql.py.
Anyway, if you really need to use InnoDB, in the server-side settings
I recommend to set innodb_file_per_table to "true".

Beware that the conversion will be extremely slow (some hours), but still
faster than using InnoDB from the start. You can use the "--mysql-innodb"
command line option to force the creation of a database with MyISAM tables,
converted at the end into InnoDB.


[Microsoft SQL Server/SQLExpress]

If you get and error about how wrong and against nature the blasphemous act
of inserting an identity key is, you can try to fix it with the new custom
queries support; see ADVANCED FEATURES below.

As a shortcut, you can use the "--ms-sqlserver" command line option
to set all the needed options.


[SQLite speed-up]

For some reason, SQLite is really slow, except when used with transactions;
you can use the "--sqlite-transactions" command line option to obtain
acceptable performance. The same command also turns off "PRAGMA synchronous".

SQLite seems to hugely benefit from the use of a non-journaling filesystem
and/or of a ramdisk/tmpfs: see the generic suggestions discussed above
in the Timing section.


[SQLite failure]

It seems that with older versions of the python-sqlite package, the first run
may fail; if you get a DatabaseError exception saying "no such table",
try running again the command with the same arguments. Double funny, huh? ;-)


[data truncated]

If you get an insane amount (hundreds or thousands, on various text columns)
of warnings like these:

  imdbpy2sql.py:727: Warning: Data truncated for column 'person_role' at row 4979
  CURS.executemany(self.sqlString, self.converter(self.values()))

you probably have a problem with the configuration of your database.
The error comes from strings that get cut at the first non-ASCII character
(and so you're losing a lot of information).

To solves this problem, you must be sure that your database server is set up
properly, with the use library/client configured to communicate with the server
in a consistent way. For example, for MySQL you can set::

  character-set-server   = utf8
  default-collation      = utf8_unicode_ci
  default-character-set  = utf8

or even::

  character-set-server   = latin1
  default-collation      = latin1_bin
  default-character-set  = latin1


[adult titles]

Beware that, while running, the imdbpy2sql.py script will output
a lot of strings containing both person names and movie titles. The script
has absolutely no way of knowing that the processed title is an adult-only
movie, so... if you leave it on and your little daughter runs to you
screaming "daddy! daddy! what kind of animals does Rocco train in the
documentary 'Rocco: Animal Trainer 17'???"... well, it's not my fault! ;-)


Advanced features
-----------------

With the -e (or --execute) command line argument you can specify
custom queries to be executed at certain times, with the syntax::

  -e "TIME:[OPTIONAL_MODIFIER:]QUERY"

where TIME is one of: 'BEGIN', 'BEFORE_DROP', 'BEFORE_CREATE',
'AFTER_CREATE', 'BEFORE_MOVIES', 'BEFORE_CAST', 'BEFORE_RESTORE',
'BEFORE_INDEXES', 'END'.

The only available OPTIONAL_MODIFIER is 'FOR_EVERY_TABLE' and it means
that the QUERY command will be executed for every table in the database
(so it doesn't make much sense to use it with BEGIN, BEFORE_DROP
or BEFORE_CREATE time...), replacing the "%(table)s" text in the QUERY
with the appropriate table name.

Other available TIMEs are: 'BEFORE_MOVIES_TODB', 'AFTER_MOVIES_TODB',
'BEFORE_PERSONS_TODB', 'AFTER_PERSONS_TODB', 'BEFORE_CHARACTERS_TODB',
'AFTER_CHARACTERS_TODB', 'BEFORE_SQLDATA_TODB', 'AFTER_SQLDATA_TODB',
'BEFORE_AKAMOVIES_TODB' and 'AFTER_AKAMOVIES_TODB'; they take no modifiers.
Special TIMEs 'BEFORE_EVERY_TODB' and 'AFTER_EVERY_TODB' apply to
every BEFORE_* and AFTER_* TIME above mentioned.

These commands are executed before and after every _toDB() call in
their respective objects (CACHE_MID, CACHE_PID and SQLData instances);
the  "%(table)s" text in the QUERY is replaced as above.

You can specify so many -e arguments as you need, even if they refer
to the same TIME: they will be executed from the first to the last.
Also, always remember to correctly escape queries: after all you're
passing it on the command line!

E.g. (ok, quite a silly example...)::

  -e "AFTER_CREATE:SELECT * FROM title;"

The most useful case is when you want to convert the tables of a MySQL
from MyISAM to InnoDB::

  -e "END:FOR_EVERY_TABLE:ALTER TABLE %(table)s ENGINE=InnoDB;"

If your system uses InnoDB by default, you can trick it with::

  -e "AFTER_CREATE:FOR_EVERY_TABLE:ALTER TABLE %(table)s ENGINE=MyISAM;" -e "END:FOR_EVERY_TABLE:ALTER TABLE %(table)s ENGINE=InnoDB;"

You can use the "--mysql-innodb" command line option as a shortcut
of the above command.

Cool, huh?

Another possible use is to fix a problem with Microsoft SQLServer/SQLExpress.
To prevent errors setting IDENTITY fields, you can run something like this::

  -e 'BEFORE_EVERY_TODB:SET IDENTITY_INSERT %(table)s ON' -e 'AFTER_EVERY_TODB:SET IDENTITY_INSERT %(table)s OFF'

You can use the "--ms-sqlserver" command line option as a shortcut
of the above command.

To use transactions to speed-up SQLite, try::

  -e 'BEFORE_EVERY_TODB:BEGIN TRANSACTION;' -e 'AFTER_EVERY_TODB:COMMIT;'

Which is also the same thing the command line option "--sqlite-transactions"
does.


CSV files
---------

.. note::

   Keep in mind that not all database servers support this.

   Moreover, you can run into problems. For example, if you're using
   PostgreSQL, your server process will need read access to the directory
   where the CSV files are stored.

To create the database using a set of CSV files, run :file:`imdbpy2sql.py`
as follows::

   imdbpy2sql.py -d /dir/with/plainTextDataFiles/ -u URI \
         -c /path/to/the/csv_files_dir/

The created CSV files will be imported near the end of processing. After the import
is finished, you can safely remove these files.

Since version 4.5, it's possible to separate the two steps involved
when using CSV files:

- With the ``--csv-only-write`` command line option, the old database will be
  truncated and the CSV files saved, along with imdbID information.

- With the ``--csv-only-load`` option, these saved files can be loaded
  into an existing database (this database MUST be the one left almost empty
  by the previous run).

Beware that right now the whole procedure is not very well tested.
For both commands, you still have to specify the whole
``-u URI -d /path/plainTextDataFiles/ -c /path/CSVfiles/`` arguments.


.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _SQLAlchemy dialects: http://docs.sqlalchemy.org/en/latest/dialects/
.. _this comment by Andrew D Bate: https://github.com/alberanid/imdbpy/issues/130#issuecomment-365707620
