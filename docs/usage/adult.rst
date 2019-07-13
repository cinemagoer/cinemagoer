Adult movies
============

Since July 2019 you can use the **search_movie_advanced(title, adult=None, results=None, sort=None, sort_dir=None)** method to search for adult titles

.. code-block:: python

   >>> ia = IMDb(accessSystem='http')
   >>> movies = ia.search_movie_advanced('debby does dallas', adult=True)

