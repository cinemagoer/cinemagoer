#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
"""
imdbpy2sql.py script.

This script puts the data of the plain text data files into a
SQL database (so far, a MySQL database).

Copyright 2005 Davide Alberani <da@erlug.linux.it>

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


import os, sys, getopt, time, re
from gzip import GzipFile

import MySQLdb
from _mysql_exceptions import OperationalError

from imdb.utils import analyze_title, analyze_name, build_name, build_title
from imdb.parser.local.movieParser import _bus, _ldk, _lit, _links_sect
from imdb.parser.local.personParser import _parseBiography
from imdb._exceptions import IMDbParserError

re_nameImdbIndex = re.compile(r'\(([IVXLCDM]+)\)')

HELP = """imdbpy2sql usage:
    %s -d /directory/with/PlainTextDataFiles/ db=imdb user=admin passwd=pwd
        # NOTE: every "key=value" is passed to the MySQLdb connect function.
""" % sys.argv[0]

# Manage arguments list.
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'd:h', ['help'])
except getopt.error, e:
    print 'Troubles with arguments.'
    print HELP
    sys.exit(2)

IMDB_PTDF_DIR = None

for opt in optlist:
    if opt[0] == '-d':
        IMDB_PTDF_DIR = opt[1]
    elif opt[0] in ('-h', '--help'):
        print HELP
        sys.exit(0)

if IMDB_PTDF_DIR is None:
    print 'You must supply the directory with the plain text data files'
    print HELP
    sys.exit(2)

CONN_PARAMS = {}
for arg in args:
    kv = arg.split('=', 1)
    if len(kv) != 2:
        print 'Invalid argument: %s' % arg
        print HELP
        sys.exit(2)
    CONN_PARAMS[kv[0]] = kv[1]


# Connect to the database.
db = MySQLdb.connect(**CONN_PARAMS)
curs = db.cursor()


# Show time consumed by the single function call.
CTIME = int(time.time())
BEGIN_TIME = CTIME
def t(s):
    global CTIME
    nt = int(time.time())
    print '# TIME', s, ': %d min, %s sec.' % divmod(nt-CTIME, 60)
    CTIME = nt


# Handle laserdisc keys.
for key, value in _ldk.items():
    _ldk[key] = 'LD %s' % value


# Tags to identify where the meaningful data begin/end in files.
MOVIES = 'movies.list.gz'
MOVIES_START = ('MOVIES LIST', '===========', '')
MOVIES_STOP = '--------------------------------------------------'
CAST_START = ('Name', '----')
CAST_STOP = '-----------------------------'
RAT_START = ('MOVIE RATINGS REPORT', '',
            'New  Distribution  Votes  Rank  Title')
RAT_STOP = '\n'
RAT_TOP250_START = ('note: for this top 250', '', 'New  Distribution')
RAT_BOT10_START = ('BOTTOM 10 MOVIES', '', 'New  Distribution')
TOPBOT_STOP = '\n'
AKAT_START = ('AKA TITLES LIST', '=============', '', '', '')
AKAT_IT_START = ('AKA TITLES LIST ITALIAN', '=======================', '', '')
AKAT_DE_START = ('AKA TITLES LIST GERMAN', '======================', '')
AKAT_ISO_START = ('AKA TITLES LIST ISO', '===================', '')
AKAN_START = ('AKA NAMES LIST', '=============', '')
AV_START = ('ALTERNATE VERSIONS LIST', '=======================', '', '')
MINHASH_STOP = '-------------------------'
GOOFS_START = ('GOOFS LIST', '==========', '')
QUOTES_START = ('QUOTES LIST', '=============')
CC_START = ('CRAZY CREDITS', '=============')
BIO_START = ('BIOGRAPHY LIST', '==============')
BUS_START = ('BUSINESS LIST', '=============', '')
BUS_STOP = '                                    ====='
CER_START = ('CERTIFICATES LIST', '=================')
COL_START = ('COLOR INFO LIST', '===============')
COU_START = ('COUNTRIES LIST', '==============')
DIS_START = ('DISTRIBUTORS LIST', '=================', '')
GEN_START = ('8: THE GENRES LIST', '==================', '')
KEY_START = ('8: THE KEYWORDS LIST', '====================', '')
LAN_START = ('LANGUAGE LIST', '=============')
LOC_START = ('LOCATIONS LIST', '==============', '')
MIS_START = ('MISCELLANEOUS COMPANY LIST', '==========================')
PRO_START = ('PRODUCTION COMPANIES LIST', '=========================', '')
RUN_START = ('RUNNING TIMES LIST', '==================')
SOU_START = ('SOUND-MIX LIST', '==============')
SFX_START = ('SFXCO COMPANIES LIST', '====================', '')
TCN_START = ('TECHNICAL LIST', '==============', '', '')
LSD_START = ('LASERDISC LIST', '==============', '------------------------')
LIT_START = ('LITERATURE LIST', '===============', '')
LIT_STOP = 'COPYING POLICY'
LINK_START = ('MOVIE LINKS LIST', '================', '')
MPAA_START = ('MPAA RATINGS REASONS LIST', '=========================')
PLOT_START = ('PLOT SUMMARIES LIST', '===================', '')
RELDATE_START = ('RELEASE DATES LIST', '==================')
SNDT_START = ('SOUNDTRACKS LIST', '================', '', '', '')
TAGL_START = ('TAG LINES LIST', '==============', '', '')
TAGL_STOP = '-----------------------------------------'
TRIV_START = ('FILM TRIVIA', '===========', '')
COMPCAST_START = ('CAST COVERAGE TRACKING LIST', '===========================')
COMPCREW_START = ('CREW COVERAGE TRACKING LIST', '===========================')
COMP_STOP = '---------------'


class SourceFile(GzipFile):
    """Instances of this class are used to read gzipped files,
    starting from a defined line to a (optionally) given end."""
    def __init__(self, filename=None, mode=None, start=(), stop=None,
                    *args, **kwds):
        filename = os.path.join(IMDB_PTDF_DIR, filename)
        GzipFile.__init__(self, filename, mode, *args, **kwds)
        self.start = start
        self.stop = None # Don't check for a STOP line, now.
        for item in start:
            for line in self:
                if line.startswith(item): break
        self.stop = stop

    def readline(self, size=-1):
        line = GzipFile.readline(self, size)
        if self.stop is not None and line.startswith(self.stop): return ''
        return line

    def getByHashSections(self):
        return getSectionHash(self)

    def getByNMMVSections(self):
        return getSectionNMMV(self)

def getSectionHash(fp):
    """Return sections separated by lines starting with #"""
    curSectList = []
    curTitle = ''
    for line in fp:
        if line.startswith('#'):
            if curSectList and curTitle:
                yield curTitle, ''.join(curSectList)
                curSectList[:] = []
                curTitle = ''
            curTitle = line[2:]
        else: curSectList.append(line)
    if curSectList and curTitle:
        yield curTitle, ''.join(curSectList)
        curSectList[:] = []
        curTitle = ''

