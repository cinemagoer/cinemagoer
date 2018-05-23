Usage
=====

Here you can find information about how to use IMDbPY to write your own scripts
or programs.

This document is far from complete: the code is the final documentation! ;-)

Sections in this file:

- General usage
- Movie class
- Person class
- Character class
- Company class
- Information sets
- Top 250 / Bottom 100 lists
- Persons in movies and Movies in persons
- Companies in movies and Movies in companies
- The (not-so) "universal" "::" separator
- Movie titles and Person/Character names references
- Exceptions
- Other sources of information


General usage
-------------

To use the IMDbPY package, you have to import the imdb package and
call the IMDb function:

.. code-block:: python

   import imdb
   imdb_access = imdb.IMDb()

If you're accessing a SQL installation of the IMDb's data, you have to use
the following:

.. code-block:: python

   imdb_access = imdb.IMDb('s3', uri='URI_TO_YOUR_DB')

where ``URI_TO_YOUR_DB`` points to your SQL database (see README.sqldb
for more information).

Now you have the "imdb_access" object, instance of a subclass of
the ``imdb.IMDbBase`` class, which can be used to search for a given
title/name and to retrieve information about the referred movie, person,
or character.

The ``IMDb`` function can be called with a 'accessSystem' keyword argument,
which must be a string representing the type of data access you want to use.
That's because different systems to access the IMDb data are available:
you can directly fetch data from the web server; you can have a local copy
of the database (see http://www.imdb.com/interfaces/); you can access data
through the e-mail interface, etc.

+---------------------------+-------------+-----------------------------------+
| Supported access systems  |   Aliases   |  Description                      |
+===========================+=============+===================================+
| (default) 'http'          |    'web',   | information fetched through       |
|                           |             |                                   |
|                           |    'html'   | imdb.com web server               |
+---------------------------+-------------+-----------------------------------+
|            'sql'          |    'db',    | information fetched through       |
|                           |             |                                   |
|                           |  'database' | a SQL database (any database      |
|                           |             |                                   |
|                           |             | supported by SQLAlchemy).         |
|                           |             |                                   |
|                           |             | OLD DATASET NOT UPDATED!          |
+---------------------------+-------------+-----------------------------------+
|            's3'           | 's3dataset' | new imdb database                 |
+---------------------------+-------------+-----------------------------------+

.. note::

   Since release 3.4, the 'imdbpy.cfg' configuration file is available,
   so that you can set a system-wide (or per-user) default. The file is
   commented with indication of the location where it can be put,
   and how to modify it.

   If no imdbpy.cfg file is found (or is not readable or it can't be parsed),
   'http' is the default.


The imdb_access object has 10 main methods: ``search_movie(title)``,
``get_movie(movieID)``, ``search_person(name)``, ``get_person(personID)``,
``search_character(name)``, ``get_character(characterID)``,
``search_company(name)``, ``get_company(companyID)``, ``search_episode()``,
``update(MovieOrPersonObject)``.

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

   i = IMDb()
   # movie_list is a list of Movie objects, with only attributes like 'title'
   # and 'year' defined.
   movie_list = i.search_movie('the passion')
   # the first movie in the list.
   first_match = movie_list[0]
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


Movie class
-----------

The main use of a Movie object is to access to the info it contains
using a dictionary-like interface, like "movieObject[key]" where 'key'
is a string that identifies the information you want to get.

I've really bad news for you: at this time, what 'key' is, is a
little unclear! <g>

In general, it's the name of the section as used by the IMDb web server
to show the data. When the information is a list of people with a role
(an actor, a stunt, a writer, etc.) the relative section in the HTML page
starts with a link to a "/Glossary/X#SectName" page; here "sectname"
is used as 'key'.

When the info regards companies (distributors, special effects, etc.)
or the movie itself (sound mix, certifications, etc.), the section in the HTML
page begins with a link to a "/List?SectName=" page, so we use "sectname"
as a 'key'.

The section name (the key) is always (with some minor exceptions) lowercase;
underscores and dashes are replaced with spaces. Some other keys aren't taken
from the HTML page, but are defined within the Movie class.

To get the complete list of keys available for a given Movie object, you can
use the ``movieObject.keys()`` method (obviously only keys that refer
to some existing information are defined. So a movie without an art director
will raise a KeyError exception is you try ``movieObject['art director'])``.
To avoid the exception, you can test if a Movie object has a given key using
``key in movieObject``, or get the value with the ``get(key)`` method,
which returns the value or None if the key is not found (an optional parameter
can modify the default value returned if the key isn't found).

Below is a list of the main keys you can encounter, the type of the value
returned by movieObject[key], and a short description/example:

title (string)
  The "usual" title of the movie, like "The Untouchables".

long imdb title (string)
  "Uncommon Valor (1983/II) (TV)"

canonical title (string)
  The title in canonical format, like "Untouchables, The".

long imdb canonical title (string)
  "Patriot, The (2000)"

year (string)
  The release year, or '????' if unknown.

kind (string)
  One of: 'movie', 'tv series', 'tv mini series', 'video game', 'video movie',
  'tv movie', 'episode'

imdbIndex (string)
  The roman numeral for movies with the same title/year.

director (Person list)
  A list of directors' names, e.g.: ['Brian De Palma'].

cast (Person list)
  A list of actors/actresses, with the currentRole instance variable
  set to a Character object which describe his role.

cover url (string)
  The link to the image of the poster.

writer (Person list)
  A list of writers, e.g.: ['Oscar Fraley (novel)'].

plot (list)
  A list of plot summaries and their authors.

rating (string)
  User rating on IMDb from 1 to 10, e.g. '7.8'.

votes (string)
  Number of votes, e.g. '24,101'.

runtimes (string list)
  List of runtimes in minutes ['119'], or something like ['USA:118', 'UK:116'].

number of episodes (int)
  Number or episodes for a TV series.

color info (string list)
  ["Color (Technicolor)"]

countries (string list)
  Production's country, e.g. ['USA', 'Italy'].

genres (string list)
  One or more of: Action, Adventure, Adult, Animation, Comedy, Crime,
  Documentary, Drama, Family, Fantasy, Film-Noir, Horror, Musical, Mystery,
  Romance, Sci-Fi, Short, Thriller, War, Western, and other genres
  defined by IMDb.

akas (string list)
  List of alternative titles.

languages (string list)
  A list of languages.

certificates (string list)
  ['UK:15', 'USA:R']

mpaa (string)
  The MPAA rating.

episodes (series only) (dictionary of dictionaries)
  One key for every season, one key for every episode in the season.

number of episodes (series only) (int)
  Total number of episodes.

number of seasons (series only) (int)
  Total number of seasons.

series years (series only) (string)
  Range of years when the series was produced.

episode of (episodes only) (Movie object)
  The series to which the episode belongs.

season (episodes only) (int)
  The season number.

episode (episodes only) (int)
  The number of the episode in the season.

long imdb episode title (episodes only) (string)
  Episode and series title.

series title (string)
  The title of the series to which the episode belongs.

canonical series title (string)
  The canonical title of the series to which the episode belongs.


Other keys that contain a list of Person objects are: costume designer,
sound crew, crewmembers, editor, production manager, visual effects,
assistant director, art department, composer, art director, cinematographer,
make up, stunt performer, producer, set decorator, production designer.

Other keys that contain list of companies are: production companies, special
effects, sound mix, special effects companies, miscellaneous companies,
distributors.

Converting a title to its "Title, The" canonical format, IMDbPY makes
some assumptions about what is an article and what isn't, and this could
lead to some wrong canonical titles. For more information on this subject,
see the "ARTICLES IN TITLES" section of the README.locale file.


Person class
------------

It works mostly like the Movie class. :-)

The Movie class defines a ``__contains__()`` method, which is used to check
if a given person has worked in a given movie with the syntax:

.. code-block:: python

   if personObject in movieObject:
       print('%s worked in %s' % (personObject['name'], movieObject['title']))

The Person class defines a ``isSamePerson(otherPersonObject)`` method, which
can be used to compare two person objects. This can be used to check whether
an object has retrieved complete information or not, as in the case of a Person
object returned by a query:

.. code-block:: python

   if personObject.isSamePerson(otherPersonObject):
       print('they are the same person!')

A similar method is defined for the Movie class, and it's called
``isSameTitle(otherMovieObject)``.


Character class
---------------

It works mostly like the Person class. :-)

For more information about the "currentRole" attribute, see the
README.currentRole file.


Company class
-------------

It works mostly like the Person class. :-)

