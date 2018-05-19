The S3 dataset
==============

Since the end of 2017, IMDb stopped updating the old plain text data files,
and started distributing a data set that is much easier to parse
(even if it contains much less information).

To use the new data set with IMDbPY you have to:

#. Create a database (let's call it "imdb"), using a database server supported
   by SQLAlchemy. Please use a collation like "utf8_unicode_ci".

#. Install the system libraries needed to access that database
   (they are NOT included in SQLAlchemy), like psycopg2 for PostgreSQL
   or pymysql for MySQL.

#. Download the files on https://datasets.imdbws.com/ and put all of them
   in the same directory.

#. Import the data using the ``bin/s32imdbpy.py`` script. For example::

     ./bin/s32imdbpy.py ~/Download/imdb-s3-dataset-2018-02-07/ \
            postgres://user:password@localhost/imdb

Once the import is finished (on a modern system it should take about an hour
or less), you will have a SQL database with all the information.
Running the script again will drop the current tables and import the data again.

After this point, you can just use the same old API of IMDbPY:

.. code-block:: python

    from imdb import IMDb
    ia = IMDb('s3', 'postgres://user:password@localhost/imdb')

    results = ia.search_movie('the matrix')
    for result in results:
        print(result.movieID, result)

    tm = results[0]
    ia.update(tm)
    print(sorted(tm.keys()))