def getSectionNMMV(fp):
    """Return sections separated by lines starting with 'NM: ', 'MV: ',
    'OT: ' or 'MOVI'."""
    curSectList = []
    curNMMV = ''
    for line in fp:
        if line[:4] in ('MV: ', 'NM: ', 'OT: ', 'MOVI'):
            if curSectList and curNMMV:
                yield curNMMV, ''.join(curSectList)
                curSectList[:] = []
                curNMMV = ''
            if line[:4] == 'MOVI': curNMMV = line[6:]
            else: curNMMV = line[4:]
        elif not line.startswith('-'): curSectList.append(line)
    if curSectList and curNMMV:
        yield curNMMV, ''.join(curSectList)
        curSectList[:] = []
        curNMMV = ''


class _BaseCache(dict):
    """Base class for Movie and Person basic information."""
    def __init__(self, d={}, flushEvery=18000, counterInit=1):
        dict.__init__(self)
        self.counter = counterInit
        # Flush data into the SQL database every flushEvery entries.
        self.flushEvery = flushEvery
        self._tmpDict = {}
        for k, v in d.items(): self[k] = v

    def __setitem__(self, key, value):
        """Every time a key is set, its value is discarded and substituted
        with counter; every flushEvery, the temporary dictionary is
        flushed to the database, and then zeroed."""
        if self.counter % self.flushEvery == 0:
            self.flush()
        dict.__setitem__(self, key, self.counter)
        self._tmpDict[key] = self.counter
        self.counter += 1

    def flush(self):
        """Flush to the database."""
        if self._tmpDict:
            try:
                self._toDB()
                self._tmpDict.clear()
            except OperationalError, e:
                # Dataset too large; split it in two and retry.
                if not (e and e[0] == 1153): raise OperationalError, e
                print ' * TOO MANY DATA (%s items), SPLITTING...' % \
                        len(self._tmpDict)
                c1 = self.__class__()
                c2 = self.__class__()
                newflushEvery = self.flushEvery / 2
                c1.flushEvery = newflushEvery
                c2.flushEvery = newflushEvery
                for n, (key, value) in enumerate(self._tmpDict.iteritems()):
                    if n < newflushEvery: c1._tmpDict[key] = value
                    else: c2._tmpDict[key] = value
                c1.flush()
                c2.flush()
                self._tmpDict.clear()

    def populate(self):
        """Populate the dictionary from the database."""
        raise NotImplementedError

    def _toDB(self):
        """Write the dictionary to the database."""
        raise NotImplementedError

    def add(self, key):
        """Insert a new key and return its value."""
        c = self.counter
        self[key] = None
        return c
    
    def addUnique(self, key):
        """Insert a new key and return its value; if the key is already
        in the dictionary, its previous  value is returned."""
        if self.has_key(key): return self[key]
        else: return self.add(key)


