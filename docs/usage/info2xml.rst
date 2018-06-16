Information in XML format
=========================

Since version 4.0, IMDbPY can output information of Movie, Person, Character,
and Company instances in XML format. It's possible to get a single information
(a key) in XML format, using the ``getAsXML(key)`` method (it will return None
if the key is not found). E.g.:

.. code-block:: python

   from imdb import IMDb
   ia = IMDb('http')
   movie = ia.get_movie(theMovieID)
   print(movie.getAsXML('keywords'))

It's also possible to get a representation of a whole object, using
the ``asXML()`` method::

  print(movie.asXML())

The ``_with_add_keys`` argument of the ``asXML()`` method can be set
to False (default: True) to exclude the dynamically generated keys
(like 'smart canonical title' and so on).


XML format
----------

Keywords are converted to tags, items in lists are enclosed in
a 'item' tag,  e.g.:

.. code-block:: xml

   <keywords>
     <item>a keyword</item>
     <item>another keyword</item>
   </keywords>

Except when keys are known to be not fixed (e.g.: a list of keywords),
in which case this schema is used:

.. code-block:: xml

   <item key="EscapedKeyword">
      ...
   </item>

In general, the 'key' attribute is present whenever the used tag doesn't match
the key name.

Movie, Person, Character and Company instances are converted as follows
(portions in square brackets are optional):

.. code-block:: xml

   <movie id="movieID" access-system="accessSystem">
     <title>A Long IMDb Movie Title (YEAR)</title>
     [<current-role>
        <person id="personID" access-system="accessSystem">
          <name>Name Surname</name>
          [<notes>A Note About The Person</notes>]
        </person>
      </current-role>]
      [<notes>A Note About The Movie</notes>]
   </movie>

Every 'id' can be empty.

The returned XML string is mostly not pretty-printed.


References
----------

Some text keys can contain references to other movies, persons and characters.
The user can provide the ``defaultModFunct`` function (see
the "MOVIE TITLES AND PERSON/CHARACTER NAMES REFERENCES" section of
the README.package file), to replace these references with their own strings
(e.g.: a link to a web page); it's up to the user, to be sure
that the output of the defaultModFunct function is valid XML.


DTD
---

Since version 4.1 a DTD is available; it can be found in this
directory or on the web, at: http://imdbpy.sf.net/dtd/imdbpy41.dtd

The version number changes with the IMDbPY version.


Localization
------------

Since version 4.1 it's possible to translate the XML tags;
see README.locale.


Deserializing
-------------

Since version 4.6, you can dump the generated XML in a string or
in a file, using it -later- to rebuild the original object.
In the ``imdb.helpers`` module there's the ``parseXML()`` function which
takes a string as input and returns -if possible- an instance of the Movie,
Person, Character or Company class.
