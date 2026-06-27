Usage
=====

Here you can find information about how you can use Cinemagoer in your own
programs.

.. important::

   Cinemagoer is dataset-based: before running any example you must download
   IMDb non-commercial datasets, import them with :file:`s32cinemagoer.py`, and
   connect to the populated database. SQLite is used in examples
   (``sqlite:///cinemagoer.db``), but other SQLAlchemy-supported databases are
   supported too. See :ref:`s3`.

.. warning::

   This document is far from complete: the code is the final documentation! ;-)


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   data-interface
   query
   role
   series
   adult
   info2xml
   l10n
   access
   s3
