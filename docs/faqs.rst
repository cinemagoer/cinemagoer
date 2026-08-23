FAQs
====

:Q: Is Cinemagoer compatible with Python 3?

:A: Yes. The current release requires Python 3.10 or newer. The unmaintained
    ``imdbpy-legacy`` branch is available only for historical Python releases.


:Q: Importing the data using the 's3' method, are the imdbID available?

:A: Yes! The data from https://datasets.imdbws.com/ contains the original IDs.


:Q: I have an URL (of a movie, person or something else), how can I
    get a Movie/Person/... instance?

:A: Import the ``imdb.helpers`` module and use ``get_byURL``. Pass the same
    dataset database arguments you would pass to ``Cinemagoer``; only movie
    (``tt``) and person (``nm``) URLs are supported by the S3 backend.


:Q: I'm writing an interface based on Cinemagoer and I have problems handling
    encoding, chars conversions, replacements of references and so on.

:A: See the many functions in the imdb.helpers module.


:Q: How can I resize an image URL I already have?

:A: You can use ``imdb.helpers.resizeImage`` for a compatible caller-provided
    URL. IMDb's downloadable datasets do not contain movie-cover or person-
    headshot URLs, so objects retrieved by the S3 backend cannot supply the
    input URL.
