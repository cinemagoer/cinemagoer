Adult movies
============

Since version 6.8 you can use the **search_movie_advanced(title, adult=None, results=None, sort=None, sort_dir=None)** method to search for adult titles

.. code-block:: python

   >>> import imdb
   >>> ia = imdb.Cinemagoer(accessSystem='http')
   >>> movies = ia.search_movie_advanced('debby does dallas', adult=True)