class MoviesCache(_BaseCache):
    """Manage the movies list."""
    def populate(self):
        print ' * POPULATING MoviesCache...'
        db.query('SELECT movieid, title, kind, year, imdbindex FROM titles;')
        res = db.use_result()
        x = res.fetch_row()
        while x:
            x = x[0]
            td = {'title': x[1], 'kind': x[2]}
            if x[3]: td['year'] = x[3]
            if x[4]: td['imdbIndex'] = x[4]
            title = build_title(td, canonical=1)
            dict.__setitem__(self, title, x[0])
            x = res.fetch_row()
        curs.execute('SELECT MAX(movieid) FROM titles;')
        maxid = curs.fetchall()[0][0]
        if maxid is not None: self.counter = maxid + 1
        else: self.counter = 1

    def _toDB(self):
        print ' * FLUSHING MoviesCache...'
        l = []
        lapp = l.append
        for k, v in self._tmpDict.iteritems():
            tmp = [v]
            try: t = analyze_title(k)
            except IMDbParserError: continue
            for j in ('title', 'kind', 'year', 'imdbIndex'):
                tmp.append(t.get(j))
            lapp(tmp)
        curs.executemany('INSERT INTO titles (movieid, title, kind, year, imdbindex) VALUES (%s, %s, %s, %s, %s)', l)


class PersonsCache(_BaseCache):
    """Manage the persons list."""
    def populate(self):
        print ' * POPULATING PersonsCache...'
        db.query('SELECT personid, name, imdbindex FROM names;')
        res = db.use_result()
        x = res.fetch_row()
        while x:
            x = x[0]
            nd = {'name': x[1]}
            if x[2]: nd['imdbIndex'] = x[2]
            name = build_name(nd, canonical=1)
            dict.__setitem__(self, name, x[0])
            x = res.fetch_row()
        curs.execute('SELECT MAX(personid) FROM names;')
        maxid = curs.fetchall()[0][0]
        if maxid is not None: self.counter = maxid + 1
        else: self.counter = 1
  
    def _toDB(self):
        print ' * FLUSHING PersonsCache...'
        l = []
        lapp = l.append
        for k, v in self._tmpDict.iteritems():
            tmp = [v]
            try: t = analyze_name(k)
            except IMDbParserError: continue
            for j in ('name', 'imdbIndex'):
                tmp.append(t.get(j))
            lapp(tmp)
        curs.executemany('INSERT INTO names (personid, name, imdbindex) VALUES (%s, %s, %s)', l)


class SQLData(dict):
    """Variable set of information, to be stored from time to time
    to the SQL database."""
    def __init__(self, d={}, sqlString='', flushEvery=20000, counterInit=1):
        dict.__init__(self)
        self.counterInit = counterInit
        self.counter = counterInit
        self.flushEvery = flushEvery
        self.sqlString = sqlString
        for k, v in d.items(): self[k] = v

    def __setitem__(self, key, value):
        """The value is discarded, the counter is used as the 'real' key
        and the user's 'key' is used as its values."""
        if self.counter % self.flushEvery == 0:
            self.flush()
        dict.__setitem__(self, self.counter, key)
        self.counter += 1

    def add(self, key):
        self[key] = None

    def flush(self):
        if self:
            try:
                self._toDB()
                self.clear()
                self.counter = self.counterInit
            except OperationalError, e:
                if not (e and e[0] == 1153): raise OperationalError, e
                print ' * TOO MANY DATA (%s items), SPLITTING...' % len(self)
                c1 = self.__class__()
                c2 = self.__class__()
                newflushEvery = self.flushEvery / 2
                c1.flushEvery = newflushEvery
                c2.flushEvery = newflushEvery
                c1.sqlString = self.sqlString
                c2.sqlString = self.sqlString
                for n, (key, value) in enumerate(self.iteritems()):
                    if n < newflushEvery: dict.__setitem__(c1, key, value)
                    else: dict.__setitem__(c2, key, value)
                c1.flush()
                c2.flush()
                self.clear()
                self.counter = self.counterInit

    def _toDB(self):
        print ' * FLUSHING SQLData...'
        curs.executemany(self.sqlString, self.values())


# Miscellaneous functions.

def unpack(line, headers, seps=('\t',)):
    """Given a line, split at seps and return a dictionary with key
    from the header list.
    E.g.:
        line = '      0000000124    8805   8.4  Incredibles, The (2004)'
        header = ('votes distribution', 'votes', 'rating', 'title')
        seps=('  ',)

    will returns: {'votes distribution': '0000000124', 'votes': '8805',
                    'rating': '8.4', 'title': 'Incredibles, The (2004)'}
    """
    r = {}
    ls1 = None
    ls2 = []
    for sep in seps:
        if ls1 is None:
            ls1 = line.split(sep)
        else:
            for item in ls1:
                ls2 += item.split(sep)
            ls1[:] = ls2
            ls2 = []
    ls1 = [x for x in ls1 if x]
    for index, item in enumerate(ls1):
        try: name = headers[index]
        except IndexError: name = 'item%s' % index
        r[name] = item.strip()
    return r


