Credits
=======

See also the `Contributors`_ document for a list of the major developers
who share the copyright on some portions of the code.

First of all, I want to thank all the package maintainers, and especially
Ana Guerrero. Another big thanks to the developers who used IMDbPY
for their projects and research; they can be found here:
https://imdbpy.sourceforge.io/ecosystem.html

Other very special thanks go to some people who followed the development
of IMDbPY very closely, providing hints and insights: Ori Cohen, James Rubino,
Tero Saarni, and Jesper Noer (for a lot of help, and also for the wonderful
https://bitbucket.org/); and let's not forget all the translators
on https://www.transifex.com/davide_alberani/imdbpy/.

Below is a list of people who contributed with bug reports, small patches,
and hints (kept in reverse order since IMDbPY 4.5):

* Adrien C. and Markus-at-GitHub for improvements to full-size covers

* Tim Belcher for a report about forgotten debug code.

* Paul Jensen for many bug reports about tv series.

* Andrew D Bate for documentation on how to reintroduce foreign keys.

* yiqingzhu007 for a bug report about synopsis.

* David Runge for managing the Arch Linux package.

* enriqueav for fixes after the IMDb redesign.

* Piotr Staszewski for a fix for external sites parser.

* Mike Christopher for the user reviews parser.

* apelord for a parser for full credits.

* Mike Christopher for a patch for synopsis parser.

* Damon Brodie for a bug report about technical parser.

* Sam Petulla for a bug report about searching for keywords.

* zoomorph for an improvement for parsing your own votes.

* Fabrice Laporte for a bug report on setup.py.

* Wael Sinno for a patch for parsing movie-links.

* Tool Man, for a fix on sound track parsing.

* Rafael Lopez for a series of fixes on top/bottom lists.

* Derek Duoba for a bug report about XML output.

* Cody Hatfield for a parser for the Persons's resume page.

* Mystfit for a fix handling company names.

* Troy Deck for a path for MySQL.

* miles82 for a patch on metascore parsing.

* Albert Claret for the parser of the critic reviews page.

* Shobhit Singhal for fixes in parsing biographies and plots.

* Dan Poirier for documentation improvements.

* Frank Braam for a fix for MSSQL.

* Darshana Umakanth for a bug report the search functions.

* Osman Boyaci for a bug report on movie quotes.

* Mikko Matilainen for a patch on encodings.

* Roy Stead for the download_applydiffs.py script.

* Matt Keenan for a report about i18n in search results.

* belgabor for a patch in the goofs parser.

* Ian Havelock for a bug report on charset identification.

* Mikael Puhakka for a bug report about foreign language results in a search.

* Wu Mao for a bug report on the GAE environment.

* legrostdg for a bug report on the new search pages.

* Haukur Páll Hallvarðsson for a patch on query parameters.

* Arthur de Peretti-Schlomoff for a list of French articles and
  fixes to Spanish articles.

* John Lambert, Rick Summerhill and Maciej for reports and fixes
  for the search query.

* Kaspars "Darklow" Sprogis for an impressive amount of tests and reports about
  bugs parsing the plain text data files and many new ideas.

* Damien Stewart for many bug reports about the Windows environment.

* Vincenzo Ampolo for a bug report about the new imdbIDs save/restore queries.

* Tomáš Hnyk for the idea of an option to reraise caught exceptions.

* Emmanuel Tabard for ideas, code and testing on restoring imdbIDs.

* Fabian Roth for a bug report about the new style of episodes list.

* Y. Josuin for a bug report on missing info in crazy credits file.

* Arfrever Frehtes Taifersar Arahesis for a patch for locales.

* Gustaf Nilsson for bug reports about BeautifulSoup.

* Jernej Kos for patches to handle "in production" information
  and birth/death years.

* Saravanan Thirumuruganathan for a bug report about genres in mobile.

* Paul Koan, for a bug report about DVD pages and movie references.

* Greg Walters for a report about a bug with queries with too
  many results.

* Olav Kolbu for tests and report about how the IMDb.com servers
  reply to queries made with and without cookies.

* Jef "ofthelit", for a patch for the reduce.sh script bug
  reports for Windows.

* Reiner Herrmann for benchmarks using SSD hard drives.

* Thomas Stewart for some tests and reports about a bug
  with charset in the plain text data files.

* Ju-Hee Bae for an important series of bug reports about
  the problems derived by the last IMDb's redesign.

* Luis Liras and Petite Abeille for a report and a bugfix about
  imdbpy2sql.py used with SQLite and SQLObject.

* Kevin S. Anthony for a bug report about episodes list.

* Bhupinder Singh for a bug report about exception handling in Python 2.4.

* Ronald Hatcher for a bug report on the GAE environment.

* Ramusus for a lot of precious bug reports.

* Laurent Vergne for a hint about InnoDB, MyISAM and foreign keys.

* Israel Fruch for patches to support the new set of parsers.

* Inf3cted MonkeY, for a bug report about 'vote details'.

* Alexmipego, for suggesting to add a md5sum to titles and names.

* belgabortm for a bug report about movies with multiple 'countries'.

* David Kaufman for an idea to make the 'update' method more robust.

* Dustin Wyatt for a bug with SQLite of Python 2.6.

* Julian Scheid for bug reports about garbage in the ptdf.

* Adeodato Simó for a bug report about the new imdb.com layout.

* Josh Harding for a bug report about the new imdb.com layout.

* Xavier Naidoo for a bug report about top250 and BeautifulSoup.

* Basil Shubin for hints about a new helper function.

* Mark Jeffery, for some help debugging a lxml bug.

* Hieu Nguyen for a bug report about fetching real imdbIDs.

* Rdian06 for a patch for movies without plot authors.

* Tero Saarni, for the series 60 GUI and a lot of testing and
  debugging.

* Ana Guerrero, for maintaining the official debian package.

* H. Turgut Uyar for a number of bug reports and a lot of work on
  the test-suite.

* Ori Cohen for some code and various hints.

* Jesper Nøhr for a lot of testing, especially on 'sql'.

* James Rubino for many bug reports.

* Cesare Lasorella for a bug report about newer versions of SQLObject.

* Andre LeBlanc for a bug report about airing date of tv series episodes.

* aow for a note about some misleading descriptions.

* Sébastien Ragons for tests and reports.

* Sridhar Ratnakumar for info about PKG-INF.

* neonrush for a bug parsing Malcolm McDowell filmography!

* Alen Ribic for some bug reports and hints.

* Joachim Selke for some bug reports with SQLAlchemy and DB2 and a lot
  of testing and debugging of the ibm_db driver (plus a lot of hints
  about how to improve the imdbpy2sql.py script).

* Karl Newman for bug reports about the installer of version 4.5.

* Saruke Kun and Treas0n for bug reports about 'Forbidden' errors
  from the imdb.com server.

* Chris Thompson for some bug reports about summary() methods.

* Mike Castle for performace tests with SQLite and numerous hints.

* Indy (indyx) for a bug about series cast parsing using BeautifulSoup.

* Yoav Aviram for a bug report about tv mini-series.

* Arjan Gijsberts for a bug report and patch for a problem with
  movies listed in the Bottom 100.

* Helio MC Pereira for a bug report about unicode.

* Michael Charclo for some bug reports performing 'http' queries.

* Amit Belani for bug reports about plot outline and other changes.

* Matt Warnock for some tests with MySQL.

* Mark Armendariz for a bug report about too long field in MySQL db
  and some tests/analyses.

* Alexy Khrabrov, for a report about a subtle bug in imdbpy2sql.py.

* Clark Bassett for bug reports and fixes about the imdbpy2sql.py
  script and the cutils.c C module.

* mumas for reporting a bug in summary methods.

* Ken R. Garland for a bug report about 'cover url' and a lot of
  other hints.

* Steven Ovits for hints and tests with Microsoft SQL Server, SQLExpress
  and preliminary work on supporting diff files.

* Fredrik Arnell for tests and bug reports about the imdbpy2sql.py script.

* Arnab for a bug report in the imdbpy2sql.py script.

* Elefterios Stamatogiannakis for the hint about transactions and SQLite,
  to obtain an impressive improvement in performances.

* Jon Sabo for a bug report about unicode and the imdbpy2sql.py script
  and some feedback.

* Andrew Pendleton for a report about a very hideous bug in
  the imdbpy2sql.py (garbage in the plain text data files + programming
  errors + utf8 strings + postgres).

* Ataru Moroboshi ;-) for a bug report about role/duty and notes.

