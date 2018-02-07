# The S3 dataset

Since the end of 2017, IMDb stopped updating the old plain text data files,
and started distributing a much easier to parse dataset (even if it contains
much less information).

To use the new dataset with IMDbPY you have to:

1. create a database (let's call it "imdb"), using a database server supported by SQLAlchemy.
Please use a collation like utf8_unicode_ci.

2. install on your system the libraries needed to access that database (they
are NOT included in SQLAlchemy), like psycopg2 for PostgreSQL or pymysql
for MySQL.

3. download the files https://datasets.imdbws.com/ and put all of them in the same directory

4. import the data using the bin/s32imdbpy.py script; for example:
   ./bin/s32imdbpy.py ~/Download/imdb-s3-dataset-2018-02-07/ postgres://user:password@localhost/imdb

Once the import is done (on a modern system it should take about an hour or less) you'll have
a SQL database with all the information.
Running again the script with drop the current tables and import the data again.

At this point, you can just use the same old API of IMDbPY:

    from imdb import IMDb
    ia = IMDb('s3', 'postgres://user:password@localhost/imdb')

    results = ia.search_movie('the matrix')
    for result in results:
        print(result.movieID, result)

    tm = results[0]
    ia.update(tm)
    print(sorted(tm.keys()))