def _titleNote(title):
    """Split title and notes in 'Title, The (year) {note}' format."""
    rt = title
    rn = None
    sb = title.find('{')
    if sb != -1:
        eb = title.rfind('}')
        if eb > sb:
            rn = '(episode %s)' % title[sb+1:eb]
            rt = title[:sb]+title[eb+1:].strip()
    return rt, rn


def _parseMinusList(fdata):
    """Parse a list of lines starting with '- '."""
    rlist = []
    tmplist = []
    for line in fdata:
        if line.startswith('- '):
            if tmplist: rlist.append(' '.join(tmplist))
            l = line[2:].strip()
            if l: tmplist[:] = [l]
            else: tmplist[:] = []
        else:
            l = line.strip()
            if l: tmplist.append(l)
    if tmplist: rlist.append(' '.join(tmplist))
    return rlist


def _parseColonList(lines, replaceKeys):
    """Parser for lists with "TAG: value" strings."""
    out = {}
    for line in lines:
        line = line.strip()
        if not line: continue
        cols = line.split(':', 1)
        if len(cols) < 2: continue
        k = cols[0]
        k = replaceKeys.get(k, k)
        v = ' '.join(cols[1:]).strip()
        if not out.has_key(k): out[k] = []
        out[k].append(v)
    return out


# Functions used to manage data files.

def readMovieList():
    """Read the movies.list.gz file."""
    mdbf = SourceFile(MOVIES, start=MOVIES_START, stop=MOVIES_STOP)
    count = 0
    for line in mdbf:
        title = line.split('\t')[0]
        mid = CACHE_MID.addUnique(title)
        if count % 10000 == 0:
            print 'SCANNING movies: %s (movieid: %s)' % (title, mid)
        count += 1
    CACHE_MID.flush()
    mdbf.close()


def doCast(fp, roleid, rolename):
    """Populate the cast table."""
    pid = None
    count = 0
    name = ''
    sqlstr = 'INSERT INTO cast (personid, movieid, currentrole, note, nrorder, roleid) VALUES (%s, %s, %s, %s, %s, ' + str(roleid) + ')'
    sqldata = SQLData(sqlString=sqlstr)
    if rolename == 'miscellaneous crew': sqldata.flushEvery = 10000
    for line in fp:
        if line and line[0] != '\t':
            if line[0] == '\n': continue
            sl = [x for x in line.split('\t') if x]
            if len(sl) != 2: continue
            name, line = sl
            pid = CACHE_PID.addUnique(name.strip())
        line = line.strip()
        ll = line.split('  ')
        r = _titleNote(ll[0])
        title, note = _titleNote(ll[0])
        note = note or ''
        role = ''
        order = ''
        for item in ll[1:]:
            if not item: continue
            if item[0] == '[':
                role = item[1:-1]
            elif item[0] == '(':
                if note: note += ' '
                note += item
            elif item[0] == '<':
                textor = item[1:-1]
                try:
                    order = long(textor)
                except ValueError:
                    os = textor.split(',')
                    if len(os) == 3:
                        try:
                            order = ((long(os[2])-1) * 1000) + \
                                    ((long(os[1])-1) * 100) + (long(os[0])-1)
                        except ValueError:
                            pass
        movieid = CACHE_MID.addUnique(title)
        currset = (pid, movieid, role or None,
                    note or None, order or None)
        sqldata.add(currset)
        if count % 10000 == 0:
            print 'SCANNING %s: %s' % (rolename, name)
        count += 1    
    sqldata.flush()
    print 'CLOSING %s...' % rolename


def castLists():
    """Read files listed in the 'role' column of the 'roletypes' table."""
    db.query('SELECT id, role FROM roletypes;')
    res = db.store_result()
    i = res.fetch_row()
    while i:
        roleid = i[0][0]
        rolename = fname = i[0][1]
        if rolename == 'guest':
            i = res.fetch_row()
            continue
        fname = fname.replace(' ', '-')
        if fname == 'actress': fname = 'actresses.list.gz'
        elif fname == 'miscellaneous-crew': fname = 'miscellaneous.list.gz'
        else: fname = fname + 's.list.gz'
        print 'DOING', fname
        f = SourceFile(fname, start=CAST_START, stop=CAST_STOP)
        doCast(f, roleid, rolename)
        f.close()
        i = res.fetch_row()
        t('castLists(%s)' % rolename)


