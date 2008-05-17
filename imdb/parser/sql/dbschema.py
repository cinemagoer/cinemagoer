"""
parser.sql.dbschema module (imdb.parser.sql package).

This package provides the SQLObject's classes used to describe
the layout of the database used by thr imdb.parser.sql package.
Every database supported by the SQLObject Object Relational Manager
is available.

Copyright 2005-2008 Davide Alberani <da@erlug.linux.it>
               2006 Giuseppe "Cowo" Corbelli <cowo --> lugbs.linux.it>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from sqlobject import *

# XXX: ForeignKey can be used to create constrains between tables,
#      but they create an Index in the database, and this
#      means poor performances at insert-time.

class AkaName(SQLObject):
    personID = IntCol(notNone=True)
    name = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    namePcodeCf = StringCol(length=5, default=None)
    namePcodeNf = StringCol(length=5, default=None)
    surnamePcode = StringCol(length=5, default=None)

class KindType(SQLObject):
    """this table is for values like 'movie', 'tv series', 'video games'..."""
    kind = UnicodeCol(length=15, default=None, alternateID=True)

class CompanyType(SQLObject):
    """this table is for values like 'production companies'."""
    kind = UnicodeCol(length=32, default=None, alternateID=True)

class AkaTitle(SQLObject):
    # XXX: It's safer to set notNone to False, here.
    #      alias for akas are stored completely in the AkaTitle table;
    #      this means that episodes will set also a "tv series" alias name.
    #      Reading the aka-title.list file it looks like there are
    #      episode titles with aliases to different titles for both
    #      the episode and the series title, while for just the series
    #      there are no aliases.
    #      E.g.:
    #      aka title                                 original title
    # "Series, The" (2005) {The Episode}     "Other Title" (2005) {Other Title}
    # But there is no:
    # "Series, The" (2005)                   "Other Title" (2005)
    movieID = IntCol(notNone=False)
    title = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    kindID = IntCol(notNone=True)
    productionYear = IntCol(default=None)
    phoneticCode = StringCol(length=5, default=None)
    episodeOfID = IntCol(default=None)
    seasonNr = IntCol(default=None)
    episodeNr = IntCol(default=None)
    note = UnicodeCol(default=None)

class CastInfo(SQLObject):
    personID = IntCol(notNone=True)
    movieID = IntCol(notNone=True)
    personRoleID = IntCol(default=None)
    note = UnicodeCol(default=None)
    nrOrder = IntCol(default=None)
    roleID = IntCol(notNone=True)

class CompCastType(SQLObject):
    kind = UnicodeCol(length=32, notNone=True, alternateID=True)

class CompleteCast(SQLObject):
    movieID = IntCol()
    subjectID = IntCol(notNone=True)
    statusID = IntCol(notNone=True)

class InfoType(SQLObject):
    info = UnicodeCol(length=32, notNone=True, alternateID=True)

class LinkType(SQLObject):
    link = UnicodeCol(length=32, notNone=True, alternateID=True)

class MovieLink(SQLObject):
    movieID = IntCol(notNone=True)
    linkedMovieID = IntCol(notNone=True)
    linkTypeID = IntCol(notNone=True)

class MovieInfo(SQLObject):
    movieID = IntCol(notNone=True)
    infoTypeID = IntCol(notNone=True)
    info = UnicodeCol(notNone=True)
    note = UnicodeCol(default=None)

class MovieCompanies(SQLObject):
    movieID = IntCol(notNone=True)
    companyID = IntCol(notNone=True)
    companyTypeID = IntCol(notNone=True)
    note = UnicodeCol(default=None)

class Name(SQLObject):
    """
    namePcodeCf is the soundex of the name in the canonical format.
    namePcodeNf is the soundex of the name in the normal format, if different
    from namePcodeCf.
    surnamePcode is the soundex of the surname, if different from the
    other two values
    """
    name = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    imdbID = IntCol(default=None)
    namePcodeCf = StringCol(length=5, default=None)
    namePcodeNf = StringCol(length=5, default=None)
    surnamePcode = StringCol(length=5, default=None)

class CharName(SQLObject):
    """
    namePcodeNf is the soundex of the name in the normal format.
    surnamePcode is the soundex of the surname, if different from namePcodeNf.
    """
    name = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    imdbID = IntCol(default=None)
    namePcodeNf = StringCol(length=5, default=None)
    surnamePcode = StringCol(length=5, default=None)

class CompanyName(SQLObject):
    """
    namePcodeNf is the soundex of the name in the normal format.
    namePcodeSf is the soundex of the name plus the country code.
    """
    name = UnicodeCol(notNone=True)
    # Maybe a little too long.
    countryCode = UnicodeCol(length=255, default=None)
    imdbID = IntCol(default=None)
    namePcodeNf = StringCol(length=5, default=None)
    namePcodeSf = StringCol(length=5, default=None)

class PersonInfo(SQLObject):
    personID = IntCol(notNone=True)
    infoTypeID = IntCol(notNone=True)
    info = UnicodeCol(notNone=True)
    note = UnicodeCol(default=None)

class RoleType(SQLObject):
    role = UnicodeCol(length=32, notNone=True, alternateID=True)

class Title(SQLObject):
    title = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    kindID = IntCol(notNone=True)
    productionYear = IntCol(default=None)
    imdbID = IntCol(default=None)
    phoneticCode = StringCol(length=5, default=None)
    episodeOfID = IntCol(default=None)
    seasonNr = IntCol(default=None)
    episodeNr = IntCol(default=None)
    # Maximum observed length is 44; 49 can store 5 comma-separated
    # year-year pairs.
    seriesYears = StringCol(length=49, default=None)


DB_TABLES = [Name, CharName, CompanyName, KindType, Title, CompanyType,
        AkaName, AkaTitle, RoleType, CastInfo, CompCastType, CompleteCast,
        InfoType, LinkType, MovieLink, MovieInfo, MovieCompanies, PersonInfo]

def setConnection(uri, debug=False):
    """Set connection for every table."""
    kw = {}
    # FIXME: it's absolutely unclear what we should do to correctly
    #        support unicode in MySQL; with some versions of SQLObject,
    #        it seems that setting use_unicode=1 is the _wrong_ thing to do.
    if uri.lower().startswith('mysql'):
        kw['use_unicode'] = 1
        kw['sqlobject_encoding'] = 'utf8'
        kw['charset'] = 'utf8'
    conn = connectionForURI(uri, **kw)
    conn.debug = debug
    for table in DB_TABLES:
        table.setConnection(conn)
        table.sqlmeta.cacheValues = False
        table._cacheValue = False
    return conn

def dropTables(ifExists=True, connectURI=None):
    """Drop the tables."""
    if connectURI is not None:
        setConnection(connectURI)
    DB_TABLES_DROP = list(DB_TABLES)
    DB_TABLES_DROP.reverse()
    for table in DB_TABLES_DROP:
        table.dropTable(ifExists)

def createTables(connectURI=None, ifNotExists=True):
    """Create the tables and insert default values."""
    if connectURI is not None:
        setConnection(connectURI)
    for table in DB_TABLES:
        table.createTable(ifNotExists=ifNotExists)
    for kind in ('movie', 'tv series', 'tv movie', 'video movie',
                'tv mini series', 'video game', 'episode'):
        KindType(kind=kind)
    for ckind in ('distributors', 'production companies',
                'special effects companies', 'miscellaneous companies'):
        CompanyType(kind=ckind)
    INFOS = ('runtimes', 'color info', 'genres', 'languages', 'certificates',
            'sound mix', 'tech info', 'countries', 'taglines', 'keywords',
            'alternate versions', 'crazy credits', 'goofs', 'soundtrack',
            'quotes', 'release dates', 'trivia', 'locations', 'mini biography',
            'birth notes', 'birth date', 'height', 'death date', 'spouse',
            'other works', 'birth name', 'salary history', 'nick names',
            'books', 'agent address', 'biographical movies', 'portrayed',
            'where now', 'trademarks', 'interviews', 'articles',
            'magazine covers', 'pictorials', 'death notes', 'LD disc format',
            'LD year', 'LD digital sound', 'LD official retail price',
            'LD frequency response', 'LD pressing plant', 'LD length',
            'LD language', 'LD review', 'LD spaciality', 'LD release date',
            'LD production country', 'LD contrast', 'LD color rendition',
            'LD picture format', 'LD video noise', 'LD video artifacts',
            'LD release country', 'LD sharpness', 'LD dynamic range',
            'LD audio noise', 'LD color information', 'LD group (genre)',
            'LD quality program', 'LD close captions/teletext/ld+g',
            'LD category', 'LD analog left', 'LD certification',
            'LD audio quality', 'LD video quality', 'LD aspect ratio',
            'LD analog right', 'LD additional information',
            'LD number of chapter stops', 'LD dialogue intellegibility',
            'LD disc size', 'LD master format', 'LD subtitles',
            'LD status of availablility', 'LD quality of source',
            'LD number of sides', 'LD video standard', 'LD supplement',
            'LD original title', 'LD sound encoding', 'LD number', 'LD label',
            'LD catalog number', 'LD laserdisc title', 'screenplay/teleplay',
            'novel', 'adaption', 'book', 'production process protocol',
            'printed media reviews', 'essays', 'other literature', 'mpaa',
            'plot', 'votes distribution', 'votes', 'rating',
            'production dates', 'copyright holder', 'filming dates', 'budget',
            'weekend gross', 'gross', 'opening weekend', 'rentals',
            'admissions', 'studios', 'top 250 rank', 'bottom 10 rank')
    for info in INFOS:
        InfoType(info=info)
    for ccast in ('cast', 'crew', 'complete', 'complete+verified'):
        CompCastType(kind=ccast)
    LINKS = ('follows', 'followed by', 'remake of', 'remade as', 'references',
            'referenced in', 'spoofs', 'spoofed in', 'features',
            'featured in', 'spin off from', 'spin off', 'version of',
            'similar to', 'edited into', 'edited from',
            'alternate language version of', 'unknown link')
    for link in LINKS:
        LinkType(link=link)
    # XXX: I'm quite sure that 'guest' is now obsolete.
    ROLES = ('actor', 'actress', 'producer', 'writer', 'cinematographer',
            'composer', 'costume designer', 'director', 'editor',
            'miscellaneous crew', 'production designer', 'guest')
    for role in ROLES:
        RoleType(role=role)


def _hasIndex(table, index):
    """Return True if the named index is already in the given table."""
    return index.name in [idx.name for idx in table.sqlmeta.indexes]


def createIndexes(ifNotExists=True, connectURI=None):
    """Create the indexes in the database."""
    if connectURI is not None:
        setConnection(connectURI)
    indexesDef = [
        (AkaName, [
                    DatabaseIndex('personID', name='idx_person'),
                    DatabaseIndex('namePcodeCf', name='idx_pcodecf'),
                    DatabaseIndex('namePcodeNf', name='idx_pcodenf'),
                    DatabaseIndex('surnamePcode', name='idx_pcode')]),
        (AkaTitle, [
                    DatabaseIndex('movieID', name='idx_movieid'),
                    DatabaseIndex('phoneticCode', name='idx_pcode'),
                    DatabaseIndex('episodeOfID', name='idx_epof')]),
        (CastInfo, [DatabaseIndex('personID', name='idx_pid'),
                    DatabaseIndex('movieID', name='idx_mid'),
                    DatabaseIndex('personRoleID', name='idx_cid')]),
        (CompleteCast, [DatabaseIndex('movieID', name='idx_mid')]),
        (MovieLink, [DatabaseIndex('movieID', name='idx_mid')]),
        (MovieInfo, [DatabaseIndex('movieID', name='idx_mid')]),
        (MovieCompanies, [
                    DatabaseIndex('movieID', name='idx_mid'),
                    DatabaseIndex('companyID', name='idx_cid')]),
        (Name, [DatabaseIndex({'column': 'name', 'length': 6},
                                name='idx_name'),
                DatabaseIndex('namePcodeCf', name='idx_pcodecf'),
                DatabaseIndex('namePcodeNf', name='idx_pcodenf'),
                DatabaseIndex('surnamePcode', name='idx_pcode')]),
        (CharName, [DatabaseIndex({'column': 'name', 'length': 6},
                                name='idx_name'),
                DatabaseIndex('namePcodeNf', name='idx_pcodenf'),
                DatabaseIndex('surnamePcode', name='idx_pcode')]),

        (PersonInfo, [DatabaseIndex('personID', name='idx_pid')]),
        (CompanyName, [
                    DatabaseIndex({'column': 'name', 'length': 6},
                                name='idx_name'),
                    DatabaseIndex('namePcodeNf', name='idx_pcodenf'),
                    DatabaseIndex('namePcodeSf', name='idx_pcodesf')]),
        (Title, [DatabaseIndex({'column': 'title', 'length': 10},
                                name='idx_title'),
                DatabaseIndex('phoneticCode', name='idx_pcode'),
                DatabaseIndex('episodeOfID', name='idx_epof')])]
    for table, indexes in indexesDef:
        for index in indexes:
            if not _hasIndex(table, index):
                table.sqlmeta.addIndex(index)
        table.createIndexes(ifNotExists=ifNotExists)

