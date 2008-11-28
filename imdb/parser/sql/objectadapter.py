"""
parser.sql.objectadapter module (imdb.parser.sql package).

This module adpts the SQLObject ORM to the internal mechanism.

Copyright 2008 Davide Alberani <da@erlug.linux.it>

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
from sqlobject.sqlbuilder import ISNULL, ISNOTNULL, AND, OR, IN

from dbschema import *


# Maps our placeholders to SQLAlchemy's column types.
MAP_COLS = {
        INTCOL: IntCol,
        UNICODECOL: UnicodeCol,
        STRINGCOL: StringCol
}


# Exception raised when Table.get(id) returns no value.
NotFoundError = SQLObjectNotFound


# class method to be added to the SQLObject class.
def addIndexes(cls, ifNotExists=True):
    """Create all required indexes."""
    for col in cls._imdbpySchema.cols:
        if col.index:
            idxName = col.index
            colToIdx = col.name
            if col.indexLen:
                colToIdx = {'column': col.name, 'length': col.indexLen}
            if idxName in [i.name for i in cls.sqlmeta.indexes]:
                # Check if the index is already present.
                continue
            idx = DatabaseIndex(colToIdx, name=idxName)
            cls.sqlmeta.addIndex(idx)
    cls.createIndexes(ifNotExists)
addIndexes = classmethod(addIndexes)


# Module-level "cache" for SQLObject classes, to prevent
# "class TheClass is already in the registry" errors, when
# two or more connections to the database are made.
# XXX: is this the best way to act?
TABLES_REPOSITORY = {}

def getDBTables(uri=None):
    """Return a list of classes to be used to access the database
    through the SQLObject ORM.  The connection uri is optional, and
    can be used to tailor the db schema to specific needs."""
    DB_TABLES = []
    for table in DB_SCHEMA:
        if table.name in TABLES_REPOSITORY:
            DB_TABLES.append(TABLES_REPOSITORY[table.name])
            continue
        attrs = {'_imdbpyName': table.name, '_imdbpySchema': table,
                'addIndexes': addIndexes}
        for col in table.cols:
            if col.name == 'id':
                continue
            attrs[col.name] = MAP_COLS[col.kind](**col.params)
        # Create a subclass of SQLObject.
        # XXX: use a metaclass?  I can't see any advantage.
        cls = type(table.name, (SQLObject,), attrs)
        DB_TABLES.append(cls)
        TABLES_REPOSITORY[table.name] = cls
    return DB_TABLES


def toUTF8(s):
    """For some strange reason, sometimes SQLObject wants utf8 strings
    instead of unicode."""
    return s.encode('utf_8')


def setConnection(uri, tables, encoding='utf8', debug=False):
    """Set connection for every table."""
    kw = {}
    # FIXME: it's absolutely unclear what we should do to correctly
    #        support unicode in MySQL; with some versions of SQLObject,
    #        it seems that setting use_unicode=1 is the _wrong_ thing to do.
    if uri.lower().startswith('mysql'):
        kw['use_unicode'] = 1
        kw['sqlobject_encoding'] = encoding
        kw['charset'] = encoding
    conn = connectionForURI(uri, **kw)
    conn.debug = debug
    for table in tables:
        table.setConnection(conn)
        #table.sqlmeta.cacheValues = False
        # FIXME: is it safe to set table._cacheValue to False?  Looks like
        #        we can't retrieve correct values after an update (I think
        #        it's never needed, but...)  Anyway, these are set to False
        #        for performance reason at insert time (see imdbpy2sql.py).
        table._cacheValue = False
    # Required by imdbpy2sql.py.
    conn.paramstyle = conn.module.paramstyle
    return conn

