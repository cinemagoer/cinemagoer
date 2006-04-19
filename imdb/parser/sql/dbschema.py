#!/usr/bin/env python

from sqlobject import *

class AkaName(SQLObject):
    person = ForeignKey('Name', notNone=True)
    name = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    phoneticCode1 = StringCol(default=None)
    phoneticCode2 = StringCol(default=None)
    phoneticCode3 = StringCol(default=None)

class KindType(SQLObject):
    """this table is for values like 'movie', 'tv series', 'video games'..."""
    kind = UnicodeCol(length=15, default=None, alternateID=True)

class AkaTitle(SQLObject):
    # XXX: I fear that it's safer to set notNone to False, here.
    #        alias for akas are stored completely in the AkaTitle table;
    #        this means that episodes will set also a "tv series" alias
    #        name.
    #        Reading the aka-title.list file it looks like there are
    #        episode titles with aliases to different titles for both
    #        the episode and the series title, while for just the series
    #        there are no aliases.
    #        E.g.:
    #        aka title                                 original title
    # "Series, The" (2005) {The Episode}     "Other Title" (2005) {Other Title}
    # But there is no:
    # "Series, The" (2005)                   "Other Title" (2005)
    #
    # Another option is to handle these cases, and add the "Other Title" (2005)
    # AKA and make it point to the "Series, The" (2005) original title.
    # I'm not sure this can be always feasible.
    movie = ForeignKey('Title', notNone=True)
    title = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    kind = ForeignKey('KindType', notNone=True)
    productionYear = IntCol(default=None)
    phoneticCode = StringCol(default=None)
    note = UnicodeCol(default=None)
    episodeOf = ForeignKey('AkaTitle', default=None)

class CastInfo(SQLObject):
    person = ForeignKey('Name', notNone=True)
    movie = ForeignKey('Title', notNone=True)
    personRole = UnicodeCol(default=None)
    note = UnicodeCol(default=None)
    nrOrder = IntCol(default=None)
    role = ForeignKey('RoleType', notNone=True)

class CompCastType(SQLObject):
    kind = UnicodeCol(length=32, notNone=True, alternateID=True)

class CompleteCast(SQLObject):
    movie = ForeignKey('Title')
    subject = ForeignKey('CompCastType', notNone=True)
    status = ForeignKey('CompCastType', notNone=True)
    note = UnicodeCol(default=None)

class InfoType(SQLObject):
    info = UnicodeCol(length=32,notNone=True, alternateID=True)

class LinkType(SQLObject):
    link = UnicodeCol(length=32, notNone=True, alternateID=True)

class MovieLink(SQLObject):
    movie = ForeignKey('Title', notNone=True)
    linkedMovie = ForeignKey('Title', notNone=True)
    linkType = ForeignKey('LinkType', notNone=True)
    note = UnicodeCol(default=None)

class MovieInfo(SQLObject):
    movie = ForeignKey('Title', notNone=True)
    infoType = ForeignKey('InfoType', notNone=True)
    info = UnicodeCol(notNone=True)
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

class PersonInfo(SQLObject):
    person = ForeignKey('Name', notNone=True)
    infoType = ForeignKey('InfoType', notNone=True)
    info = UnicodeCol(notNone=True)
    note = UnicodeCol(default=None)

class RoleType(SQLObject):
    role = UnicodeCol(length=32, notNone=True, alternateID=True)

class Title(SQLObject):
    title = UnicodeCol(notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    kind = ForeignKey('KindType', notNone=True)
    productionYear = IntCol(default=None)
    imdbID = IntCol(default=None)
    phoneticCode = StringCol(length=5, default=None)
    episodeOf = ForeignKey('Title', default=None)

DB_TABLES = [Name, KindType, Title, AkaName, AkaTitle, RoleType, CastInfo,
        CompCastType, CompleteCast, InfoType, LinkType, MovieLink, MovieInfo,
        PersonInfo]

def setConnection(uri):
    """Set connection for every table."""
    conn = connectionForURI(uri)
    for table in DB_TABLES:
        table.setConnection(conn)
    return conn

def dropTables(ifExists=True, connectURI=None):
    """Drop the tables."""
    if connectURI is not None:
        setConnection(connectURI)
    DB_TABLES_DROP = list(DB_TABLES)
    DB_TABLES_DROP.reverse()
    for table in DB_TABLES_DROP:
        table.dropTable(ifExists)

def createTables(connectURI=None):
    """Create the tables and insert default values."""
    if connectURI is not None:
        setConnection(connectURI)
    for table in DB_TABLES:
        table.createTable()
    for kind in ('movie', 'tv series', 'tv movie', 'video movie', 'tv mini series', 'video game', 'episode'):
        KindType(kind=kind)
    INFOS = ('runtimes', 'color info', 'genres', 'distributors', 'languages', 'certificates', 'special effects companies', 'sound mix', 'tech info', 'production companies', 'countries', 'taglines', 'keywords', 'alternate versions', 'crazy credits', 'goofs', 'soundtrack', 'quotes', 'release dates', 'trivia', 'locations', 'miscellaneous companies', 'mini biography', 'birth notes', 'birth date', 'height', 'death date', 'spouse', 'other works', 'birth name', 'salary history', 'nick names', 'books', 'agent address', 'biographical movies', 'portrayed', 'where now', 'trademarks', 'interviews', 'articles', 'magazine covers', 'pictorials', 'death notes', 'LD disc format', 'LD year', 'LD digital sound', 'LD official retail price', 'LD frequency response', 'LD pressing plant', 'LD length', 'LD language', 'LD review', 'LD spaciality', 'LD release date', 'LD production country', 'LD contrast', 'LD color rendition', 'LD picture format', 'LD video noise', 'LD video artifacts', 'LD release country', 'LD sharpness', 'LD dynamic range', 'LD audio noise', 'LD color information', 'LD group (genre)', 'LD quality program', 'LD close captions/teletext/ld+g', 'LD category', 'LD analog left', 'LD certification', 'LD audio quality', 'LD video quality', 'LD aspect ratio', 'LD analog right', 'LD additional information', 'LD number of chapter stops', 'LD dialogue intellegibility', 'LD disc size', 'LD master format', 'LD subtitles', 'LD status of availablility', 'LD quality of source', 'LD number of sides', 'LD video standard', 'LD supplement', 'LD original title', 'LD sound encoding', 'LD number', 'LD label', 'LD catalog number', 'LD laserdisc title', 'screenplay/teleplay', 'novel', 'adaption', 'book', 'production process protocol', 'printed media reviews', 'essays', 'other literature', 'mpaa', 'plot', 'votes distribution', 'votes', 'rating', 'production dates', 'copyright holder', 'filming dates', 'budget', 'weekend gross', 'gross', 'opening weekend', 'rentals', 'admissions', 'studios', 'top 250 rank', 'bottom 10 rank')
    for info in INFOS:
        InfoType(info=info)
    for ccast in ('cast', 'crew', 'complete', 'complete+verified'):
        CompCastType(kind=ccast)
    LINKS = ('follows', 'followed by', 'remake of', 'remade as', 'references', 'referenced in', 'spoofs', 'spoofed in', 'features', 'featured in', 'spin off from', 'spin off', 'version of', 'similar to', 'edited into', 'edited from', 'alternate language version of', 'unknown link')
    for link in LINKS:
        LinkType(link=link)
    ROLES = ('actor', 'actress', 'producer', 'writer', 'cinematographer', 'composer', 'costume designer', 'director', 'editor', 'miscellaneous crew', 'production designer', 'guest')
    for role in ROLES:
        RoleType(role=role)

