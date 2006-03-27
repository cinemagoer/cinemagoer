#!/usr/bin/env python

from sqlobject import *

class AkaName(SQLObject):
    person = ForeignKey('Name', notNone=True)
    name = UnicodeCol(length=255, notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)

class KindType(SQLObject):
    """this table is for values like 'movie', 'tv series', 'video games'..."""
    kind = UnicodeCol(length=15, default=None, alternateID=True)

class AkaTitle(SQLObject):
    movie = ForeignKey('Title', notNone=True)
    title = UnicodeCol(length=255, notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    kind = ForeignKey('KindType', notNone=True)
    productionYear = IntCol(default=None)
    note = UnicodeCol(length=255, default=None)

class CastInfo(SQLObject):
    person = ForeignKey('Name', notNone=True)
    movie = ForeignKey('Title', notNone=True)
    personRole = UnicodeCol(length=255, default=None)
    note = UnicodeCol(length=255, default=None)
    nrOrder = IntCol(default=None)
    role = ForeignKey('RoleType', notNone=True)

class CompCastType(SQLObject):
    kind = UnicodeCol(length=32, notNone=True, alternateID=True)

class CompleteCast(SQLObject):
    movie = ForeignKey('Title')
    subject = ForeignKey('CompCastType', notNone=True)
    status = ForeignKey('CompCastType', notNone=True)
    note = UnicodeCol(length=255, default=None)

class InfoType(SQLObject):
    info = UnicodeCol(length=32,notNone=True, alternateID=True)

class LinkType(SQLObject):
    link = UnicodeCol(length=32, notNone=True, alternateID=True)

class MovieLink(SQLObject):
    movie = ForeignKey('Title', notNone=True)
    linkedMovie = ForeignKey('Title', notNone=True)
    linkType = ForeignKey('LinkType', notNone=True)
    note = UnicodeCol(length=255, default=None)

class MovieInfo(SQLObject):
    movie = ForeignKey('Title', notNone=True)
    infoType = ForeignKey('InfoType', notNone=True)
    info = UnicodeCol(notNone=True)
    note = UnicodeCol(length=255, default=None)

class Name(SQLObject):
    name = UnicodeCol(length=255, notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    imdbID = IntCol(default=None)

class PersonInfo(SQLObject):
    person = ForeignKey('Name', notNone=True)
    infoType = ForeignKey('InfoType', notNone=True)
    info = UnicodeCol(notNone=True)
    note = UnicodeCol(length=255, default=None)

class RoleType(SQLObject):
    role = UnicodeCol(length=32, notNone=True, alternateID=True)

class Title(SQLObject):
    title = UnicodeCol(length=255, notNone=True)
    imdbIndex = UnicodeCol(length=12, default=None)
    kind = ForeignKey('KindType', notNone=True)
    productionYear = IntCol(default=None)
    imdbID = IntCol(default=None)
    phoneticCode = StringCol(default=None)
    episodeOf = ForeignKey('Episodes')

class Episodes(SQLObject):
    episodeID = IntCol(alternateID=True, notNone=True)

DB_TABLES = [Name, KindType, Title, AkaName, AkaTitle, RoleType, CastInfo,
        CompCastType, CompleteCast, InfoType, LinkType, MovieLink, MovieInfo,
        PersonInfo, Episodes]

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
    for kind in ('movie', 'tv series', 'tv movie', 'video movie', 'tv mini series', 'video game'):
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