def doAkaNames():
    """People's akas."""
    pid = None
    count = 0
    fp = SourceFile('aka-names.list.gz', start=AKAN_START)
    sqldata = SQLData(sqlString='INSERT INTO akanames (personid, name, imdbindex) VALUES (%s, %s, %s)')
    for line in fp:
        if line and line[0] != ' ':
            if line[0] == '\n': continue
            pid = CACHE_PID.addUnique(line.strip())
        else:
            line = line.strip()
            if line[:5] == '(aka ': line = line[5:]
            if line[-1:] == ')': line = line[:-1]
            try: name = analyze_name(line)
            except IMDbParserError: continue
            sqldata.add((pid, name.get('name'), name.get('imdbIndex')))
            if count % 10000 == 0:
                print 'SCANNING akanames:', line
        count += 1
    sqldata.flush()
    fp.close()


def doAkaTitles():
    """Movies' akas."""
    mid = None
    count = 0
    fp = SourceFile('aka-titles.list.gz', start=AKAT_START)
    sqldata = SQLData(sqlString='INSERT INTO akatitles (movieid, title, imdbindex, kind, year, note) VALUES (%s, %s, %s, %s, %s, %s)', flushEvery=10000)
    for fname, start in (('aka-titles.list.gz',AKAT_START),
                         ('italian-aka-titles.list.gz',AKAT_IT_START),
                         ('german-aka-titles.list.gz',AKAT_DE_START),
                         ('iso-aka-titles.list.gz',AKAT_ISO_START)):
        fp = SourceFile(fname, start=start, stop='---------------------------')
        for line in fp:
            if line and line[0] != ' ':
                if line[0] == '\n': continue
                mid = CACHE_MID.addUnique(line.strip())
            else:
                res = unpack(line.strip(), ('title', 'note'))
                akat = res.get('title', '')
                if akat[:5] == '(aka ': akat = akat[5:]
                if akat[-2:] == '))': akat = akat[:-1]
                if count % 10000 == 0:
                    print 'SCANNING %s: %s' % \
                            (fname[:-8].replace('-', ' '), akat)
                try: akat = analyze_title(akat)
                except IMDbParserError, e: continue
                ce = (mid, akat.get('title'), akat.get('imdbIndex'),
                        akat.get('kind'), akat.get('year'), res.get('note'))
                sqldata.add(ce)
            count += 1
        sqldata.flush()
        fp.close()


def doMovieLinks():
    """Connections between movies."""
    mid = None
    count = 0
    sqldata = SQLData(sqlString='INSERT INTO movielinks (movieid, movietoid, linktypeid, note) VALUES (%s, %s, %s, %s)', flushEvery=10000)
    fp = SourceFile('movie-links.list.gz', start=LINK_START)
    onote = ''
    tonote = ''
    for line in fp:
        if line and line[0] != ' ':
            if line[0] == '\n': continue
            title, onote = _titleNote(line.strip())
            mid = CACHE_MID.addUnique(title)
            onote = onote or ''
            if count % 10000 == 0:
                print 'SCANNING movielinks:', title
        else:
            link = line.strip()
            theid = None
            for k, v in MOVIELINK_IDS:
                if link.startswith('(%s' % k):
                    theid = v
                    break
            if theid is None: continue
            totitle = link[len(k)+2:-1].strip()
            totitle, tonote = _titleNote(totitle)
            note = ''
            if onote:
                note = 'MV note: %s' % onote
            if tonote:
                if note: note += ', '
                note += 'LN note: %s' % tonote
            totitleid = CACHE_MID.addUnique(totitle)
            sqldata.add((mid, totitleid, theid, note or None))
        count += 1
    sqldata.flush()
    fp.close()


def minusHashFiles(fp, funct, defaultid, descr):
    """A file with lines starting with '# ' and '- '."""
    sqls = 'INSERT INTO moviesinfo (movieid, infoid, info, note) VALUES (%s, %s, %s, %s)'
    sqldata = SQLData(sqlString=sqls)
    sqldata.flushEvery = 2500
    if descr == 'quotes': sqldata.flushEvery = 4000
    elif descr == 'soundtracks': sqldata.flushEvery = 3000
    elif descr == 'trivia': sqldata.flushEvery = 3000
    count = 0
    for title, text in fp.getByHashSections():
        title = title.strip()
        title, note = _titleNote(title)
        d = funct(text.split('\n'))
        mid = CACHE_MID.addUnique(title)
        if count % 10000 == 0:
            print 'SCANNING %s: %s' % (descr, title)
        for data in d:
            sqldata.add((mid, defaultid, data, note))
        count += 1
    sqldata.flush()


def doMinusHashFiles():
    """Files with lines starting with '# ' and '- '."""
    for fname, start in [('alternate versions',AV_START),
                         ('goofs',GOOFS_START), ('crazy credits',CC_START),
                         ('quotes',QUOTES_START),
                         ('soundtracks',SNDT_START),
                         ('trivia',TRIV_START)]:
        fp = SourceFile(fname.replace(' ', '-')+'.list.gz', start=start,
                        stop=MINHASH_STOP)
        funct = _parseMinusList
        if fname == 'quotes': funct = getQuotes
        index = fname
        if index == 'soundtracks': index = 'soundtrack'
        minusHashFiles(fp, funct, INFO_TYPES[index], fname)
        fp.close()


