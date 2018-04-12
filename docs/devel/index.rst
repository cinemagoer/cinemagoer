Development
===========

.. packages
  imdb (package)
        Contains the IMDb function, the IMDbBase class and imports
        the IMDbError exception class.
  _exceptions
        Defines the exceptions internally used.
  _logging
        Provides the logging facility used by IMDbPY.
  linguistics
        Defines some functions and data useful to smartly guess the language
        of a movie title (internally used).
  Movie
        Contains the Movie class, used to describe and manage a movie.
  Person
        Contains the Person class, used to describe and manage a person.
  Character
        Contains the Character class, used to describe and manage a character.
  Company
        Contains the Company, used to describe and manage a company.
  utils
        Miscellaneous utilities used by many IMDbPY modules.
  parser (package)
        A package containing a package for every data access system implemented.
  http (package)
        Contains the IMDbHTTPAccessSystem class which is a subclass
        of the imdb.IMDbBase class; it provides the methods used to retrieve and
        manage data from the web server (using, in turn, the other modules in
        the package). It defines methods to get a movie and to search for a title.
  http.movieParser
        Parse HTML strings from the pages on the IMDb web server about a movie;
        returns dictionaries of {key: value}.
  http.personParser
        Parse HTML strings from the pages on the IMDb web server about a person;
        returns dictionaries.
  http.characterParser
        Parse HTML strings from the pages on the IMDb web server about a character;
        returns dictionaries.
  http.companyParser
        Parse HTML strings from the pages on the IMDb web server about a company;
        returns dictionaries.
  http.searchMovieParser
        Parse an HTML string, result of a query for a movie title.
  http.searchPersonParser
        Parse an HTML string, result of a query for a person name.
  http.searchCharacterParser
        Parse an HTML string, result of a query for a character name.
  http.searchCompanyParser
        Parse an HTML string, result of a query for a company name.
  http.searchKeywordParser
        Parse an HTML string, result of a query for a keyword.
  http.topBottomParser
        Parse an HTML string, result of a query for top250 and bottom100 movies.
  http.utils
        Miscellaneous utilities used only by the http package.
  The parser.sql package manages the access to the data in the SQL database,
  created with the imdbpy2sql.py script; see the README.sqldb file.
  The dbschema module contains tables definitions and some useful functions.
  The helpers module contains functions and other goodies not directly used
  by the IMDbPY package, but that can be useful to develop IMDbPY-based programs.

I wanted to stay independent from the source of the data for a given
movie/person/character/company, and so the imdb.IMDb function returns
an instance of a class that provides specific methods to access a given
data source (web server, SQL database, etc.)

Unfortunately that means that the movieID in the Movie class, the personID
in the Person class and the characterID in the Character class are dependent
on the data access system used. So, when a Movie, a Person or a Character
object is instantiated, the accessSystem instance variable is set to a string
used to identify the used data access system.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   extend
   test
   release