The "currentRole" attribute is always None.


Information sets
----------------

Since release 1.2, it's possible to retrieve almost every piece of information
about a given movie or person. This can be a problem, because (at least for
the 'http' data access system) it means that a lot of web pages must be fetched
and parsed, and this can be time and bandwidth consuming, especially if you're
interested only in a small set of the information.

Now the ``get_person``, ``get_movie``, ``get_character``, ``get_company``,
and ``update`` methods have an optional 'info' argument, which can be set
to a list of strings, each one representing an "information set".
Movie/Person/Character/Company objects have, respectively, their own list
of available "information sets". For example, the Movie class has a set called
'taglines' for the taglines of the movie, a set called 'vote details'
for the number of votes for rating [1-10], demographic breakdowns and
top 250 rank. The Person class has a set called 'other works' for miscellaneous
works of this person and so on.

By default only important information are retrieved/updated, i.e. for a Movie
object, only 'main' and 'plot'; for a Person/Character object only 'main',
'filmography', and 'biography'.

Example:

.. code-block:: python

   >>> i = imdb.IMDb(accessSystem='http')

   >>> m = i.get_movie('0133093')  # only default info set are retrieved.
   >>> 'demographic' in m          # returns false, since no demographic breakdowns
                                   # aren't available by default

   >>> i.update(m, info=('vote details',))  # retrieve the vote details info set
   >>> print(m['demographic']               # demographic breakdowns.

Another example:

.. code-block:: python

   i = imdb.IMDb(accessSystem='http')

   # retrieve only the biography and the "other works" page
   p = i.get_person('0000154', info=['biography', 'other works'])
   print(p['salary'])
   print(p['other works'])

To see which information sets are available and what the defaults are,
see the all_info and default_info instance variables of Movie, Person,
and Character classes. Each instance of Movie, Person, or Character,
also have a current_info instance variable, for tracking the information sets
already retrieved.

Beware that the information sets vary from an access system to another:
locally not every data is accessible, while -for example for SQL-
accessing one set of data means automatically accessing a number of other
information (without major performace drawbacks).

You can get the list of available info set with the methods:
``i.get_movie_infoset()``, ``i.get_person_infoset()``,
``i.get_character_infoset()``, and ``i.get_company_infoset()``.


Top 250 / Bottom 100 lists
--------------------------

Since IMDbPY 4.0, it's possible to retrieve the list of top 250 and bottom 100
movies. Use the ``get_top250_movies()`` and ``get_bottom100_movies()`` methods.
Beware that, for 'SQL', the bottom100 list is limited to the first 10 results.


Persons in movies and Movies in persons
---------------------------------------

Parsing the information about a movie, you'll encounter a lot of references
to the people who worked on it, like the cast, the director, the stunts,
and so on.

For people in the cast (actors/actresses), the "currentRole" instance
variable is set to the name of the character they played (e.g.: "Roy Neary"
for the role played by Richard Dreyfuss in Close Encounters of the Third Kind).
In this case currentRole will be a Character instance.

Another instance variable of a Person object is "notes", used to store
miscellaneous information (like an aka name for the actor, an "uncredited"
notice and so on).

It's also used, for non-cast people, to describe the job of the person
(e.g.: "assistant dialogue staff" for a person of the sound department).

It's possible to test, using the ``in`` operator, if a person worked
in a given movie, or vice-versa; the following are all valid tests:

.. code-block:: python

   movie in person
   movie in character
   person in movie
   person in character
   character in movie
   character in person

Similar usage can be considered for Character instances: please read
the README.currentRole file for more information.

.. code-block:: python

    # retrieve data for Steven Spielberg's "Close Encounters of the Third Kind"
    import imdb
    i =  imdb.IMDb(accessSystem='http')
    movie = i.get_movie('0075860')

    # Get the 7th Person object in the cast list
    cast = movie['cast'][6]
    # "Warren J. Kemmerling"
    print(cast['name'])
    # "Wild Bill"
    print(cast.currentRole)
    # "(as Warren Kemmerling)"
    print(cast.notes)

    # Get the 5th Person object in the list of writers
    writer = movie['writer'][4]
    # "Steven Spielberg"
    print(writer['name'])
    # "written by", because that was the duty of Steven Spielberg,
    # as a writer for the movie.
    print(writer.notes)

Obviously these Person objects contain only information directly
available upon parsing the movie pages, e.g.: the name, an imdbID, the role.
So if now you write::

    print(writer['actor'])

to get a list of movies acted by Mel Gibson, you'll get a KeyError exception,
because the Person object doesn't contain this kind of information.

To gather every available information, you've to use the ``update()`` method
of the IMDb class:

.. code-block:: python

    i.update(writer)
    # a list of Movie objects.
    print(writer['actor'])

The same is true when parsing person data: you'll find a list of movie
the person worked on and, for every movie, the currentRole instance variable
is set to a string describing the role of the considered person:

.. code-block:: python

    # Julia Roberts
    julia = i.get_person('0000210')
    # Output a list of movies she acted in and the played role
    # separated by '::'
    print([movie['title'] + '::' + movie.currentRole
           for movie in julia['actress']])

Here the various Movie objects only contain minimal information,
like the title and the year; the latest movie with Julia Roberts:

.. code-block:: python

    last = julia['actress'][0]
    # Retrieve full information
    i.update(last)
    # name of the first director
    print(last['director'][0]['name'])


Companies in movies and Movies in companies
-------------------------------------------

As for Person/Character and Movie objects, you can test -using the "in"
operator- if a Company has worked on a given Movie.


The (not so) "universal" "::" separator
---------------------------------------

Sometimes I've used "::" to separate a set of different data inside a string,
like the name of a company and what it has done for the movie, the information
in the "Also Known As" section, and so on.

It's easier to understand if you look at it; look at the output of:

.. code-block:: python

   import imdb
   i = imdb.IMDb()
   m = i.get_movie('0094226')
   print(m['akas'])

As a rule, there's at most one '::' separator inside a string. Splitting it
will result in two logical pieces: "TEXT::NOTE".
In the helpers module there's the ``makeTextNotes`` function that can be used
to create a custom function to pretty-print this kind of information.
See its documentation for more info.


Movie titles and Person/Character names references
--------------------------------------------------

Sometimes in Movie, Person and Character attributes, there are strings
with references to other movies or persons, e.g. in the plot, in the biography,
etc. These references are stored in the Movie, Person, and Character
instances; in the strings you will find values like _A Movie (2003)_ (qv)
or 'A Person' (qv) or '#A Character# (qv)'. When these strings are accessed
(like movie['plot'] or person['biography']), they will be modified using
a provided function, which must take the string and two dictionaries
containing titles and names references as parameters.

By default the (qv) strings are converted in the "normal" format
("A Movie (2003)", "A Person" and "A Character").

You can find some examples of these functions in the
imdb.utils module.

The function used to modify the strings can be set with the ``defaultModFunct``
parameter of the IMDb class or with the ``modFunct`` parameter
of the ``get_movie``, ``get_person``, and ``get_character`` methods:

.. code-block:: python

   import imdb
   i = imdb.IMDb(defaultModFunct=imdb.utils.modHtmlLinks)

or:

.. code-block:: python

   import imdb
   i = imdb.IMDb()
   i.get_person('0000154', modFunct=imdb.utils.modHtmlLinks)


Exceptions
----------

The ``imdb._exceptions`` module contains the exceptions raised by the imdb
package. Every exception is a subclass of ``IMDbError``, which is available
from the imdb package.

You can catch any type of errors raised by the IMDbPY package with
something like:

.. code-block:: python

   from imdb import IMDb, IMDbError

   try:
       i = IMDb()
   except IMDbError, err:
       print(err)

   try:
       results = i.search_person('Mel Gibson')
   except IMDbError, err:
       print(err)

   try:
       movie = i.get_movie('0335345')
   except IMDbError, err:
       print(err)


Other sources of information
----------------------------

Once the IMDbPY package is installed, you can read the docstrings for packages,
modules, functions, classes, objects, methods using the pydoc program;
e.g.: "pydoc imdb.IMDb" will show the documentation about the imdb.IMDb class.

The code contains a lot of comments, try reading it, if you canunderstand
my English!
