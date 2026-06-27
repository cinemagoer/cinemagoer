Adult movies
============

Since version 6.8 you can use the **search_movie_advanced(title, adult=None, results=None, sort=None, sort_dir=None)** method to search for adult titles

Before running the example, make sure you have imported IMDb non-commercial
datasets into SQLite with :file:`s32cinemagoer.py`.

.. code-block:: python

   >>> import imdb
   >>> ia = imdb.Cinemagoer(accessSystem='s3', uri='sqlite:///cinemagoer.db')
   >>> movies = ia.search_movie_advanced('debby does dallas', adult=True)

