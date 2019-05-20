Roles
=====

When parsing data of a movie, you'll encounter references to the people
who worked on it, like its cast, director and crew members.

For people in the cast (actors and actresses),
the :attr:`currentRole <imdb.Person.Person.currentRole>` attribute is set to the name
of the character they played:

.. code-block:: python

   >>> movie = ia.get_movie('0075860')
   >>> movie
   <Movie id:0075860[http] title:_Close Encounters of the Third Kind (1977)_>
   >>> actor = movie['cast'][6]
   >>> actor
   <Person id:0447230[http] name:_Kemmerling, Warren J._>
   >>> actor['name']
   'Warren J. Kemmerling'
   >>> actor.currentRole
   'Wild Bill'

Miscellaneous data, such as an AKA name for the actor or an "uncredited"
notice, is stored in the :attr:`notes <imdb.Person.Person.notes>` attribute:

.. code-block:: python

   >>> actor.notes
   '(as Warren Kemmerling)'

For crew members other than the cast,
the :attr:`notes <imdb.Person.Person.notes>` attribute contains the description
of the person's job:

.. code-block:: python

    >>> crew_member = movie['art department'][0]
    >>> crew_member
    <Person id:0330589[http] name:_Gordon, Sam_>
    >>> crew_member.notes
    'property master'

The ``in`` operator can be used to check whether a person worked in a given
movie or not:

.. code-block:: python

   >>> movie
   <Movie id:0075860[http] title:_Close Encounters of the Third Kind (1977)_>
   >>> actor
   <Person id:0447230[http] name:_Kemmerling, Warren J._>
   >>> actor in movie
   True
   >>> crew_member
   <Person id:0330589[http] name:_Gordon, Sam_>
   >>> crew_member in movie
   True
   >>> person
   <Person id:0000210[http] name:_Roberts, Julia (I)_>
   >>> person in movie
   False

Obviously these Person objects contain only information directly
available upon parsing the movie pages, e.g.: the name, an imdbID, the role.
So if now you write::

    print(writer['actor'])

to get a list of movies acted by Mel Gibson, you'll get a KeyError exception,
because the Person object doesn't contain this kind of information.


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


.. note::

   Since the end of 2017, IMDb has removed the Character kind of information.
   This document is still valid, but only for the obsolete "sql" data access
   system.

Since version 3.3, IMDbPY supports the character pages of the IMDb database;
this required some substantial changes to how actors' and acresses' roles
were handled. Starting with release 3.4, "sql" data access system is supported,
too - but it works a bit differently from "http". See "SQL" below.

The currentRole instance attribute can be found in every instance of Person,
Movie and Character classes, even if actually the Character never uses it.

The currentRole of a Person object is set to a Character instance, inside
a list of person who acted in a given movie. The currentRole of a Movie object
is set to a Character instance, inside a list of movies played be given person.
The currentRole of a Movie object is set to a Person instance, inside a list
of movies in which a given character was portrayed.

Schema::

  movie['cast'][0].currentRole -> a Character object.
                |
                +-> a Person object.

  person['actor'][0].currentRole -> a Character object.
                  |
                  +-> a Movie object.

  character['filmography'][0].currentRole -> a Person object.
                           |
                           +-> a Movie object.

The roleID attribute can be used to access/set the characterID or personID
instance attribute of the current currentRole. When building Movie or Person
objects, you can pass the currentRole parameter and the roleID parameter
(to set the ID). The currentRole parameter can be an object
(Character or Person), a string (in which case a Character or Person object is
automatically instantiated) or a list of objects or strings (to handle multiple
characters played by the same actor/actress in a movie, or character played
by more then a single actor/actress in the same movie).

Anyway, currentRole objects (Character or Person instances) can be
pretty-printed easily: calling unicode(CharacterOrPersonObject) will return
a good-old-string.


SQL
---

Fetching data from the web, only characters with an active page on the web site
will have their characterID; we don't have these information when accessing
through "sql", so *every* character will have an associated characterID.
This way, every character with the same name will share the same characterID,
even if - in fact - they may not be portraying the same character.


Goodies
-------

To help getting the required information from Movie, Person and Character
objects, in the "helpers" module there's a new factory function,
makeObject2Txt, which can be used to create your pretty-printing function.
It takes some optional parameters: movieTxt, personTxt, characterTxt
and companyTxt; in these strings %(value)s items are replaced with
object['value'] or with obj.value (if the first is not present).

E.g.:

.. code-block:: python

   import imdb
   myPrint = imdb.helpers.makeObject2Txt(personTxt=u'%(name)s ... %(currentRole)s')
   i = imdb.IMDb()
   m = i.get_movie('0057012')
   ps = m['cast'][0]
   print(myPrint(ps))
   # The output will be something like:
   # Peter Sellers ... Group Captain Lionel Mandrake / President Merkin Muffley / Dr. Strangelove


Portions of the formatting string can be stripped conditionally:
if the specified condition is false, they will be cancelled.

E.g.::

  myPrint = imdb.helpers.makeObject2Txt(personTxt='<if personID><a href=/person/%(personID)s></if personID>%(long imdb name)s<if personID></a></if personID><if currentRole> ... %(currentRole)s<if notes> %(notes)s</if notes></if currentRole>'


Another useful argument is 'applyToValues': if set to a function, it will be
applied to every value before the substitution; it can be useful to format
strings for HTML output.
