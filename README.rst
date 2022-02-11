|pypi| |pyversions| |license|

.. |pypi| image:: https://img.shields.io/pypi/v/cinemagoer.svg?style=flat-square
    :target: https://pypi.org/project/cinemagoer/
    :alt: PyPI version.

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/cinemagoer.svg?style=flat-square
    :target: https://pypi.org/project/cinemagoer/
    :alt: Supported Python versions.

.. |license| image:: https://img.shields.io/pypi/l/cinemagoer.svg?style=flat-square
    :target: https://github.com/cinemagoer/cinemagoer/blob/master/LICENSE.txt
    :alt: Project license.


**Cinemagoer** (previously known as *IMDbPY*) is a Python package for retrieving and managing the data
of the `IMDb`_ movie database about movies, people and companies.

This project and its authors are not affiliated in any way to Internet Movie Database Inc.; see the `DISCLAIMER.txt`_ file for details about data licenses.

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

- simple and complete API

- released under the terms of the GPL 2 license

Cinemagoer powers many other software and has been used in various research papers.
`Curious about that`_?


Installation
------------

Whenever possible, please use the latest version from the repository::

   pip install git+https://github.com/cinemagoer/cinemagoer


But if you want, you can also install the latest release from PyPI::

   pip install cinemagoer


Example
-------

Here's an example that demonstrates how to use Cinemagoer:

.. code-block:: python

   from imdb import Cinemagoer

   # create an instance of the IMDb class
   ia = Cinemagoer()

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

Copyright (C) 2004-2022 Davide Alberani <da --> mimante.net> et al.

Cinemagoer is released under the GPL license, version 2 or later.
Read the included `LICENSE.txt`_ file for details.

NOTE: For a list of persons who share the copyright over specific portions of code, see the `CONTRIBUTORS.txt`_ file.

NOTE: See also the recommendations in the `DISCLAIMER.txt`_ file.

.. _IMDb: https://www.imdb.com/
.. _please help with it!: http://cinemagoer.readthedocs.io/en/latest/devel/test.html
.. _Curious about that: https://cinemagoer.github.io/ecosystem/
.. _project homepage: https://cinemagoer.github.io/
.. _support: https://cinemagoer.github.io/support/
.. _Read The Docs: https://cinemagoer.readthedocs.io/
.. _GitHub: https://github.com/cinemagoer/cinemagoer
.. _LICENSE.txt: https://raw.githubusercontent.com/cinemagoer/cinemagoer/master/LICENSE.txt
.. _CONTRIBUTORS.txt: https://raw.githubusercontent.com/cinemagoer/cinemagoer/master/CONTRIBUTORS.txt
.. _DISCLAIMER.txt: https://raw.githubusercontent.com/cinemagoer/cinemagoer/master/DISCLAIMER.txt
