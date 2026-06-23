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
   <Movie id:0075860[s3] title:_Close Encounters of the Third Kind (1977)_>
   >>> actor = movie['cast'][6]
   >>> actor
   <Person id:0447230[s3] name:_Kemmerling, Warren J._>
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
   <Person id:0330589[s3] name:_Gordon, Sam_>
    >>> crew_member.notes
    'property master'

The ``in`` operator can be used to check whether a person worked in a given
movie or not:

.. code-block:: python

   >>> movie
   <Movie id:0075860[s3] title:_Close Encounters of the Third Kind (1977)_>
   >>> actor
   <Person id:0447230[s3] name:_Kemmerling, Warren J._>
   >>> actor in movie
   True
   >>> crew_member
   <Person id:0330589[s3] name:_Gordon, Sam_>
   >>> crew_member in movie
   True
   >>> person
   <Person id:0000210[s3] name:_Roberts, Julia (I)_>
   >>> person in movie
   False

Obviously these Person objects contain only information directly
available in the retrieved movie data, e.g.: the name, an imdbID, and role data.
So if now you write::

    print(actor['actor'])

to get a list of movies acted by Mel Gibson, you'll get a KeyError exception,
because the Person object doesn't contain this kind of information.


The same is true when parsing person data: you'll find a list of movie
the person worked on and, for every movie, the currentRole instance variable
is set to a string describing the role of the considered person:

.. code-block:: python

    julia = i.get_person('0000210')
    for job in julia['filmography'].keys():
        print('# Job: ', job)
        for movie in julia['filmography'][job]:
            print('\t%s %s (role: %s)' % (movie.movieID, movie['title'], movie.currentRole))

Here the various Movie objects only contain minimal information,
like the title and the year; the latest movie with Julia Roberts:

.. code-block:: python

    last = julia['filmography']['actress'][0]
    # Retrieve full information
    i.update(last)
    # name of the first director
    print(last['director'][0]['name'])


The ``currentRole`` attribute is still available and can contain role names
as provided by dataset-backed information.


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
   i = imdb.Cinemagoer()
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
