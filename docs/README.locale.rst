Localization
============

Since version 4.1 it's easy to translate the labels that describe
sets of information.


Limitation
----------

So far no internal message or exception is translated, the internationalization
is limited to the "tags" returned by the ``getAsXML`` and ``asXML`` methods
of the Movie, Person, Character, or Company classes.  Beware that in many cases
these "tags" are not the same as the "keys" used to access information
in the same classes, as if they are dictionaries.

E.g.: you can translate "long-imdb-name" -the tag returned by the call
``person.getAsXML('long imdb name')``- but not "long imdb name" directly.
To translate keys, you can use the ``helpers.translateKey`` function in
the 'helpers' module.


Usage
-----

If you want to add i18n to your IMDbPY-based application, all you need
to do is to switch to the 'imdbpy' text domain:

.. code-block:: python

   import imdb.locale

   # Standard gettext stuff.
   import gettext
   from gettext import gettext as _

   # Switch to the imdbpy domain.
   gettext.textdomain('imdbpy')

   # Request a translation.
   print(_(u'long-imdb-name'))


Adding a new language
---------------------

You can (but you're not forced to) use Transifex to manage/coordinate
your translations; see: http://www.transifex.net/projects/p/imdbpy/c/default/
Below are the generic instruction about how translation works.

In the ``imdb.locale`` package, you'll find some scripts useful to build
your own internationalization files.

If you create a new translation or update an existing one, you can send
it to the <imdbpy-devel@lists.sourceforge.net> mailing list, for
inclusion in the next releases.

- The generatepot.py script should be used only when the DTD is changed;
  it's used to create the imdbpy.pot file (the one shipped is always
  up-to-date).

- You can copy the imdbpy.pot file to your language's .po file (e.g.
  imdbpy-fr.po for French) and modify it accordingly to your needs.

- Then you must run rebuildmo.py (which is automatically called
  at install time, by the setup.py script) to create the .mo files.

If you need to upgrade an existing .po file, after changes to the .pot
file (usually because the DTD was changed), you can use the msgmerge
tool, part of the GNU gettext suite::

  msgmerge -N imdbpy-fr.po imdbpy.pot > new-imdbpy-fr.po


Articles in titles
------------------

Converting a title to its 'Title, The' canonical format, IMDbPY does
some assumptions about what is an article and what not, and this could
lead to some wrong canonical titles.  E.g.: "Hard, Die" instead of
"Die Hard", since 'Die' is guessed as an article (and it is, in Germany...)
To solve this problem, there are other keys: "smart canonical title",
"smart long imdb canonical title", "smart canonical series title",
"smart canonical episode title" which can be used to do a better job
converting a title into its canonical format.

It works, but it needs to know something about articles in various
languages: if you want to help, see the LANG_ARTICLES and LANG_COUNTRIES
dictionaries in the 'linguistics' module.

To know what the language in which a movie title is assumed to be,
call its 'guessLanguage' method (it will return None, if unable to guess).
If you want to force a given language instead of the guessed one, you
can call its 'smartCanonicalTitle' method, setting the 'lang' argument
appropriately.


Alternative titles
------------------

Sometimes it's useful to manage a title's alternatives (AKAs) knowing
their languages. In the 'helpers' module there are some (hopefully)
useful functions:

- ``akasLanguages(movie)`` - Given a movie, return a list of tuples
  in (lang, AKA) format (lang can be None, if unable to detect).

- ``sortAKAsBySimilarity(movie, title)`` - Sort the AKAs on a movie considering
  how much they are similar to a given title (see the code for more options).

- ``getAKAsInLanguage(movie, lang)`` - Return a list of AKAs of the movie
  in the given language (see the code for more options).
