Changelog
=========

* What's new in release 6.5

  [general]

  - converted the documentation to Sphinx rst format

  [http]

  - fix title parser for in-production movies
  - parsers are based on piculet
  - improve collection of full-size cover images


* What's new in release 6.4 "Electric Dreams" (14 Mar 2018)

  [http]

  - remove obsolete parsers
  - remove Character objects
  - fix for search parsers


* What's new in release 6.3 "Altered Carbon" (27 Feb 2018)

  [general]

  - documentation updates
  - introduced the 'imdbpy' CLI
  - s3 accessSystem to access the new dataset from IMDb

  [http]

  - fixes for IMDb site redesign
  - Person parser fixes
  - users review parser
  - improve external sites parser
  - switch from akas.imdb.com domain to www.imdb.com
  - fix for synopsis
  - fix for tv series episodes

  [s3]

  - ability to import and access all the information


* What's new in release 6.2 "Justice League" (19 Nov 2017)

  [general]

  - introduce check for Python version
  - SQLAlchemy can be disabled using --without-sqlalchemy
  - fix #88: configuration file parser
  - update documentation

  [http]

  - fixed ratings parser
  - moved cookies from json to Python source


* What's new in release 6.1

  - skipped version 6.1 due to a wrong release on pypi


* What's new in release 6.0 "Life is Strange" (12 Nov 2017)

  [general]

  - now IMDbPY is a Python 3 package
  - simplified the code base: #61
  - remove dependencies: SQLObject, BeautifulSoup, C compiler
  - introduced a tox testsuite
  - fix various parsers


* What's new in release 5.1 "Westworld" (13 Nov 2016)

  [general]

  - fix for company names containing square brackets.
  - fix XML output when imdb long name is missing.
  - fixes #33: unable to use --without-sql

  [http]

  - fix birth/death dates parsing.
  - fix top/bottom lists.
  - Persons's resume page parser (courtesy of codynhat)
  - fixes #29: split color info
  - parser for "my rating" (you have to use your own cookies)

  [sql]

  - sound track list correctly identified.
  - fixes #50: process splitted data in order
  - fixes #53: parser for movie-links


* What's new in release 5.0 "House of Cards" (02 May 2014)

  [general]

  - Spanish, French, Arabic, Bulgarian and German translations.
  - Introduced the list of French articles.
  - fix for GAE.
  - download_applydiffs.py script.
  - fixed wrong handling of encoding in episode titles
  - renamed README.utf8 to README.unicode

  [http]

  - fixed searches (again).
  - search results are always in English.
  - updated the cookies.
  - support for obtaining metacritic score and URL.
  - fixed goofs parser.
  - fixed url for top250.
  - fixes for biography page.
  - fix for quotes.
  - better charset identification.
  - category and spoiler status for goofs.
  - changed query separators from ; to &.
  - fix for episodes of unknown seasons.
  - new cookie.

  [mobile]

  - fixed searches.

  [sql]

  - fix for MSSQL


* What's new in release 4.9 "Iron Sky" (15 Jun 2012)

  [general]

  - urls used to access the IMDb site can be configured.
  - helpers function to handle movie AKAs in various
    languages (code by Alberto Malagoli).
  - renamed the 'articles' module into 'linguistics'.
  - introduced the 'reraiseExceptions' option, to re-raise
    evey caught exception.

  [http]

  - fix for changed search parameters.
  - introduced a 'timeout' parameter for connections to the web server.
  - fix for business information.
  - parser for the new style of episodes list.
  - unicode searches handled as iso8859-1.
  - fix for garbage in AKA titles.

  [sql]

  - vastly improved the store/restore of imdbIDs; now it should be faster
    and more accurate.
  - now the 'name' table contains a 'gender' field that can be 'm', 'f' or NULL.
  - fix for nicknames.
  - fix for missing titles in the crazy credits file.
  - handled exceptions creating indexes, foreign keys and
    executing custom queries.
  - fixed creation on index for keywords.
  - excluded {{SUSPENDED}} titles.


* What's new in release 4.8.2 "The Big Bang Theory" (02 Nov 2011)

  [general]

  - fixed install path of locales.

  [http]

  - removed debug code.


* What's new in release 4.8 "Super" (01 Nov 2011)

  [general]

  - fix for a problem managing exceptions with Python 2.4.
  - converted old-style exceptions to instances.
  - enanchements for the reduce.sh script.
  - added notes about problems connecting to IMDb's web servers.
  - improvements in the parsers of movie titles.
  - improvements in the parser of person names.

  [http]

  - potential fix for GAE environment.
  - handled the new style of "in production" information.
  - fix for 'episodes' list.
  - fix for 'episodes rating'.
  - fix for queries that returned too many results.
  - fix for wrong/missing references.
  - removed no more available information set "amazon
    reviews" and "dvd".
  - fix for cast of tv series.
  - fix for title of tv series.
  - now the beautiful parses work again.

  [httpThin]

  - removed "httpThin", falling back to "http".

  [mobile]

  - fix for missing headshots.
  - fix for rating and number of votes.
  - fix for missing genres.
  - many other fixes to keep up-to-date with the IMDb site.

  [sql]

  - fix for a nasty bug parsing notes about character names.
  - fixes for SQLite with SQLOjbect.


* What's new in release 4.7 "Saw VI" (23 Jan 2011)

  [http]

  - first fixes for the new set of parsers.
  - first changes to support the new set of web pages.
  - fix for lists of uncategorized episodes.
  - fix for movies with multiple countries.
  - fix for the currentRole property.
  - more robust handling for vote details.

  [mobile]

  - first fixes for the new set of parsers.

  [sql]

  - the tables containing titles and names (and akas) now
    include a 'md5sum' column calculated on the "long imdb canonical title/name".


