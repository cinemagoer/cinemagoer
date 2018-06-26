.. _testing:

How to test
===========

IMDbPY has a test suite based on `pytest`_. The simplest way to run the tests
is to run the following command in the top level directory of the project::

   pytest

You can execute a specific test module::

   pytest tests/test_http_movie_combined.py

Or execute test functions that match a given keyword::

   pytest -k cover


make
----

A :file:`Makefile` is provided for easier invocation of jobs.
The following targets are defined (among others, run "make" to see
the full list):

test
   Run tests quickly with the default Python.

lint
   Check style with flake8.

docs
   Generate Sphinx HTML documentation, including API docs.

coverage
   Check code coverage quickly with the default Python.

clean
   Clean everything.


tox
---

Multiple test environments can be tested using tox::

   tox

This will test all the environments listed in the :file:`tox.ini` file.
If you want to run all tests for a specific environment, for example python 3.4,
supply it as an argument to tox::

   tox -e py34

You can supply commands that will be executed in the given environment.
For example, to run the test function that have the string "cover" in them
using pypy3, execute::

   tox -e pypy3 -- pytest -k cover

Or to get a Python prompt under Python 3.5 (with IMDbPY and all dependencies
already installed), execute::

   tox -e py35 -- python


S3 dataset
----------

The tests will use the HTTP access system by default. If you would also like
to test the database generated from the S3 dataset, define the ``IMDBPY_S3_URI``
environment variable::

   IMDBPY_S3_URI='postgres://imdb@localhost/imdb' pytest

This will run the tests for both HTTP and S3 access systems.


.. _pytest: https://pytest.org/
