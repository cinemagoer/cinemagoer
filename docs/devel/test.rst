.. _testing:

How to test
===========

Cinemagoer has a test suite based on `pytest`_. Install the locked development
environment and compile the ignored translation catalogs first::

   uv sync --locked --group dev
   uv run python rebuildmo.py

Then run the suite from the top-level directory::

   uv run pytest

You can execute a specific test module::

   uv run pytest tests/test_in_operator.py

Or execute test functions that match a given keyword::

   uv run pytest -k cover


Base package
------------

The default ``dev`` group includes SQLAlchemy so its adapter tests can run. To
test the base package without SQLAlchemy, install only the test tools::

   uv sync --locked --no-default-groups --group test
   uv run --no-default-groups --group test python rebuildmo.py
   uv run --no-default-groups --group test pytest

This is the dependency mode used by the required Python-version and coverage
CI jobs. SQLAlchemy-specific tests are expected to skip in this environment;
native SQLite behavior and the actionable missing-extra error must pass.


Quality checks
--------------

Run the same required quality environments used by CI with::

   uv run --no-default-groups --group tox tox run -e coverage,style,docs

The individual underlying commands are::

   uv run --no-default-groups --group test pytest --cov --cov-report=term-missing
   uv run --no-default-groups --group style ruff check --preview imdb tests build_support.py rebuildmo.py tools
   uv run --no-default-groups --group doc sphinx-build -W --keep-going -b html docs docs/_build


tox
---

The tox configuration covers Python 3.10 through 3.14, coverage, style, and
documentation. Run every configured environment with::

   uv run --no-default-groups --group tox tox

Run a specific Python or quality environment with::

   uv run --no-default-groups --group tox tox run -e py314
   uv run --no-default-groups --group tox tox run -e style

Additional pytest arguments can be passed after ``--``::

   uv run --no-default-groups --group tox tox run -e py314 -- pytest -k cover


S3 dataset
----------

Tests run against the dataset-backed access system. To test with your own
database generated from IMDb non-commercial datasets, define the
``CINEMAGOER_S3_URI`` environment variable::

   CINEMAGOER_S3_URI='sqlite:///cinemagoer.db' \
       uv run --no-default-groups --group test pytest

You can populate this database with :file:`s32cinemagoer.py` before running
the test suite.


.. _pytest: https://pytest.org/
