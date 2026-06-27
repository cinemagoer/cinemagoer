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


**Cinemagoer** (previously known as *IMDbPY*) is a Python package for retrieving and managing IMDb
data about movies, people and companies from IMDb non-commercial downloadable datasets.

This project and its authors are not affiliated in any way to Internet Movie Database Inc.; see the `DISCLAIMER.txt`_ file for details about data licenses.

.. admonition:: Revamp notice
   :class: note

   Starting on April 2026, the scope of this project shifted significantly due to the introduction of a WAF in front of the IMDb website.
   From that day we can no longer guarantee that the package will work as expected with IMDb data (from a technical and legal standpoints),
   and we limited the scope of Cinemagoer to the handling of the dataset that is freely distributed by IMDb.

    If you still need IMDb web-page parsing, see `cinemagoerng`_.
    It is focused on parsing IMDb web pages, but requires you to provide
    the function used to fetch those pages.

   

Main features
-------------

- written in Python 3

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

.. note::

    Cinemagoer reads data from a local database populated from IMDb datasets.
    Before running Python examples:

    1. Download the ``*.tsv.gz`` files from https://datasets.imdbws.com/
       (or run ``download-from-s3``)
    2. Import them with :file:`s32cinemagoer.py`
    3. Open the populated database with Cinemagoer

    SQLite is used in examples for simplicity, but any SQLAlchemy-supported
    database can be used.

.. code-block:: bash

    s32cinemagoer.py /path/to/imdb-tsv-files/ sqlite:///cinemagoer.db

.. code-block:: python

   from imdb import Cinemagoer

    # Open the SQLite database populated with s32cinemagoer.py.
    ia = Cinemagoer('s3', uri='sqlite:///cinemagoer.db')

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

Contribute
------------

Visit the `CONTRIBUTOR_GUIDE.rst`_ to learn how you can contribute to the Cinemagoer package.

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
.. _cinemagoerng: https://github.com/cinemagoer/cinemagoerng
.. _CONTRIBUTOR_GUIDE.rst: https://github.com/ethorne2/cinemagoer/blob/documentation-add-contributor-guide/CONTRIBUTOR_GUIDE.rst
.. _LICENSE.txt: https://raw.githubusercontent.com/cinemagoer/cinemagoer/master/LICENSE.txt
.. _CONTRIBUTORS.txt: https://raw.githubusercontent.com/cinemagoer/cinemagoer/master/CONTRIBUTORS.txt
.. _DISCLAIMER.txt: https://raw.githubusercontent.com/cinemagoer/cinemagoer/master/DISCLAIMER.txt
