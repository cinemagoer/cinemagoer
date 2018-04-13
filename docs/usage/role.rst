Roles
=====

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