def getTaglines():
    """Movie's taglines."""
    fp = SourceFile('taglines.list.gz', start=TAGL_START, stop=TAGL_STOP)
    sqls = 'INSERT INTO moviesinfo (movieid, infoid, info, note) VALUES (%s, %s, %s, %s)'
    sqldata = SQLData(sqlString=sqls, flushEvery=10000)
    count = 0
    for title, text in fp.getByHashSections():
        title = title.strip()
        title, note = _titleNote(title)
        mid = CACHE_MID.addUnique(title)
        for tag in text.split('\n'):
            tag = tag.strip()
            if not tag: continue
            if count % 10000 == 0:
                print 'SCANNING taglines:', title
            sqldata.add((mid, INFO_TYPES['taglines'], tag, note))
            count += 1
    sqldata.flush()
    fp.close()
        

def getQuotes(lines):
    """Movie's quotes."""
    quotes = []
    qttl = []
    for line in lines:
        if line.startswith('  ') and qttl and qttl[-1] and \
                not qttl[-1].endswith('::'):
            line = line.lstrip()
            if line: qttl[-1] += ' %s' % line
        elif not line.strip():
            if qttl: quotes.append('::'.join(qttl))
            qttl[:] = []
        else:
            line = line.lstrip()
            if line: qttl.append(line)
    if qttl: quotes.append('::'.join(qttl))
    return quotes


def getBusiness(lines):
    """Movie's business information."""
    bd = _parseColonList(lines, _bus)
    for k in bd.keys():
        nv = []
        for v in bd[k]:
            v = v.replace('USD ', '$').replace('GBP ', '£').replace('EUR', '€')
            nv.append(v)
        bd[k] = nv
    return bd


def getLaserDisc(lines):
    """Laserdisc information."""
    d = _parseColonList(lines, _ldk)
    for k, v in d.iteritems():
        d[k] = ' '.join(v)
    return d


def getLiterature(lines):
    """Movie's literature information."""
    return _parseColonList(lines, _lit)


_mpaa = {'RE': 'mpaa'}
def getMPAA(lines):
    """Movie's mpaa information."""
    d = _parseColonList(lines, _mpaa)
    for k, v in d.iteritems():
        d[k] = ' '.join(v)
    return d


def nmmvFiles(fp, funct, fname):
    """Files with sections separated by 'MV: ' or 'NM: '."""
    count = 0
    sqlsP = 'INSERT INTO personsinfo (personid, infoid, info, note) VALUES (%s, %s, %s, %s)'
    sqlsM = 'INSERT INTO moviesinfo (movieid, infoid, info, note) VALUES (%s, %s, %s, %s)'
    if fname == 'biographies.list.gz':
        datakind = 'person'
        sqls = sqlsP
        curs.execute('SELECT id FROM roletypes WHERE role = "guest";')
        guestid = curs.fetchone()[0]
        guestdata = SQLData(sqlString='INSERT INTO cast (personid, movieid, currentrole, note, roleid) VALUES (%s, %s, %s, %s, ' + str(guestid) + ')')
        guestdata.flushEvery = 10000
        akanamesdata = SQLData(sqlString='INSERT INTO akanames (personid, name, imdbindex) VALUES (%s, %s, %s)')
    else:
        datakind = 'movie'
        sqls = sqlsM
        guestdata = None
        akanamesdata = None
    sqldata = SQLData(sqlString=sqls)
    if fname == 'plot.list.gz': sqldata.flushEvery = 1000
    elif fname == 'literature.list.gz': sqldata.flushEvery = 5000
    elif fname == 'business.list.gz': sqldata.flushEvery = 10000
    elif fname == 'biographies.list.gz': sqldata.flushEvery = 5000
    _ltype = type([])
    for ton, text in fp.getByNMMVSections():
        ton = ton.strip()
        if not ton: continue
        note = None
        if datakind == 'movie':
            ton, note = _titleNote(ton)
            mopid = CACHE_MID.addUnique(ton)
        else: mopid = CACHE_PID.addUnique(ton)
        if count % 10000 == 0:
            print 'SCANNING %s: %s' % (fname[:-8].replace('-', ' '), ton)
        d = funct(text.split('\n'))
        for k, v in d.iteritems():
            if k != 'notable tv guest appearances':
                theid = INFO_TYPES.get(k)
                if theid is None:
                    print 'WARNING key "%s" of ton "%s" not in INFO_TYPES' % \
                                (k, ton)
                    continue
            if type(v) is _ltype:
                for i in v:
                    if k == 'notable tv guest appearances':
                        # Put "guest" information in the cast table.
                        title = i.get('long imdb canonical title')
                        if not title: continue
                        movieid = CACHE_MID.addUnique(title)
                        guestdata.add((mopid, movieid, i.currentRole or None,
                                        i.notes or None))
                        continue
                    if k in ('plot', 'mini biography'):
                        s = i.split('::')
                        if len(s) == 2:
                            if note: note += ' '
                            note = '(author: %s)' % s[0]
                            i = s[1]
                    if i: sqldata.add((mopid, theid, i, note))
                    note = None
            else:
                if v: sqldata.add((mopid, theid, v, note))
            if k in ('nick names', 'birth name') and v:
                # Put also the birth name/nick names in the list of aliases.
                if k == 'birth name': realnames = [v]
                else: realnames = v
                for realname in realnames:
                    imdbIndex = re_nameImdbIndex.findall(realname) or None
                    if imdbIndex:
                        imdbIndex = imdbIndex[0]
                        realname = re_nameImdbIndex.sub('', realname)
                    # Strip misc notes.
                    fpi = realname.find('(')
                    if fpi != -1:
                        lpi = realname.rfind(')')
                        if lpi != -1:
                            realname = '%s %s' % (realname[:fpi].strip(),
                                                    realname[lpi:].strip())
                            realname = realname.strip()
                    if realname:
                        # XXX: check for duplicates?
                        #if k == 'birth name':
                        #    realname = canonicalName(realname)
                        #else:
                        #    realname = normalizeName(realname)
                        akanamesdata.add((mopid, realname, imdbIndex))
        count += 1
    if guestdata is not None: guestdata.flush()
    if akanamesdata is not None: akanamesdata.flush()
    sqldata.flush()


