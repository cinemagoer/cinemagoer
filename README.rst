|pypi| |pyversions| |license| |travis|

.. |pypi| image:: https://img.shields.io/pypi/v/imdbpy.svg?style=flat-square
    :target: https://pypi.org/project/imdbpy/
    :alt: PyPI version.

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/imdbpy.svg?style=flat-square
    :target: https://pypi.org/project/imdbpy/
    :alt: Supported Python versions.

.. |license| image:: https://img.shields.io/pypi/l/imdbpy.svg?style=flat-square
    :target: https://github.com/alberanid/imdbpy/blob/master/LICENSE.txt
    :alt: Project license.

.. |travis| image:: https://travis-ci.org/alberanid/imdbpy.svg?branch=master
    :target: https://travis-ci.org/alberanid/imdbpy
    :alt: Travis CI build status.


**IMDbPY** is a Python package for retrieving and managing the data
of the `IMDb`_ movie database about movies, people and companies.

.. admonition:: Revamp notice
   :class: note

   Starting on November 2017, many things were improved and simplified:

   - moved the package to Python 3 (compatible with Python 2.7)
   - removed dependencies: SQLObject, C compiler, BeautifulSoup
   - removed the "mobile" and "httpThin" parsers
   - introduced a test suite (`please help with it!`_)


Main features
-------------

- written in Python 3 (compatible with Python 2.7)

- platform-independent

- can retrieve data from both the IMDb's web server, or a local copy
  of the database

- simple and complete API

- released under the terms of the GPL 2 license

IMDbPY powers many other software and has been used in various research papers.
`Curious about that`_?


Installation
------------

Whenever possible, please use the latest version from the repository::

   pip install git+https://github.com/alberanid/imdbpy


But if you want, you can also install the latest release from PyPI::

   pip install imdbpy


Example
-------

Here's an example that demonstrates how to use IMDbPY:

.. code-block:: python

   from imdb import IMDb

   # create an instance of the IMDb class
   ia = IMDb()

   # get a movie
   movie = ia.get_movie('0133093')

   # print the names of the directors of the movie
   print('Directors:')
   for director in movie['directors']:
       print(director['name'])

   # print the genres of the movie
   print('Genres:')
   for genre in movie['genres']:
       print(genre)

   # search for a person name
   people = ia.search_person('Mel Gibson')
   for person in people:
      print(person.personID, person['name'])


Getting help
------------

Please refer to the `support`_ page on the `project homepage`_
and to the the online documentation on `Read The Docs`_.

The sources are available on `GitHub`_.

License
-------

Copyright (C) 2004-2019 Davide Alberani <da --> mimante.net> et al.

IMDbPY is released under the GPL license, version 2 or later.
Read the included `LICENSE.txt`_ file for details.

NOTE: For a list of persons who share the copyright over specific portions of code, see the `CONTRIBUTORS.txt`_ file.

NOTE: See also the recommendations in the `DISCLAIMER.txt`_ file.

.. _IMDb: https://www.imdb.com/
.. _please help with it!: http://imdbpy.readthedocs.io/en/latest/devel/test.html
.. _Curious about that: https://imdbpy.github.io/ecosystem/
.. _project homepage: https://imdbpy.github.io/
.. _support: https://imdbpy.github.io/support/
.. _Read The Docs: https://imdbpy.readthedocs.io/
.. _GitHub: https://github.com/alberanid/imdbpy
.. _LICENSE.txt: https://raw.githubusercontent.com/alberanid/imdbpy/master/LICENSE.txt
.. _CONTRIBUTORS.txt: https://raw.githubusercontent.com/alberanid/imdbpy/master/CONTRIBUTORS.txt
.. _DISCLAIMER.txt: https://raw.githubusercontent.com/alberanid/imdbpy/master/DISCLAIMER.txt
