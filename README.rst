**IMDbPY** is a Python package for retrieving and managing the data
of the `IMDb`_ movie database about movies, people and companies.

.. admonition:: Revamp notice
   :class: note

   Starting on November 2017, many things were improved and simplified:

   - moved the package to Python 3 (compatible with Python 2.7)
   - removed dependencies: SQLObject, C compiler, BeautifulSoup
   - removed the "mobile" and "httpThin" parsers
   - introduced a testsuite (`please help with it!`_)

   The original Python 2 version is available in the *imdbpy-legacy* branch
   (mostly unsupported).


Main features
-------------

- written in Python 3 (compatible with Python 2.7)

- platform-independent

- can retrieve data from both the IMDb's web server, or a local copy
  of the database

- a simple and complete API

- released under the terms of the GPL 2 license

IMDbPY powers many other software and has been used in various research papers.
`Curious about that`_?


Installation
------------

Whenever it's possible, please always use the latest version
from the repository. To install it using ``pip``:

.. code-block:: sh

    pip3 install git+https://github.com/alberanid/imdbpy


Code example
------------

.. code-block:: python

    from imdb import IMDb

    # create an instance of the IMDb class
    ia = IMDb()

    # get a movie and print its director(s)
    the_matrix = ia.get_movie('0133093')
    print(the_matrix['director'])

    # show all the information sets avaiable for Movie objects
    print(ia.get_movie_infoset())

    # update a Movie object with more information
    ia.update(the_matrix, ['technical'])
    # show which keys were added by the information set
    print(the_matrix.infoset2keys['technical'])
    # print one of the new keys
    print(the_matrix.get('cinematographic process'))

    # search for a person
    for person in ia.search_person('Mel Gibson'):
        print(person.personID, person['name'])

    # get the first result of a company search,
    # update it to get the basic information
    ladd_company = ia.search_company('The Ladd Company')[0]
    ia.update(ladd_company)
    # show the available information and print some
    print(ladd_company.keys())
    print(ladd_company.get('production companies'))

    # get 5 movies tagged with a keyword
    dystopia = ia.get_keyword('dystopia', results=5)

    # get top250 and bottom100 movies
    top250 = ia.get_top250_movies()
    bottom100 = ia.get_bottom100_movies()


S3 database
-----------

IMDb distributes some of the data in their `s3 database`_. Using IMDbPY,
you can easily import them using the ``s32imdbpy.py`` script.
Download the files `from here`_, create an empty database in your favorite
database server, and then run:

.. code-block:: sh

    ./bin/s32imdbpy.py /path/to/the/tsv.gz/files/ URI

where *URI* is the identifier used to access a SQL database
amongst the ones supported by `SQLAlchemy`_,
for example ``postgres://user:password@localhost/imdb``.

You will use the same URI with the "s3" *accessSystem* to create an instance
of the IMDb object that is able to access the database:

.. code-block:: python

    ia = IMDb('s3', uri)

For more information, see **docs/README.s3.txt**


Main objects and methods
------------------------

Create an instance of the IMDb class, to access information from the web
or a SQL database:

.. code-block:: python

    ia = imdb.IMDb()

Return an instance of a Movie, Person or Company class.
The objects have the basic information:

.. code-block:: python

   movie = ia.get_movie(movieID)
   person = ia.get_person(personID)
   company = ia.get_company(companyID)

Return a list of Movie, Person or Company instances. These objects
have only bare information, like title and movieID:

.. code-block:: python

    movies = ia.search_movie(title)
    persons = ia.search_person(name)
    companies = ia.search_company(name)

Update a Movie, Person or Company instance with basic information,
or any other specified info set:

.. code-block:: python

    ia.update(obj, info=infoset)

Return all info sets available for a movie; similar methods are available
for other objects:

.. code-block:: python

    ia.get_movie_infoset()

Mapping between the fetched info sets and the keywords they provide;
similar methods are available for other objects:

.. code-block:: python

    movie.infoset2keys

The ID of the object:

.. code-block:: python

    movie.movieID
    person.personID
    company.companyID

Get a key of an object:

.. code-block:: python

    movie['title']
    person.get('name')

Search for keywords similar to the one provided, and fetch movies matching
a given keyword:

.. code-block:: python

    keywords = ia.search_keyword(keyword)
    movies = ia.get_keyword(keyword)

Get the top 250 and bottom 100 movies:

.. code-block:: python

    ia.get_top250_movies()
    ia.get_bottom100_movies()

Check whether a person worked in a given movie or not:

.. code-block:: python

    person in movie
    movie in person

Check whether a key is present for a movie (or person) or not:

.. code-block:: python

    'cast' in movie
    'filmography' in person


License
-------

IMDbPY is released under the terms of the GNU GPL v2 (or later) license.

.. _IMDb: https://www.imdb.com/
.. _please help with it!: https://sourceforge.net/p/imdbpy/mailman/message/36107729/
.. _Curious about that: https://imdbpy.sourceforge.io/ecosystem.html
.. _s3 database: https://www.imdb.com/interfaces/
.. _from here: https://datasets.imdbws.com/
.. _SQLAlchemy: https://www.sqlalchemy.org/
