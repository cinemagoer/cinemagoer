Information sets
================

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
