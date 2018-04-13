:orphan:

Querying data
=============

Method descriptions:

``search_movie(title)``
  Searches for the given title, and returns a list of Movie objects containing
  only basic information like the movie title and year, and with a "movieID"
  instance variable:

   - ``movieID`` is an identifier of some kind; for the sake of simplicity
     you can think of it as the ID used by the IMDb's web server used
     to uniquely identify a movie (e.g.: '0094226' for Brian De Palma's
     "The Untouchables"), but keep in mind that it's not necessary the
     same ID!!!

     For some implementations of the "data access system" these two IDs can
     be the same (as is the case for the 'http' data access system), but
     other access systems can use a totally different kind of movieID.
     The easier (I hope!) way to understand this is to think of the movieID
     returned by the search_movie() method as the *thing* you have to pass
     to the get_movie() method, so that it can retrieve info about the referred
     movie.

     So, movieID *can* be the imdbID ('0094226') if you're accessing the web
     server, but with a SQL installation of the IMDb database, movieID will be
     an integer, as read from the id column in the database.

``search_episode(title)``
  This is identical to ``search_movie()``, except that it is tailored
  to searching for titles of TV series episodes. Best results are expected
  when searching for just the title of the episode, *without* the title
  of the TV series.

``get_movie(movieID)``
  This will fetch the needed data and return a Movie object for the movie
  referenced by the given movieID. The Movie class can be found in the Movie
  module. A Movie object presents basically the same interface of a Python's
  dictionary; so you can access, for example, the list of actors and actresses
  using the syntax ``movieObject['cast']``.

The ``search_person(name)``, ``get_person(personID)``,
``search_character(name)``, ``get_character(characterID)``,
``search_company(name)``, and ``get_company(companyID)`` methods work the same
way as ``search_movie(title)`` and ``get_movie(movieID)``.

The ``search_keyword(string)`` method returns a list of strings that are
valid keywords, similar to the one given.

The ``get_keyword(keyword)`` method returns a list of Movie instances that
are tagged with the given keyword.

The ``get_imdbMovieID(movieID)``, ``get_imdbPersonID(personID)``,
``get_imdbCharacterID(characterID)``, and ``get_imdbCompanyID(companyID)``
methods take, respectively, a movieID, a personID, a movieID, or a companyID
and return the relative imdbID; it's safer to use the
``get_imdbID(MovieOrPersonOrCharacterOrCompanyObject)`` method.

The ``title2imdbID(title)``, ``name2imdbID(name)``, ``character2imdbID(name)``,
and ``company2imdbID(name)`` methods take, respectively, a movie title
(in the plain text data files format), a person name, a character name, or
a company name, and return the relative imdbID; when possible it's safer
to use the ``get_imdbID(MovieOrPersonOrCharacterOrCompanyObject)`` method.

The ``get_imdbID(MovieOrPersonOrCharacterOrCompanyObject)`` method returns
the imdbID for the given Movie, Person, Character or Company object.

The ``get_imdbURL(MovieOrPersonOrCharacterOrCompanyObject)`` method returns
a string with the main IMDb URL for the given Movie, Person, Character, or
Company object; it does its best to retrieve the URL.

The ``update(MovieOrPersonOrCharacterOrCompanyObject)`` method takes
an instance of a Movie, Person, Character, or Company class, and retrieves
other available information.

Remember that the ``search_*(txt)``  methods will return a list of Movie,
Person, Character or Company objects with only basic information,
such as the movie title or the person/character name. So, ``update()`` can be
used to retrieve every other information.

By default a "reasonable" set of information are retrieved: 'main',
'filmography', and 'biography' for a Person/Character object; 'main' and 'plot'
for a Movie object; 'main' for a Company object.

Example:

.. code-block:: python

   # only basic information like the title will be printed.
   print(first_match.summary())
   # update the information for this movie.
   i.update(first_match)
   # a lot of information will be printed!
   print(first_match.summary())
   # retrieve trivia information
   i.update(first_match, 'trivia')
    print(m['trivia'])
   # retrieve both 'quotes' and 'goofs' information (with a list or tuple)
   i.update(m, ['quotes', 'goofs'])
   print(m['quotes'])
   print(m['goofs'])
   # retrieve every available information.
   i.update(m, 'all')