* What's new in release 4.6 "The Road" (19 Jun 2010)

  [general]

  - introduced the 'full-size cover url' and 'full-size headshot'
    keys for Movie, Person and Character instances.
  - moved the development to a Mercurial repository.
  - introduced the parseXML function in the imdb.helpers module.
  - now the asXML method can exclude dynamically generated keys.
  - rationalized the use of the 'logging' and 'warnings' modules.
  - the 'update' method no longer raises an exception, if asked for
    an unknown info set.

  [http/mobile]

  - removed new garbage from the imdb pages.
  - support new style of akas.
  - fix for the "trivia" page.
  - fixes for searches with too many results.

  [sql]

  - fixes for garbage in the plain text data files.
  - support for SQLite shipped with Python 2.6.


* What's new in release 4.5.1 "Dollhouse" (01 Mar 2010)

  [general]

  - reintroduced the ez_setup.py file.
  - fixes for AKAs on 'release dates'.
  - added the dtd.


* What's new in release 4.5 "Invictus" (28 Feb 2010)

  [general]

  - moved to setuptools 0.6c11.
  - trying to make the SVN release versions work fine.
  - http/mobile should work in GAE (Google App Engine).
  - added some goodies scripts, useful for programmers (see the
    docs/goodies directory).

  [http/mobile]

  - removed urllib-based User-Agent header.
  - fixes for some minor changes to IMDb's html.
  - fixes for garbage in movie quotes.
  - improvements in the handling of AKAs.

  [mobile]

  - fixes for AKAs in search results.

  [sql]

  - fixes for bugs restoring imdbIDs.
  - first steps to split CSV creation/insertion.


* What's new in release 4.4 "Gandhi" (06 Jan 2010)

  [general]

  - introduced a logging facility; see README.logging.
  - the 'http' and 'mobile' should be a lot more robust.

  [http]

  - fixes for the n-th set of changes to IMDb's HTML.
  - improvements to perfect-match searches.
  - slightly simplified the parsers for search results.

  [mobile]

  - fixes for the n-th set of changes to IMDb's HTML.
  - slightly simplified the parsers for search results.

  [sql]

  - movies' keywords are now correctly imported, using CSV files.
  - minor fixes to handle crap in the plain text data files.
  - removed an outdate parameter passed to SQLObject.
  - made imdbpy2sql.py more robust in some corner-cases.
  - fixes for the Windows environment.


* What's new in release 4.3 "Public Enemies" (18 Nov 2009)

  [general]

  - the installer now takes care of .mo files.
  - introduced, in the helpers module, the functions keyToXML and
    translateKey, useful to translate dictionary keys.
  - support for smart guessing of the language of a movie title.
  - updated the DTD.

  [http]

  - fixed a lot of bugs introduced by the new IMDb.com design.
  - nicer handling of HTTP 404 response code.
  - fixed parsers for top250 and bottom100 lists.
  - fixed a bug parsing AKAs.
  - fixed misc bugs.

  [mobile]

  - removed duplicates in list of genres.

  [sql]

  - fixed a bug in the imdbpy2sql.py script using CSV files;
    the 'movie_info_idx' and 'movie_keyword' were left
    empty/with wrong data.


* What's new in release 4.2 "Battlestar Galactica" (31 Aug 2009)

  [general]

  - the 'local' data access system is gone.  See README.local.
  - the imdb.parser.common package was removed, and its code integrated
    in imdb.parser.sql and in the imdbpy2sql.py script.
  - fixes for the installer.
  - the helpers module contains the fullSizeCoverURL function, to convert
    a Movie, Person or Character instance (or a URL in a string)
    in an URL to the full-size version of its cover/headshot.
    Courtesy of Basil Shubin.
  - used a newer version of msgfmt.py, to work around a hideous bug
    generating locales.
  - minor updates to locales.
  - updated the DTD to version 4.2.

  [http]

  - removed garbage at the end of quotes.
  - fixed problems parsing company names and notes.
  - keys in character's quotes dictionary are now Movie instances.
  - fixed a bug converting entities char references (affected BeautifulSoup).
  - fixed a long-standing bug handling &amp; with BeautifulSoup.
  - top250 is now correctly parsed by BeautifulSoup.

  [sql]

  - fixed DB2 call for loading blobs/cblobs.
  - information from obsolete files are now used if and only if they
    refer to still existing titles.
  - the --fix-old-style-titles argument is now obsolete.


* What's new in release 4.1 "State Of Play" (02 May 2009)

  [general]

  - DTD definition.
  - support for locale.
  - support for the new style for movie titles ("The Title" and no
    more "Title, The" is internally used).
  - minor fix to XML code to work with the test-suite.

  [http]

  - char references in the &#xHEXCODE; format are handled.
  - fixed a bug with movies containing '....' in titles.  And I'm
    talking about Malcolm McDowell's filmography!
  - 'airing' contains object (so the accessSystem variable is set).
  - 'tv schedule' ('airing') pages of episodes can be parsed.
  - 'tv schedule' is now a valid alias for 'airing'.
  - minor fixes for empty/wrong strings.

  [sql]

  - in the database, soundex values for titles are always calculated
    after the article is stripped (if any).
  - imdbpy2sql.py has the --fix-old-style-titles option, to handle
    files in the old format.
  - fixed a bug saving imdbIDs.

  [local]

  - the 'local' data access system should be considered obsolete, and
    will probably be removed in the next release.


