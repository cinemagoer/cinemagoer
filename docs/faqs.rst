FAQs
====

:Q: Is IMDbPY compatible with Python 3?

:A: Yes. Actually, the versions after 6.0 are compatible only with Python 3.
    If you need an older, unmaintained, version for Python, see the
    imdbpy-legacy branch in the repository.


:Q: Why is the movieID (and other IDs) used in the old "sql" database not
    the same as the ID used on the IMDb.com site?

:A: First, a bit of nomenclature: "movieID" is the term we use for a unique
    identifier used by IMDbPY to manage a single movie (similar terms
    for other kinds of data such as "personID" for persons). An "imdbID"
    is the term we use for a unique identifier that the IMDb.com site uses
    for the same kind of data (e.g.: the 7-digit number in tt0094226,
    as seen in the URL for "The Untouchables").

    When using IMDbPY to access the web ("http" data access system), movieIDs
    and imdbIDs are the same thing -beware that in this case a movieID
    is a string, with the leading zeroes.

    Unfortunately, when populating a SQL database with data from the plain text
    data files, we don't have access to imdbIDs -since they are
    not distributed at all- and so we have to generate them ourselves
    (they are the "id" columns in tables like "title" or "name").
    This means that these values are valid only for your current database:
    if you update it with a newer set of plain text data files, these IDs
    will surely change (and, by the way, they are integers).
    It's also obvious, now, that you can't exchange IDs between the "http"
    and the "sql" data access systems, and similarly you can't use imdbIDs
    with your local database or vice-versa.


:Q: When using a SQL database, what's the "imdb_id" (or something like that)
    column in tables like "title", "name" and so on?

:A: It's internally used by IMDbPY to remember the imdbID of a movie
    (the one used by the web site), once it has been encountered. This way,
    if IMDbPY is asked again about the imdbID of a movie (or person, or ...),
    it won't have to contact the web site again.

    When accessing the database, you'll use the numeric value
    of the "id" column, e.g. "movieID". Note that, to update the SQL database,
    you have to access it using a user who has write permission.

    As a bonus, when possible, the values of the imdbIDs are saved
    between updates of the SQL database (using the imdbpy2sql.py script).
    Beware that it's tricky and not always possible, but the script does
    its best to succeed.


:Q: But what if I really need the imdbIDs, to use in my database?

:A: No, you don't. Search for a title, get its information. Be happy!


:Q: I have a great idea: Write a script to fetch all the imdbIDs
    from the web site!  Can't you do it?

:A: Yeah, I can. But I won't. :-)

    It would be quite easy to map every title on the web to its imdbID,
    but there are still lots of problems. First of all, every user will end up
    doing it for their own copy of the plain text data files (and this will
    make the imdbpy2sql.py script painfully slow and prone to all sort
    of problems). Moreover, the imdbIDs are unique and never reused, true,
    but movie titles _do_ change: to fix typos, to override working titles,
    to cope with a new movie with the same title release in the same year,
    not to mention cancelled or postponed movies.

    Other than that, we'd have to do the same for persons, characters, and
    companies. Believe me: it doesn't make sense. Work on your local database
    using your movieIDs (or even better: don't mind about movieIDs and think
    in terms of searches and Movie instances!) and retrieve the imdbID only
    in the rare circumstances when you really need them (see the next FAQ).
    Repeat after me: I DON'T NEED ALL THE imdbIDs. :-)


:Q: When using a SQL database, how can I convert a movieID (whose value
    is valid only locally) to an imdbID (the ID used by the imdb.com site)?

:A: Various functions can be used to convert a movieID (or personID or
    other IDs) to the imdbID used by the web site. Example:

    .. code-block:: python

       from imdb import IMDb
       ia = IMDb('sql', uri=URI_TO_YOUR_SQL_DATABASE)
       movie = ia.search_movie('The Untouchables')[0] # a Movie instance.
       print('The movieID for The Untouchables:', movie.movieID)
       print('The imdbID used by the site:', ia.get_imdbMovieID(movie.movieID))
       print('Same ID, smarter function:', ia.get_imdbID(movie))

    It goes without saying that ``get_imdbMovieID`` method has some sibling
    methods: ``get_imdbPersonID``, ``get_imdbCompanyID`` and
    ``get_imdbCharacterID``. Also notice that the ``get_imdbID`` method
    is smarter, and takes any kind of instance (the other functions need
    a movieID, personID, ...)

    Another method that will try to retrieve the imdbID is ``get_imdbURL``,
    which works like ``get_imdbID`` but returns a URL.

    In case of problems, these methods will return None.


:Q: I have a movie title (in the format used by the plain text data files)
    or other kind of data (like a person/character/company name) and I want
    to get its imdbID. How can I do it?

:A: The safest thing is probably to do a normal search on IMDb (using
    the "http" data access system of IMDbPY) and see if the first item is
    the correct one. You can also try the "title2imdbID" method (and similar)
    of the IMDb instance (no matter if you're using "http" or "sql"), but
    expect some failures -in which case it will return None.


:Q: I have an URL (of a movie, person or something else), how can I
    get a Movie/Person/... instance?

:A: Import the ``imdb.helpers`` module and use the ``get_byURL`` function.


:Q: I'm writing an interface based on IMDbPY and I have problems handling
    encoding, chars conversions, replacements of references and so on.

:A: See the many functions in the imdb.helpers module.
