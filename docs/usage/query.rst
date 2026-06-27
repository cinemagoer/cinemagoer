Querying data
=============

Method descriptions:

``search_movie(title, results=None, _episodes=False)``
  Searches for the given title, and returns a list of Movie objects containing
  only basic information like the movie title and year, and with a "movieID"
  instance variable. The return parameter can be set to an integer value to
  specify how many results should be returned by search_movie. If _episodes is
  set to true then episodes containing the title parameter are also returned:

   - ``movieID`` is the identifier to pass to ``get_movie()`` in order to
     retrieve full information about the title.

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
methods work the same way as ``search_movie(title)`` and
``get_movie(movieID)``.

The ``get_imdbID(MovieOrPersonObject)`` method returns the imdbID for
the given Movie or Person object.

The ``get_imdbURL(MovieOrPersonObject)`` method returns a string with the
main IMDb URL for the given Movie or Person object.

The ``update(MovieOrPersonObject)`` method takes an instance of a Movie
or Person class, and retrieves other available information.

Remember that the ``search_*(txt)`` methods will return a list of Movie
or Person objects with only basic information,
such as the movie title or the person name. So, ``update()`` can be
used to retrieve every other information.

By default a "reasonable" set of information are retrieved: 'main',
'filmography', and 'biography' for a Person object; 'main' and 'plot'
for a Movie object.

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
    print(first_match['trivia'])
   # retrieve both 'quotes' and 'goofs' information (with a list or tuple)
    i.update(first_match, ['quotes', 'goofs'])
    print(first_match['quotes'])
    print(first_match['goofs'])
   # retrieve every available information.
    i.update(first_match, 'all')
