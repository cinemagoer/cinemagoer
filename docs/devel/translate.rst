.. _translate:

How to translate
----------------

.. note::

   You can (but you don't have to) use Transifex to manage/coordinate
   your translations: http://www.transifex.net/projects/p/imdbpy/

The :mod:`imdb.locale` package contains some scripts that are useful
for building your own internationalization files:

- The :file:`generatepot.py` script should be used only when the DTD
  is changed; it's used to create the :file:`imdbpy.pot` file
  (the one that gets shipped is always up-to-date).

- You can copy the :file:`imdbpy.pot` file as your language's ``.po`` file
  (for example :file:`imdbpy-fr.po` for French) and modify it according
  to your language.

- Then you have to run the :file:`rebuildmo.py` script (which is automatically
  executed at install time) to create the ``.mo`` files.

If you need to upgrade an existing translation, after changes to the ``.pot``
file (usually because the DTD was changed), you can use the ``msgmerge``
utility which is part of the GNU gettext suite::

  msgmerge -N imdbpy-fr.po imdbpy.pot > new-imdbpy-fr.po

If you create a new translation or update an existing one, you can send
it to the <imdbpy-devel@lists.sourceforge.net> mailing list, for inclusion
in upcoming releases.