def doNMMVFiles():
    """Files with large sections, about movies and persons."""
    for fname, start, funct in [('biographies.list.gz',BIO_START,_parseBiography),
            ('business.list.gz',BUS_START,getBusiness),
            ('laserdisc.list.gz',LSD_START,getLaserDisc),
            ('literature.list.gz',LIT_START,getLiterature),
            ('mpaa-ratings-reasons.list.gz',MPAA_START,getMPAA),
            ('plot.list.gz',PLOT_START,getPlot)]:
    #for fname, start, funct in [('business.list.gz',BUS_START,getBusiness)]:
        fp = SourceFile(fname, start=start)
        if fname == 'literature.list.gz': fp.stop = LIT_STOP
        elif fname == 'business.list.gz': fp.stop = BUS_STOP
        nmmvFiles(fp, funct, fname)
        fp.close()
        t('doNMMVFiles(%s)' % fname[:-8].replace('-', ' '))


def doMiscMovieInfo():
    """Files with information on a single line about movies."""
    sqldata = SQLData(sqlString='INSERT INTO moviesinfo (movieid, infoid, info, note) VALUES (%s, %s, %s, %s)')
    for dataf in (('certificates.list.gz',CER_START),
                    ('color-info.list.gz',COL_START),
                    ('countries.list.gz',COU_START),
                    ('distributors.list.gz',DIS_START),
                    ('genres.list.gz',GEN_START),
                    ('keywords.list.gz',KEY_START),
                    ('language.list.gz',LAN_START),
                    ('locations.list.gz',LOC_START),
                    ('miscellaneous-companies.list.gz',MIS_START),
                    ('production-companies.list.gz',PRO_START),
                    ('running-times.list.gz',RUN_START),
                    ('sound-mix.list.gz',SOU_START),
                    ('special-effects-companies.list.gz',SFX_START),
                    ('technical.list.gz',TCN_START),
                    ('release-dates.list.gz',RELDATE_START)):
        fp = SourceFile(dataf[0], start=dataf[1])
        typeindex = dataf[0][:-8].replace('-', ' ')
        if typeindex == 'running times': typeindex = 'runtimes'
        elif typeindex == 'technical': typeindex = 'tech info'
        elif typeindex == 'language': typeindex = 'languages'
        infoid =  INFO_TYPES[typeindex]
        count = 0
        if dataf[0] in ('distributors.list.gz', 'locations.list.gz',
                        'miscellaneous-companies.list.gz'):
            sqldata.flushEvery = 10000
        else:
            sqldata.flushEvery = 20000
        for line in fp:
            data = unpack(line.strip(), ('title', 'info', 'note'))
            if not data.has_key('title'): continue
            if not data.has_key('info'): continue
            title, note = _titleNote(data['title'])
            mid = CACHE_MID.addUnique(title)
            if data.has_key('note'):
                if note:
                    note += ' '
                    note += data['note']
                else:
                    note = data['note']
            if count % 10000 == 0:
                print 'SCANNING %s: %s' % (dataf[0][:-8].replace('-', ' '),
                                                data['title'])
            sqldata.add((mid, infoid, data['info'], note))
            count += 1
        sqldata.flush()
        fp.close()
        t('doMiscMovieInfo(%s)' % dataf[0][:-8].replace('-', ' '))
        