* Ivan Kedrin for a bug report about the analyze_title function.

* Hadley Rich for reporting bugs and providing patches for troubles
  parsing tv series' episodes and searching for tv series' titles.

* Jamie R. Rytlewski for a suggestion about saving imbIDs in 'sql'.

* Vincent Crevot, for a bug report about unicode support.

* Jay Klein for a bug report and testing to fix a nasty bug in the
  imdbpy2sql.py script (splitting too large data sets).

* Ivan Garcia for an important bug report about the use of IMDbPY
  within wxPython programs.

* Kessia Pinheiro for a bug report about tv series list of episodes.

* Michael G. Noll for a bug report and a patch to fix a bug
  retrieving 'plot keywords'.

* Alain Michel, for a bug report about search_*.py and get_*.py scripts.

* Martin Arpon and Andreas Schoenle for bug reports (and patches)
  about "runtime", "aka titles" and "production notes" information
  not being parsed.

* none none (dclist at gmail.com) for a useful hint and code to
  retrieve a movie/person object, given an URL.

* Sebastian Pölsterl, for a bug report about the cover url for
  tv (mini) series, and another one about search_* methods.

* Martin Kirst for many hints and the work on the imdbpyweb program.

* Julian Mayer, for a bug report and a patch about non-ascii chars.

* Wim Schut and "eccentric", for bug reports and a patches about
  movies' cover url.

* Alfio Ferrara, for a bug report about the get_first_movie.py script.

* Magnus Lie Hetland for an hint about the searches in sql package.

* Thomas Jadjewski for a bug report about the imdbpy2sql.py script.

* Trevor MacPhail, for a bug report about search_* methods and
  the ParserBase.parse method.

* Guillaume Wisniewski, for a bug report.

* Kent Johnson, for a bug report.

* Andras Bali, for the hint about the "plot outline" information.

* Nick S. Novikov, who provided the Windows installer until I've
  managed to set up a Windows development environment.

* Simone Bacciglieri, who downloaded the plain text data files for me.

* Carmine Noviello, for some design hints.

* "Basilius" for a bug report.

* Davide for a bug report.


.. _Contributors: CONTRIBUTORS.html
