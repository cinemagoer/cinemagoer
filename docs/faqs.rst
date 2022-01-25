FAQs
====

:Q: Is Cinemagoer compatible with Python 3?

:A: Yes. Versions after 6.0 are compatible with Python 3.x, but should
    also work with Python 2.7.
    If you need an older, unmaintained, version for Python, see the
    imdbpy-legacy branch in the repository.


:Q: Importing the data using the 's3' method, are the imdbID available?

:A: Yes! The data from https://datasets.imdbws.com/ contains the original IDs.


:Q: Importing the data using the old 'sql' method, are the imdbID available?

:A: No. The old 'sql' method generates sequential imdbIDs that are unrelated to the ones used by the web site.


:Q: I have an URL (of a movie, person or something else), how can I
    get a Movie/Person/... instance?

:A: Import the ``imdb.helpers`` module and use the ``get_byURL`` function.


:Q: I'm writing an interface based on Cinemagoer and I have problems handling
    encoding, chars conversions, replacements of references and so on.

:A: See the many functions in the imdb.helpers module.


:Q: How can I get a link to an image (movie cover or people headshot) with a specific size?

:A: You can use the ``imdb.helpers.resizeImage`` function to get a link to a resized and/or cropped version of the image.
