# IMDbPY

**IMDbPY** is a Python package useful to retrieve and manage the data of the [IMDb][imdb] movie database about movies, people, characters and companies.


## Revamp notice

Starting on November 2017 many things were improved and simplified:

- move the package to Python 3
- removed dependencies: SQLObject, C compiler, BeautifulSoup
- removed the "mobile" and "httpThin" parsers
- introduced a testsuite ([please help with it!][testsuite])
- the old, Python 2, version is available in the *imdbpy-legacy* branch (mostly unsupported)


## Main features

* written in Python 3
* platform-independent
* can retrieve data from both the IMDb's web server and a local copy of the whole database
* a simple and complete API
* released under the terms of the GPL 2 license
* IMDbPY powers many other softwares and has been used in various research papers. [Curious about that][ecosystem]?


## Installation

Whenever it's possible, please always use the latest version from the repository.  To install it using `pip`:

    pip3 install git+https://github.com/alberanid/imdbpy


## Code example

    # create and instance of the IMDb class
    from imdb import IMDb
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

    # get a Character object
    deckard = ia.search_character('Rick Deckard')[0]
    ia.update(deckard)
    print(deckard['full-size headshot'])

    # get top250 and bottom100 movies
    top250 = ia.get_top250_movies()
    bottom100 = ia.get_bottom100_movies()


## S3 database

IMDb distributes some data in their [s3 database][interface]; using IMDbPY, you can easily import them using the **bin/s32imdbpy.py** script. Download the files [from here][s3dataset], create an empty database in your favorite db server, and then run:

    ./bin/s32imdbpy.py /path/to/the/tsv.gz/files/ uri

where *uri* is the identifier used to access a SQL database amongst the ones supported by [SQLAlchemy][sqlalchemy], for example *postgres://user:password@localhost/imdb*

You will use the same uri with the "s3" *accessSystem* to create an instance of the IMDb object that is able to access the database:

    ia = IMDb('s3', 'uri')

For more information, see **docs/README.s3.txt**


## Main objects and methods

> **ia = imdb.IMDb()**

create an instance of the IMDb class, to access information from the web or a SQL database.

> **movie = ia.get_movie(** movieID **)**<br>
> **person = ia.get_person(** personID **)**<br>
> **company = ia.get_company(** companyID **)**<br>
> **character = ia.get_character(** characterID **)**

return an instance of a Movie, Person, Company or Character classes. The objects have the basic information.

> **movies = ia.search_movie(** title **)**<br>
> **persons = ia.search_person(** name **)**<br>
> **companies = ia.search_company(** name **)**<br>
> **characters = ia.search_characters(** name **)**

return a list of Movie, Person, Company or Character instances. These objects have only bare information, like title and movieID.

> **ia.update(** obj, [info='infoset'] **)**

update a Movie, Person, Company or Character instance with basic information, or any other specified info set.

> **ia.get_movie_infoset()**

all the info set available for a movie; similar methods are available for other objects.

> **movie.infoset2keys**

mapping between the fetched info sets and the keywords they provide; similar methods are available for other objects.

> **movie.movieID**<br>
> **person.personID**<br>
> **company.companyID**<br>
> **character.characterID**

the ID of the object.

> **movie['title']**<br>
> **person.get('name')**

get a key of an object.

> **keywords = ia.search_keyword(** keyword **)**<br>
> **movies = ia.get_keyword(** keyword **)**

search for keywords similar to the one provided, and fetch movies matching a given keyword.

> **ia.get_top250_movies()**<br>
> **ia.get_bottom100_movies()**

top 250 and bottom 100 movies.

> **person_in_cast = movie['cast'][0]**<br>
> **notes = person_in_cast.notes**<br>
> **character = person_in_cast.currentRole**

character associated to a person who starred in a movie, and its notes.

> **person** in **movie**<br>
> **movie** in **person**

return True if a person worked in a given movie


## License

IMDbPY is released under the terms of the GNU GPL v2 (or later) license.

[imdb]: http://imdb.com
[ecosystem]: http://imdbpy.sourceforge.net/ecosystem.html
[testsuite]: https://sourceforge.net/p/imdbpy/mailman/message/36107729/
[interface]: http://www.imdb.com/interfaces/
[s3dataset]: https://datasets.imdbws.com/
[sqlalchemy]: https://www.sqlalchemy.org/
