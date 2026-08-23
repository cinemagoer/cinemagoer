.. _translate:

How to translate
----------------

.. note::

   You can (but you don't have to) use Transifex to manage/coordinate
   your translations: https://app.transifex.com/davide_alberani/cinemagoer

The :mod:`imdb.locale` package contains some scripts that are useful
for building your own internationalization files:

- The :file:`generatepot.py` script should be used only when the DTD
  is changed; it's used to create the :file:`imdbpy.pot` file
  (the one that gets shipped is always up-to-date).

- You can copy the :file:`imdbpy.pot` file as your language's ``.po`` file
  (for example :file:`imdbpy-fr.po` for French) and modify it according
  to your language.

- Run the :file:`rebuildmo.py` script to test the translation from a source
  checkout. PEP 517 builds compile all catalogs automatically into the wheel,
  so generated ``.mo`` files are not committed.

If you need to upgrade an existing translation, after changes to the ``.pot``
file (usually because the DTD was changed), you can use the ``msgmerge``
utility which is part of the GNU gettext suite::

  msgmerge -N imdbpy-fr.po imdbpy.pot > new-imdbpy-fr.po

If you create a new translation or update an existing one, you can send
it to the GitHub discussion page for inclusion in the upcoming releases: https://github.com/cinemagoer/cinemagoer/discussions .
