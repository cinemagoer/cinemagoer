How to extend
-------------

To introduce a new data access system, you have to write a new package
inside the "parser" package; this new package must provide a subclass
of the imdb.IMDb class which must define at least the following methods:

``_search_movie(title)``
  To search for a given title; must return a list of (movieID, {movieData})
  tuples.

``_search_episode(title)``
  To search for a given episode title; must return a list of
  (movieID, {movieData}) tuples.

``_search_person(name)``
  To search for a given name; must return a list of (movieID, {personData})
  tuples.

``_search_character(name)``
  To search for a given character's name; must return a list of
  (characterID, {characterData}) tuples.

``_search_company(name)``
  To search for a given company's name; must return a list of
  (companyID, {companyData}) tuples.

``get_movie_*(movieID)``
   A set of methods, one for every set of information defined for a Movie
   object; should return a dictionary with the relative information.

   This dictionary can contain some optional keys:

   - 'data': must be a dictionary with the movie info
   - 'titlesRefs': a dictionary of 'movie title': movieObj pairs
   - 'namesRefs': a dictionary of 'person name': personObj pairs

``get_person_*(personID)``
  A set of methods, one for every set of information defined for a Person
  object; should return a dictionary with the relative information.

``get_character_*(characterID)``
  A set of methods, one for every set of information defined for a Character
  object; should return a dictionary with the relative information.

``get_company_*(companyID)``
  A set of methods, one for every set of information defined for a Company
  object; should return a dictionary with the relative information.

``_get_top_bottom_movies(kind)``
  Kind can be one of 'top' and 'bottom'; returns the related list of movies.

``_get_keyword(keyword)``
  Return a list of Movie objects with the given keyword.

``_search_keyword(key)``
  Return a list of keywords similar to the given key.

``get_imdbMovieID(movieID)``
  Convert the given movieID to a string representing the imdbID, as used
  by the IMDb web server (e.g.: '0094226' for Brian De Palma's
  "The Untouchables").

``get_imdbPersonID(personID)``
  Convert the given personID to a string representing the imdbID, as used
  by the IMDb web server (e.g.: '0000154' for "Mel Gibson").

``get_imdbCharacterID(characterID)``
  Convert the given characterID to a string representing the imdbID, as used
  by the IMDb web server (e.g.: '0000001' for "Jesse James").

``get_imdbCompanyID(companyID)``
  Convert the given companyID to a string representing the imdbID, as used
  by the IMDb web server (e.g.: '0071509' for "Columbia Pictures [us]").

``_normalize_movieID(movieID)``
  Convert the provided movieID in a format suitable for internal use
  (e.g.: convert a string to a long int).

  NOTE: As a rule of thumb you *always* need to provide a way to convert
  a "string representation of the movieID" into the internally used format,
  and the internally used format should *always* be converted to a string,
  in a way or another. Rationale: A movieID can be passed from the command
  line, or from a web browser.

``_normalize_personID(personID)``
  idem

``_normalize_characterID(characterID)``
  idem

``_normalize_companyID(companyID)``
  idem

``_get_real_movieID(movieID)``
  Return the true movieID; useful to handle title aliases.

``_get_real_personID(personID)``
  idem

``_get_real_characterID(characterID)``
  idem

``_get_real_companyID(companyID)``
  idem

The class should raise the appropriate exceptions, when needed:

- ``IMDbDataAccessError`` must be raised when you cannot access the resource
  you need to retrieve movie info or you're unable to do a query (this is
  *not* the case when a query returns zero matches: in this situation an
  empty list must be returned).

- ``IMDbParserError`` should be raised when an error occurred parsing
  some data.

Now you've to modify the ``imdb.IMDb`` function so that, when the right
data access system is selected with the "accessSystem" parameter, an instance
of your newly created class is returned.

For example, if you want to call your new data access system "mysql"
(meaning that the data are stored in a mysql database), you have to add
to the imdb.IMDb function something like:

.. code-block:: python

   if accessSystem == 'mysql':
       from parser.mysql import IMDbMysqlAccessSystem
       return IMDbMysqlAccessSystem(*arguments, **keywords)

where "parser.mysql" is the package you've created to access the local
installation, and "IMDbMysqlAccessSystem" is the subclass of imdb.IMDbBase.

Then it's possible to use the new data access system like:

.. code-block:: python

   from imdb import IMDb
   i = IMDb(accessSystem='mysql')
   results = i.search_movie('the matrix')
   print(results)

.. note::

   This is a somewhat misleading example: we already have a data access system
   for SQL database (it's called 'sql' and it supports MySQL, amongst others).
   Maybe I'll find a better example...

A specific data access system implementation can define its own methods.
As an example, the IMDbHTTPAccessSystem that is in the parser.http package
defines the method ``set_proxy()`` to manage the use a web proxy; you can use
it this way:

.. code-block:: python

   from imdb import IMDb
   i = IMDb(accessSystem='http') # the 'accessSystem' argument is not
                                 # really needed, since "http" is the default.
   i.set_proxy('http://localhost:8080/')

A list of special methods provided by the imdb.IMDbBase subclass, along with
their description, is always available calling the ``get_special_methods()``
of the IMDb class:

.. code-block:: python

   i = IMDb(accessSystem='http')
   print(i.get_special_methods())

will print a dictionary with the format::

  {'method_name': 'method_description', ...}