def getRating():
    """Movie's rating."""
    fp = SourceFile('ratings.list.gz', start=RAT_START, stop=RAT_STOP)
    sqldata = SQLData(sqlString='INSERT INTO moviesinfo (movieid, infoid, info) VALUES (%s, %s, %s)')
    count = 0
    for line in fp:
        data = unpack(line, ('votes distribution', 'votes', 'rating', 'title'),
                        seps=('  ',))
        if not data.has_key('title'): continue
        title = data['title'].strip()
        mid = CACHE_MID.addUnique(title)
        if count % 10000 == 0:
                print 'SCANNING rating:', title
        sqldata.add((mid, INFO_TYPES['votes distribution'],
                    data.get('votes distribution')))
        sqldata.add((mid, INFO_TYPES['votes'], data.get('votes')))
        sqldata.add((mid, INFO_TYPES['rating'], data.get('rating')))
        count += 1
    sqldata.flush()
    fp.close()


def getTopBottomRating():
    """Movie's rating, scanning for top 250 and bottom 100."""
    for what in ('top 250 rank', 'bottom 10 rank'):
        if what == 'top 250 rank': st = RAT_TOP250_START
        else: st = RAT_BOT10_START
        fp = SourceFile('ratings.list.gz', start=st, stop=TOPBOT_STOP)
        sqldata = SQLData(sqlString='INSERT INTO moviesinfo (movieid, infoid, info) VALUES (%s, ' + str(INFO_TYPES[what]) + ', %s)')
        count = 1
        print 'SCANNING %s...' % what
        for line in fp:
            data = unpack(line, ('votes distribution', 'votes', 'rank',
                            'title'), seps=('  ',))
            if not data.has_key('title'): continue
            title = data['title'].strip()
            mid = CACHE_MID.addUnique(title)
            if what == 'top 250 rank': rank = count
            else: rank = 11 - count
            sqldata.add((mid, rank))
            count += 1
        sqldata.flush()
        fp.close()


def getPlot(lines):
    """Movie's plot."""
    plotl = []
    plotltmp = []
    for line in lines:
        if line.startswith('PL: '):
            plotltmp.append(line[4:])
        elif line.startswith('BY: '):
            plotl.append('%s::%s' % (line[4:].strip(), ' '.join(plotltmp)))
            plotltmp[:] = []
    return {'plot': plotl}


def completeCast():
    """Movie's complete cast/crew information."""
    sqldata = SQLData(sqlString='INSERT INTO completecast (movieid, object, status, note) VALUES (%s, %s, %s, %s)')
    for fname, start in [('complete-cast.list.gz',COMPCAST_START),
                        ('complete-crew.list.gz',COMPCREW_START)]:
        fp = SourceFile(fname, start=start, stop=COMP_STOP)
        if fname == 'complete-cast.list.gz': obj = 'cast'
        else: obj = 'crew'
        count = 0
        for line in fp:
            ll = [x for x in line.split('\t') if x]
            if len(ll) != 2: continue
            title, note = _titleNote(ll[0])
            mid = CACHE_MID.addUnique(title)
            if count % 10000 == 0:
                print 'SCANNING %s: %s' % (fname[:-8].replace('-', ' '), title)
            sqldata.add((mid, obj, ll[1].lower(), note))
            count += 1
        fp.close()
    sqldata.flush()


#global instances
CACHE_MID = MoviesCache()
CACHE_PID = PersonsCache()

INFO_TYPES = {}
curs.execute('SELECT id, info FROM infotypes;')
results = curs.fetchall()
for item in results:
    INFO_TYPES[item[1]] = item[0]

def _cmpfunc(x, y):
    """Sort a list of tuples, by the length of the first item (in reverse)."""
    lx = len(x[0])
    ly = len(y[0])
    if lx > ly: return -1
    elif lx < ly: return 1
    return 0

MOVIELINK_IDS = []
curs.execute('SELECT id, type FROM linktypes;')
results = curs.fetchall()
for item in results:
    MOVIELINK_IDS.append((item[1], item[0]))
MOVIELINK_IDS.sort(_cmpfunc)


# begin the iterations...

# Populate the CACHE_MID instance.
readMovieList()
#CACHE_MID.populate()
#CACHE_PID.populate()
t('readMovieList()')

# actors, actresses, directors, ....
castLists()

doAkaNames()
t('doAkaNames()')
doAkaTitles()
t('doAkaTitles()')
doMinusHashFiles()
t('doMinusHashFiles()')
doNMMVFiles()
doMiscMovieInfo()
doMovieLinks()
t('doMovieLinks()')
getRating()
t('getRating()')
getTaglines()
t('getTaglines()')
getTopBottomRating()
t('getTopBottomRating()')
completeCast()
t('completeCast()')


# Flush caches.
CACHE_MID.flush()
CACHE_PID.flush()

print 'DONE! (in %d minutes, %d seconds)' % \
        divmod(int(time.time())-BEGIN_TIME, 60)