* What's new in release 4.0 "Watchmen" (12 Mar 2009)

  [general]

  - the installer is now based on setuptools.
  - new functions get_keyword and search_keyword to handle movie's keywords
    (example scripts included).
  - Movie/Person/... keys (and whole instances) can be converted to XML.
  - two new functions, get_top250_movies and get_bottom100_movies, to
    retrieve lists of best/worst movies (example scripts included).
  - searching for movies and persons - if present - the 'akas' keyword
    is filled, in the results.
  - 'quotes' for movies is now always a list of lists.
  - the old set of parsers (based on sgmllib.SGMLParser) are gone.
  - fixed limitations handling multiple roles (with notes).
  - fixed a bug converting somethingIDs to real imdbIDs.
  - fixed some summary methods.
  - updates to the documentation.

  [http]

  - adapted BeautifulSoup to lxml (internally, the lxml API is used).
  - currentRole is no longer populated, for non-cast entries (everything
    ends up into .notes).
  - fixed a bug search for too common terms.
  - fixed a bug identifying 'kind', searching for titles.
  - fixed a bug parsing airing dates.
  - fixed a bug searching for company names (when there's a direct hit).
  - fixed a bug handling multiple characters.
  - fixed a bug parsing episode ratings.
  - nicer keys for technical details.
  - removed the 'agent' page.

  [sql]

  - searching for a movie, the original titles are returned, instead
    of AKAs.
  - support for Foreign Keys.
  - minor changes to the db's design.
  - fixed a bug populating tables with SQLAlchemy.
  - imdbpy2sql.py shows user time and system time, along with wall time.

  [local]

  - searching for a movie, the original titles are returned, instead
    of AKAs.


* What's new in release 3.9 "The Strangers" (06 Jan 2009)

  [general]

  - introduced the search_episode method, to search for episodes' titles.
  - movie['year'] is now an integer, and no more a string.
  - fixed a bug parsing company names.
  - introduced the helpers.makeTextNotes function, useful to pretty-print
    strings in the 'TEXT::NOTE' format.

  [http]

  - fixed a bug regarding movies listed in the Bottom 100.
  - fixed bugs about tv mini-series.
  - fixed a bug about 'series cast' using BeautifulSoup.

  [sql]

  - fixes for DB2 (with SQLAlchemy).
  - improved support for movies' aka titles (for series).
  - made imdbpy2sql.py more robust, catching exceptions even when huge
    amounts of data are skipped due to errors.
  - introduced CSV support in the imdbpy2sql.py script.


* What's new in release 3.8 "Quattro Carogne a Malopasso" (03 Nov 2008)

  [http]

  - fixed search system for direct hits.
  - fixed IDs so that they always are str and not unicode.
  - fixed a bug about plot without authors.
  - for pages about a single episode of a series, "Series Crew" are
    now separated items.
  - introduced the preprocess_dom method of the DOMParserBase class.
  - handling rowspan for DOMHTMLAwardsParser is no more a special case.
  - first changes to remove old parsers.

  [sql]

  - introduced support for SQLAlchemy.

  [mobile]

  - fixed multiple 'nick names'.
  - added 'aspect ratio'.
  - fixed a "direct hit" bug searching for people.

  [global]

  - fixed search_* example scripts.
  - updated the documentation.


* What's new in release 3.7 "Burn After Reading" (22 Sep 2008)

  [http]

  - introduced a new set of parsers, active by default, based on DOM/XPath.
  - old parsers fixed; 'news', 'genres', 'keywords', 'ratings', 'votes',
    'tech', 'taglines' and 'episodes'.

  [sql]

  - the pure python soundex function now behaves correctly.

  [general]

  - minor updates to the documentation, with an introduction to the
    new set of parsers and notes for packagers.


* What's new in release 3.6 "RahXephon" (08 Jun 2008)

  [general]

  - support for company objects for every data access systems.
  - introduced example scripts for companies.
  - updated the documentation.

  [http and mobile]

  - changes to support the new HTML for "plot outline" and some lists
    of values (languages, genres, ...)
  - introduced the set_cookies method to set cookies for IMDb's account and
    the del_cookies method to remove the use of cookies; in the imdbpy.cfg
    configuration file, options "cookie_id" and "cookie_uu" can be set to
    the appropriate values; if "cookie_id" is None, no cookies are sent.
  - fixed parser for 'news' pages.
  - fixed minor bug fetching movie/person/character references.

  [http]

  - fixed a search problem, while not using the IMDbPYweb's account.
  - fixed bugs searching for characters.

  [mobile]

  - fixed minor bugs parsing search results.

  [sql]

  - fixed a bug handling movieIDs, when there are some
    inconsistencies in the plain text data files.

  [local]

  - access to 'mpaa' and 'miscellaneous companies' information.


* What's new in release 3.5 "Blade Runner" (19 Apr 2008)

  [general]

  - first changes to work on Symbian mobile phones.
  - now there is an imdb.available_access_systems() function, that can
    be used to get a list of available data access systems.
  - it's possible to pass 'results' as a parameter of the imdb.IMDb
    function; it sets the number of results to return for queries.
  - fixed summary() method in Movie and Person, to correctly handle
    unicode chars.
  - the helpers.makeObject2Txt function now supports recursion over
    dictionaries.
  - cutils.c MXLINELEN increased from 512 to 1024; some critical
    strcpy replaced with strncpy.
  - fixed configuration parser to be compatible with Python 2.2.
  - updated list of articles and some stats in the comments.
  - documentation updated.

  [sql]

  - fixed minor bugs in imdbpy2sql.py.
  - restores imdbIDs for characters.
  - now CharactersCache honors custom queries.
  - the imdbpy2sql.py's --mysql-force-myisam command line option can be
    used to force usage of MyISAM tables on InnoDB databases.
  - added some warnings to the imdbpy2sql.py script.

  [local]

  - fixed a bug in the fall-back function used to scan movie titles,
    when the cutils module is not available.
  - mini biographies are cut up to 2**16-1 chars, to prevent troubles
    with some MySQL servers.
  - fixed bug in characters4local.py, dealing with some garbage in the files.


* What's new in release 3.4 "Flatliners" (16 Dec 2007)

  [general]

  - *** NOTE FOR PACKAGERS *** in the docs directory there is the
    "imdbpy.cfg" configuration file, which should be installed in /etc
    or equivalent directory; the setup.py script *doesn't* manage its
    installation.
  - introduced a global configuration file to set IMDbPY's parameters.
  - supported characters using "sql" and "local" data access systems.
  - fixed a bug retrieving characterID from a character's name.

  [http]

  - fixed a bug in "release dates" parser.
  - fixed bugs in "episodes" parser.
  - fixed bugs reading "series years".
  - stricter definition for ParserBase._re_imdbIDmatch regular expression.

  [mobile]

  - fixed bugs reading "series years".
  - fixed bugs reading characters' filmography.

  [sql]

  - support for characters.

  [local]

  - support for characters.
  - introduced the characters4local.py script.


* What's new in release 3.3 "Heroes" (18 Nov 2007)

  [general]

  - first support for character pages; only for "http" and "mobile", so far.
  - support for multiple characters.
  - introduced an helper function to pretty-print objects.
  - added README.currentRole.
  - fixed minor bug in the __hash__ method of the _Container class.
  - fixed changes to some key names for movies.
  - introduced the search_character.py, get_character.py and
    get_first_character.py example scripts.

  [http]

  - full support for character pages.
  - fixed a bug retrieving some 'cover url'.
  - fixed a bug with multi-paragraphs biographies.
  - parsers are now instanced on demand.
  - accessSystem and modFunct are correctly set for every Movie, Person
    and Character object instanced.

  [mobile]

  - full support for character pages.

  [sql]

  - extended functionality of the custom queries support for the
    imdbpy2sql.py script to circumvent a problem with MS SQLServer.
  - introducted the "--mysql-innodb" and "--ms-sqlserver" shortcuts
    for the imdbpy2sql.py script.
  - introduced the "--sqlite-transactions" shortcut to activate
    transaction using SQLite which, otherwise, would have horrible
    performances.
  - fixed a minor bug with top/bottom ratings, in the imdbpy2sql.py script.

  [local]

  - filtered out some crap in the "quotes" plain text data files, which
    also affected sql, importing the data.


* What's new in release 3.2 "Videodrome" (25 Sep 2007)

  [global]

  - now there's an unique place where "akas.imdb.com" is set, in the
    main module.
  - introduced __version__ and VERSION in the main module.
  - minor improvements to the documentation.

  [http]

  - updated the main movie parser to retrieve the recently modified
    cast section.
  - updated the crazy credits parser.
  - fixed a bug retrieving 'cover url'.

  [mobile]

  - fixed a bug parsing people's filmography when only one duty
    was listed.
  - updated to retrieve series' creator.

  [sql]

  - added the ability to perform custom SQL queries at the command
    line of the imdbpy2sql.py script.
  - minor fixes for the imdbpy2sql.py script.


* What's new in release 3.1 "The Snake King" (18 Jul 2007)

  [global]

  - the IMDbPYweb account now returns a single item, when a search
    returns only one "good enough" match (this is the IMDb's default).
  - updated the documentation.
  - updated list of contributors and developers.

  [http]

  - supported the new result page for searches.
  - supported the 'synopsis' page.
  - supported the 'parents guide' page.
  - fixed a bug retrieving notes about a movie's connections.
  - fixed a bug for python2.2 (s60 mobile phones).
  - fixed a bug with 'Production Notes/Status'.
  - fixed a bug parsing role/duty and notes (also for httpThin).
  - fixed a bug retrieving user ratings.
  - fixed a bug (un)setting the proxy.
  - fixed 2 bugs in movie/person news.
  - fixed a bug in movie faqs.
  - fixed a bug in movie taglines.
  - fixed a bug in movie quotes.
  - fixed a bug in movie title, in "full cast and crew" page.
  - fixed 2 bugs in persons' other works.

  [sql]

  - hypothetical fix for a unicode problem in the imdbpy2sql.py script.
  - now the 'imdbID' fields in the Title and Name tables are restored,
    updating from an older version.
  - fixed a nasty bug handling utf-8 strings in the imdbpy2sql.py script.

  [mobile]

  - supported the new result page for searches.
  - fixed a bug for python2.2 (s60 mobile phones).
  - fixed a bug searching for persons with single match and no
    messages in the board.
  - fixed a bug parsing role/duty and notes.


* What's new in release 3.0 "Spider-Man 3" (03 May 2007)

  [global]

  - IMDbPY now works with the new IMDb's site design; a new account is
    used to access data; this affect a lot of code, especially in the
    'http', 'httpThin' and 'mobile' data access systems.
  - every returned string should now be unicode; dictionary keywords are
    _not_ guaranteed to be unicode (but they are always 7bit strings).
  - fixed a bug in the __contains__ method of the Movie class.
  - fix in the analyze_title() function to handle malformed episode
    numbers.

  [http]

  - introduced the _in_content instance variable for objects instances of
    ParserBase, True when inside the <div id="tn15content"> tag.
    Opening and closing this pair of tags two methods, named _begin_content()
    and _end_content() are called with no parameters (by default, they do
    nothing).
  - in the utils module there's the build_person function, useful to create
    a Person instance from the tipical formats found in the IMDb's web site.
  - an analogue build_movie function can be used to instance Movie objects.
  - inverted the getRefs default - now if not otherwise set, it's False.
  - added a parser for the "merchandising" ("for sale") page for persons.
  - the 'rating' parser now collects also 'rating' and 'votes' data.
  - the HTMLMovieParser class (for movies) was rewritten from zero.
  - the HTMLMaindetailsParser class (for persons) was rewritten from zero.
  - unified the "episode list" and "episodes cast" parsers.
  - fixed a bug parsing locations, which resulted in missing information.
  - locations_parser splitted from "tech" parser.
  - "connections" parser now handles the recently introduced notes.

  [http parser conversion]

  - these parsers worked out-of-the-box; airing, eprating, alternateversions,
    dvd, goofs, keywords, movie_awards, movie_faqs, person_awards, rec,
    releasedates, search_movie, search_person, soundclips, soundtrack, trivia,
    videoclips.
  - these parsers were fixed; amazonrev, connections, episodes, crazycredits,
    externalrev, misclinks, newsgrouprev, news, officialsites, otherworks,
    photosites, plot, quotes, ratings, sales, taglines, tech, business,
    literature, publicity, trivia, videoclips, maindetails, movie.

  [mobile]

  - fixed to work with the new design.
  - a lot of code is now shared amongst 'http' and 'mobile'.

  [sql]

  - fixes for other bugs related to unicode support.
  - minor changes to slightly improve performances.


* What's new in release 2.9 "Rodan! The Flying Monster" (21 Feb 2007)

  [global]

  - on 19 February IMDb has redesigned its site; this is the last
    IMDbPY's release to parse the "old layout" pages; from now on,
    the development will be geared to support the new web pages.
    See the README.redesign file for more information.
  - minor clean-ups and functions added to the helpers module.

  [http]

  - fixed some unicode-related problems searching for movie titles and
    person names; also changed the queries used to search titles/names.
  - fixed a bug parsing episodes for tv series.
  - fixed a bug retrieving movieID for tv series, searching for titles.

  [mobile]

  - fixed a problem searching exact matches (movie titles only).
  - fixed a bug with cast entries, after minor changes to the IMDb's
    web site HTML.

  [local and sql]

  - fixed a bug parsing birth/death dates and notes.

  [sql]

  - (maybe) fixed another unicode-related bug fetching data from a
    MySQL database.  Maybe.  Maybe.  Maybe.


* What's new in release 2.8 "Apollo 13" (14 Dec 2006)

  [general]

  - fix for environments where sys.stdin was overridden by a custom object.

  [http data access system]

  - added support for the movies' "FAQ" page.
  - now the "full credits" (aka "full cast and crew") page can be parsed;
    it's mostly useful for tv series, because this page is complete while
    "combined details" contains only partial data.
    E.g.

        ia.update(tvSeries, 'full credits')

  - added support for the movies' "on television" (ia.update(movie, "airing"))
  - fixed a bug with 'miscellaneous companies'.
  - fixed a bug retrieving the list of episodes for tv series.
  - fixed a bug with tv series episodes' cast.
  - generic fix for XML single tags (unvalid HTML tags) like <br/>
  - fixed a minor bug with 'original air date'.

  [sql data access system]

  - fix for a unicode bug with recent versions of SQLObject and MySQL.
  - fix for a nasty bug in imdbpy2sql.py that will show up splitting a
    data set too large to be sent in a single shot to the database.

  [mobile data access system]

  - fixed a bug searching titles and names, where XML char references
    were not converted.


* What's new in release 2.7 "Pitch Black" (26 Sep 2006)

  [general]

  - fixed search_movie.py and search_person.py scripts; now they return
    both the movieID/personID and the imdbID.
  - the IMDbPY account was configured to hide the mini-headshots.
  - http and mobile data access systems now try to handle queries
    with too many results.

  [http data access system]

  - fixed a minor bug retrieving information about persons, with movies
    in production.
  - fixed support for cast list of tv series.
  - fixed a bug retrieving 'plot keywords'.
  - some left out company credits are now properly handled.

  [mobile data access system]

  - fixed a major bug with the cast list, after the changes to the
    IMDb web site.
  - fixed support for cast list of tv series.
  - fixed a minor bug retrieving information about persons, with movies
    in production.
  - now every AKA title is correctly parsed.

  [sql data access system]

  - fixed a(nother) bug updating imdbID for movies and persons.
  - fixed a bug retrieving personID, while handling names references.

  [local data access system]

  - "where now" information now correctly handles multiple lines (also
    affecting the imdbpy2sql.py script).


* What's new in release 2.6 "They Live" (04 Jul 2006)

  [general]

  - renamed sortMovies to cmpMovies and sortPeople to cmpPeople; these
    function are now used to compare Movie/Person objects.
    The cmpMovies also handles tv series episodes.

  [http data access system]

  - now information about "episodes rating" are retrieved.
  - fixed a bug retrieving runtimes and akas information.
  - fixed an obscure bug trying an Exact Primary Title/Name search when
    the provided title was wrong/incomplete.
  - support for the new format of the "DVD details" page.

  [sql data access system]

  - now at insert-time the tables doesn't have indexes, which are
    added later, resulting in a huge improvement of the performances
    of the imdbpy2sql.py script.
  - searching for tv series episodes now works.
  - fixed a bug inserting information about top250 and bottom10 films rank.
  - fixed a bug sorting movies in people's filmography.
  - fixed a bug filtering out adult-only movies.
  - removed unused ForeignKeys in the dbschema module.
  - fixed a bug inserting data in databases that require a commit() call,
    after a call to executemany().
  - fixed a bug inserting aka titles in database that checks for foreign
    keys consistency.
  - fixed an obscure bug splitting too huge data sets.
  - MoviesCache and PersonsCache are now flushed few times.
  - fixed a bug handling excessive recursion.
  - improved the exceptions handling.


* What's new in release 2.5 "Ninja Thunderbolt" (15 May 2006)

  [general]

  - support for tv series episodes; see the README.series file.
  - modified the DISCLAIMER.txt file to be compliant to the debian guidelines.
  - fixed a bug in the get_first_movie.py script.
  - Movie and Person instances are now hashable, so that they can be used
    as dictionary keys.
  - modified functions analyze_title and build_title to support tv episodes.
  - use isinstance for type checking.
  - minor updates to the documentation.
  - the imdbID for Movie and Person instances is now searched if either
    one of movieID/personID and title/name is provided.
  - introduced the isSame() method for both Movie and Person classes,
    useful to compare object by movieID/personID and accessSystem.
  - __contains__() methods are now recursive.
  - two new functions in the IMDbBase class, title2imdbID() and name2imdbID()
    are used to get the imdbID, given a movie title or person name.
  - two new functions in the helpers module, sortedSeasons() and
    sortedEpisodes(), useful to manage lists/dictionaries of tv series
    episodes.
  - in the helpers module, the get_byURL() function can be used to retrieve
    a Movie or Person object for the given URL.
  - renamed the "ratober" C module to "cutils".
  - added CONTRIBUTORS.txt file.

  [http data access system]

  - fixed a bug regarding currentRole for tv series.
  - fixed a bug about the "merchandising links" page.

  [http and mobile data access systems]

  - fixed a bug retrieving cover url for tv (mini) series.

  [mobile data access system]

  - fixed a bug with tv series titles.
  - retrieves the number of episodes for tv series.

  [local data access system]

  - new get_episodes function in the cutils/ratober C module.
  - search functions (both C and pure python) are now a lot faster.
  - updated the documentation with work-arounds to make the mkdb program
    works with a recent set of plain text data files.

  [sql data access system]

  - uses the SQLObject ORM to support a wide range of database engines.
  - added in the cutils C module the soundex() function, and a fall back
    Python only version in the parser.sql package.


* What's new in release 2.4 "Munich" (09 Feb 2006)

  [general]

  - strings are now unicode/utf8.
  - unified Movie and Person classes.
  - the strings used to store every kind of information about movies and
    person now are modified (substituting titles and names references)
    only when it's really needed.
  - speed improvements in functions modifyStrings, sortMovies,
    canonicalName, analyze_name, analyze_title.
  - performance improvements in every data access system.
  - removed the deepcopy of the data, updating Movie and Person
    information.
  - moved the "ratober" C module in the imdb.parser.common package,
    being used by both ""http" and "sql" data access systems.
  - C functions in the "ratober" module are always case insensitive.
  - the setup.py script contains a work-around to make installation
    go on even if the "ratober" C module can't be compiled (displaying
    a warning), since it's now optional.
  - minor updates to documentation, to keep it in sync with changes
    in the code.
  - the new helpers.py module contains functions useful to write
    IMDbPY-based programs.
  - new doc file README.utf8, about unicode support.

  [http data access system]

  - the ParserBase class now inherits from sgmllib.SGMLParser,
    instead of htmllib.HTMLParser, resulting in a little improvement
    in parsing speed.
  - fixed a bug in the parser for the "news" page for movies and
    persons.
  - removed special handlers for entity and chardefs in the HTMLMovieParser
    class.
  - fixed bugs related to non-ascii chars.
  - fixed a bug retrieving the URL of the cover.
  - fixed a nasty bug retrieving the title field.
  - retrieve the 'merchandising links' page.
  - support for the new "episodes cast" page for tv series.
  - fixed a horrible bug retrieving guests information for tv series.

  [sql data access system]

  - fixed the imdbpy2sql.py script, to handle files with spurious lines.
  - searches for names and titles are now much faster, if the
    imdb.parser.common.ratober C module is compiled and installed.
  - imdbpy2sql.py now works also on partial data (i.e. if you've not
    downloaded every single plain text file).
  - imdbpy2sql.py considers also a couple of files in the contrib directory.
  - searching names and titles, only the first 5 chars returned from
    the SOUNDEX() SQL function are compared.
  - should works if the database is set to unicode/utf-8.

  [mobile data access system]

  - fixed bugs related to non-ascii chars.
  - fixed a bug retrieving the URL of the cover.
  - retrieve currentRole/notes also for tv guest appearances.

  [local data access system]

  - it can work even if the "ratober" C module is not compiled;
    obviously the pure python substitute is painfully slow (a
    warning is issued).


* What's new in release 2.3 "Big Fish" (03 Dec 2005)

  [general]

  - uniformed numerous keys for Movie and Person objects.
  - 'birth name' is now always in canonical form, and 'nick names'
    are always normalized; these changes also affect the sql data
    access system.

  [http data access system]

  - removed the 'imdb mini-biography by' key; the name of the author
    is now prepended to the 'mini biography' key.
  - fixed an obscure bug using more than one access system (http in
    conjunction with mobile or httpThin).
  - fixed a bug in amazon reviews.

  [mobile data access system]

  - corrected some bugs retrieving filmography and cast list.

  [sql data access system]

  - remove 'birth name' and 'nick names' from the list of 'akas'.
  - in the SQL database, 'crewmembers' is now 'miscellaneous crew'.
  - fixed a bug retrieving "guests" for TV Series.


* What's new in release 2.2 "The Thing" (17 Oct 2005)

  [general]

  - now the Person class has a 'billingPos' instance variable used to
    keep record of the position of the person in the list of credits (as
    an example, "Laurence Fishburne" is billed in 2nd position in the
    cast list for the "Matrix, The (1999)" movie.
  - added two functions to the utils module, to sort respectively
    movies (by year/title/imdbIndex) and persons (by billingPos/name/imdbIndex).
  - every data access system support the 'adultSearch' argument and the
    do_adult_search() method to exclude the adult movies from your searches.
    By default, adult movies are always listed.
  - renamed the scripts, appending the ".py" extension.
  - added an "IMDbPY Powered" logo and a bitmap used by the Windows installer.
  - now Person and Movie objects always convert name/title to the canonical
    format (Title, The).
  - minor changes to the functions used to convert to "canonical format"
    names and titles; they should be faster and with better matches.
  - 'title' is the first argument, instancing a Movie object (instead
    of 'movieID').
  - 'name' is the first argument, instancing a Movie object (instead
    of 'personID').

  [http data access system]

  - retrieves the 'guest appearances' page for TV series.
  - fixed a bug retrieving newsgroup reviews urls.
  - fixed a bug managing non-breaking spaces (they're truly a damnation!)
  - fixed a bug with mini TV Series in people's biographies.
  - now keywords are in format 'bullet-time' and no more 'Bullet Time'.

  [mobile data access system]

  - fixed a bug with direct hits, searching for a person's name.
  - fixed a bug with languages and countries.

  [local data access system]

  - now cast entries are correctly sorted.
  - new search system; it should return better matches in less
    time (searching people's name is still somewhat slow); it's
    also possibile to search for "long imdb canonical title/name".
  - fixed a bug retrieving information about a movie with the same
    person listed more than one time in a given role/duty (e.g., the
    same director for different episodes of a TV series).  Now it
    works fine and it should also be a bit faster.
  - 'notable tv guest appearences' in biography is now a list of Movie
    objects.
  - writers are sorted in the right order.

  [sql data access system]

  - search results are now sorted in correct order; difflib is used to
    calculate strings similarity.
  - new search SQL query and comparison algorithm; it should return
    much better matches.
  - searches for only a surname now returns much better results.
  - fixed a bug in the imdbpy2sql.py script; now movie quotes are correctly
    managed.
  - added another role, 'guests', for notable tv guest appearences.
  - writers are sorted in the right order.
  - put also the 'birth name' and the 'nick names' in the akanames table.


* What's new in release 2.1 "Madagascar" (30 Aug 2005)

  [general]

  - introduced the "sql data access system"; now you can transfer the
    whole content of the plain text data files (distributed by IMDb)
    into a SQL database (MySQL, so far).
  - written a tool to insert the plain text data files in a SQL database.
  - fixed a bug in items() and values() methods of Movie and Person
    classes.
  - unified portions of code shared between "local" and "sql".

  [http data access system]

  - fixed a bug in the search_movie() and search_person() methods.
  - parse the "external reviews", "newsgroup reviews", "newsgroup reviews",
    "misc links", "sound clips", "video clips", "amazon reviews", "news" and
    "photo sites" pages for movies.
  - parse the "news" page for persons.
  - fixed a bug retrieving personID and movieID within namesRefs
    and titlesRefs.

  [local data access system]

  - fixed a bug; 'producer' data where scanned two times.
  - some tags were missing for the laserdisc entries.

  [mobile data access system]

  - fixed a bug retrieving cast information (sometimes introduced
    with "Cast overview" and sometimes with "Credited cast").
  - fixed a bug in the search_movie() and search_person() methods.


* What's new in release 2.0 "Land Of The Dead" (16 Jul 2005)

  [general]

  - WARNING! Now, using http and mobile access methods, movie/person
    searches will include by default adult movie titles/pornstar names.
    You can still deactivate this feature by setting the adultSearch
    argument to false, or calling the do_adult_search() method with
    a false value.
  - fixed a bug using the 'all' keyword of the 'update' method.

  [http data access system]

  - added the "recommendations" page.
  - the 'notes' instance variable is now correctly used to store
    miscellaneous information about people in non-cast roles, replacing
    the 'currentRole' variable.
  - the adultSearch initialization argument is by default true.
  - you can supply the proxy to use with the 'proxy' initialization
    argument.
  - retrieve the "plot outline" information.
  - fixed a bug in the BasicMovieParser class, due to changes in the
    IMDb's html.
  - the "rating details" parse information about the total number
    of voters, arithmetic mean, median and so on.  The values are
    stored as integers and floats, and no more as strings.
  - dictionary keys in soundtrack are lowercase.
  - fixed a bug with empty 'location' information.

  [mobile data access system]

  - number of votes, rating and top 250 rank are now integers/floats.
  - retrieve the "plot outline" information.

  [local data access system]

  - number of votes, rating and top 250 rank are now integers/floats.


* What's new in release 1.9 "Ed Wood" (02 May 2005)

  [general]

  - introduced the new "mobile" data access system, useful for
    small systems.  It should be from 2 to 20 times faster than "http"
    or "httpThin".
  - the "http", "httpThin" and "mobile" data access system can now
    search for adult movies.  See the README.adult file.
  - now it should works again with python 2.0 and 2.1.
  - fixed a bug affecting performances/download time.
  - unified some keywords amongst differents data access systems.

  [http data access system]

  - fixed some bugs; now it retrieves names akas correctly.


* What's new in release 1.8 "Paths Of Glory" (24 Mar 2005)

  [general]

  - introduced a new data access system "httpThin", useful for
    systems with limited bandwidth and CPU power, like PDA,
    hand-held devices and mobile phones.
  - the setup.py script can be configured to not compile/install
    the local access system and the example scripts (useful for
    hand-held devices); introduced setup.cfg and MANIFEST.in files.
  - updated the list of articles used to manage movie titles.
  - removed the all_info tuples from Movie and Person classes,
    since the list of available info sets depends on the access
    system. I've added two methods to the IMDbBase class,
    get_movie_infoset() and get_person_infoset().
  - removed the IMDbNotAvailable exception.
  - unified some code in methods get_movie(), get_person() and
    update() in IMDbBase class.
  - minor updates to the documentation; added a 46x46 PNG icon.
  - documentation for small/mobile systems.

  [Movie class]

  - renamed the m['notes'] item of Movie objects to m['episodes'].

  [Person class]

  - the p.__contains__(m) method can be used to check if the p
    Person has worked in the m Movie.

  [local data access system]

  - gather information about "laserdisc", "literature" and "business".
  - fixed a bug in ratober.c; now the search_name() function
    handles search strings already in the "Surname, Name" format.
  - two new methods, get_lastMovieID() and get_lastPersonID().

  [http data access system]

  - limit the number of results for the query; this will save a
    lot of bandwidth.
  - fixed a bug retrieving the number of episodes of tv series.
  - now it retrieves movies information about "technical specifications",
    "business data", "literature", "soundtrack", "dvd" and "locations".
  - retrieves people information about "publicity" and "agent".


* What's new in release 1.7 "Saw" (04 Feb 2005)

  [general]

  - Person class has two new keys; 'canonical name' and
    'long imdb canonical name', like "Gibson, Mel" and
    "Gibson, Mel (I)".
  - now titles and names are always internally stored in the
    canonical format.
  - search_movie() and search_person() methods return the
    "read" movieID or personID (handling aliases).
  - Movie and Person objects have a 'notes' instance attribute,
    used to specify comments about the role of a person in a movie.
    The Movie class can also contain a ['notes'] item, used to
    store information about the runtime; e.g. (26 episodes).
  - fixed minor bugs in the IMDbBase, Person and Movie classes.
  - some performance improvements.

  [http data access system]

  - fixed bugs retrieving the currentRole.
  - try to handle unicode chars; return unicode strings when required.
  - now the searches return also "popular titles" and
    "popular names" from the new IMDb's search system.

  [local data access system]

  - information about movie connections are retrieved.
  - support for multiple biographies.
  - now it works with Python 2.2 or previous versions.
  - fixed a minor glitch in the initialization of the ratober C module.
  - fixed a pair buffer overflows.
  - fixed some (very rare) infinite loops bugs.
  - it raises IMDbDataAccessError for (most of) I/O errors.

  [Movie class]
  - fixed a bug getting the "long imdb canonical title".


* What's new in release 1.6 "Ninja Commandments" (04 Jan 2005)

  [general]

  - now inside Movie and Person object, the text strings (biography,
    movie plot, etc.) contain titles and names references, like
    "_Movie, The (1999)_ (qv)" or "'A Person' (qv)"; these reference
    are transformed at access time with a user defined function.
  - introduced _get_real_movieID and _get_real_personID methods
    in the IMDbBase class, to handle title/name aliases for the
    local access system.
  - split the _normalize_id method in _normalize_movieID
    and _normalize_personID.
  - fixed some bugs.

  [Movie class]

  - now you can access the 'canonical title' and
    'long imdb canonical title' attributes, to get the movie title
    in the format "Movie Title, The".

  [local data access system]

  - title and name aliases now work correctly.
  - now get_imdbMovieID and get_imdbPersonID methods should
    work in almost every case.
  - people's akas are handled.

  [http data access system]

  - now the BasicMovieParser class can correctly gather the imdbID.


* What's new in release 1.5 "The Incredibles" (23 Dec 2004)

  [local database]

  - support a local installation of the IMDb database!
    WOW!  Now you can download the plain text data files from
    http://imdb.com/interfaces.html and access those
    information through IMDbPY!

  [general]

  - movie titles and person names are "fully normalized";
    Not "Matrix, The (1999)", but "The Matrix (1999)";
    Not "Cruise, Tom" but "Tom Cruise".
  - get_mop_infoSet() methods can now return a tuple with the
    dictionary data and a list of information sets they provided.

  [http data access system]

  - support for the new search system (yes, another one...)
  - a lot of small fixes to stay up-to-date with the html
    of the IMDb web server.
  - modified the personParser module so that it will no
    more download both "filmoyear" and "maindetails" pages;
    now only the latter is parsed.
  - movie search now correctly reports the movie year and index.
  - gather "locations" information about a movie.
  - modified the HTMLAwardsParser class so that it doesn't list
    empty entries.


* What's new in release 1.4 "The Village" (10 Nov 2004)

  [http data access system]

  - modified the personParser.HTMLMaindetailsParser class,
    because IMDb has changed the img tag for the headshot.
  - now 'archive footage' is handled correctly.

  [IMDb class]

  - fixed minor glitches (missing "self" parameter in a
    couple of methods).

  [misc]

  - now distutils installs also the example scripts in ./bin/*


* What's new in release 1.3 "House of 1000 Corpses" (6 Jul 2004)

  [http data access system]

  - modified the BasicMovieParser and BasicPersonParser classes,
    because IMDb has removed the "pageflicker" from the html pages.

  [general]

  - the test suite was moved outside the tgz package.


* What's new in release 1.2 "Kill Bill" (2 May 2004)

  [general]

  - now it retrieves almost every available information about movie
    and people!
  - introduced the concept of "data set", to retrieve different sets
    of information about a movie/person (so that it's possibile to
    fetch only the needed information).
  - introduced a test suite, using the PyUnit (unittest) module.
  - fixed a nasty typo; the analyze_title and build_title functions
    now use the strings 'tv mini series' and 'tv series' for the 'kind'
    key (previously the 'serie' word ws used).
  - new design; removed the mix-in class and used a factory pattern;
    imdb.IMDb is now a function, which returns an instance of a class,
    subclass of imdb.IMDbBase.
  - introduced the build_name(name_dict) function in the utils module,
    which takes a dictionary and build a long imdb name.
  - fixed bugs in the analyze_name function; now it correctly raise
    an IMDbParserError exception for empty/all spaces strings.
  - now the analyze_title function sets only the meaningful
    information (i.e.: no 'kind' or 'year' key, if they're not set)

  [http data access system]

  - removed all non-greedy regular expressions.
  - removed all regular expressions in the movieParser module; now
    self.rawdata is no more used to search "strange" matches.
  - introduced a ParserBase class, used as base class for the parsers.
  - retrieve information about the production status (pre-production,
    announced, in production, etc.)
  - mpaa is now a string.
  - now when an IMDbDataAccessError is raised it shows also the
    used proxy.
  - minor changes to improve performances in the handle_data method of
    the HTMLMovieParser class.
  - minor changes to achieve a major performances improvement in
    the BasicPersonParser class in the searchPersonParse module.

  [Movie class]

  - fixed a bug in isSameTitle method, now the accessSystem is correctly
    checked.
  - fixed some typos.

  [Person class]

  - minor changes to the isSamePerson method (now it uses the build_name
    function).


* What's new in release 1.1 "Gigli" (17 Apr 2004)

  [general]

  - added support for persons (search & retrieve information about people).
  - removed the dataSets module.
  - removed the MovieTitle and the SearchMovieResults classes; now information
    about the title is stored directly in the Movie object and the search
    methods return simple lists (of Movie or Person objects).
  - removed the IMDbTitleError exception.
  - added the analyze_name() function in the imdb.utils module, which
    returns a dictionary with the 'name' and 'imdbIndex' keys from the
    given long imdb name string.

  [http data access system]

  - http search uses the new search system.
  - moved the plotParser module content inside the movieParser module.
  - fixed a minor bug handling AKAs for movie titles.

  [IMDb class]

  - introduced the update(obj) method of the IMDb class, to update
    the information of the given object (a Movie or Person instance).
  - added the get_imdbURL(obj) method if the IMDb class, which returns
    the URL of the main IMDb page for the given object (a Movie or Person).
  - renamed the 'kind' parameter of the IMDb class to 'accessSystem'.

  [Movie class]

  - now __str__() returns only the short name; the summary() method
    returns a pretty-printed string for the Movie object.
  - persons are no more simple strings, but Person objects (the role/duty
    is stored in the currentRole variable of the object).
  - isSameTitle(obj) method to compare two Movie objects even when
    not all information are gathered.
  - new __contains__() method, to check is a given person was in a movie.

  [misc]

  - updated the documentation.
  - corrected some syntax/grammar errors.


* What's new in release 1.0 "Equilibrium" (01 Apr 2004)

  [general]

  - first public release.
  - retrieve data only from the web server.
  - search only for movie titles.
