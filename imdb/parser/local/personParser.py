"""
parser.local.personParser module (imdb package).

This module provides the functions used to parse the
information about people in a local installation of the
IMDb database.

Copyright 2004-2008 Davide Alberani <da@erlug.linux.it>

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

from types import UnicodeType

from imdb.Movie import Movie
from imdb._exceptions import IMDbDataAccessError
from imdb.utils import re_titleRef, analyze_name, build_name, normalizeName, \
                        date_and_notes
from characterParser import getCharactersIDs
from utils import getRawData, getLabel, getFullIndex, latin2utf


def _parseList(l, prefix, mline=1):
    """Given a list of lines l, strips prefix and join consecutive lines
    with the same prefix; if mline is True, there can be multiple info with
    the same prefix, and the first line starts with 'prefix: * '."""
    resl = []
    reslapp = resl.append
    ltmp = []
    ltmpapp = ltmp.append
    fistl = '%s: * ' % prefix
    otherl = '%s:   ' % prefix
    if not mline:
        fistl = fistl[:-2]
        otherl = otherl[:-2]
    firstlen = len(fistl)
    otherlen = len(otherl)
    parsing = 0
    joiner = ' '.join
    for line in l:
        if line[:firstlen] == fistl:
            parsing = 1
            if ltmp:
                reslapp(joiner(ltmp))
                ltmp[:] = []
            data = line[firstlen:].strip()
            if data: ltmpapp(data)
        elif mline and line[:otherlen] == otherl:
            data = line[otherlen:].strip()
            if data: ltmpapp(data)
        else:
            if ltmp:
                reslapp(joiner(ltmp))
                ltmp[:] = []
            if parsing:
                if ltmp: reslapp(joiner(ltmp))
                break
    return resl


def _buildGuests(gl):
    """Return a list of Movie objects from a list of GA lines."""
    rl = []
    rlapp = rl.append
    for g in gl:
        # When used by the imdbpy2sql.py script, latin_1 strings are passed.
        if not isinstance(g, UnicodeType):
            g = unicode(g, 'latin_1', 'replace')
        titl = re_titleRef.findall(g)
        if len(titl) != 1: continue
        note = u''
        if g[-1] == ')':
            opi = g.rfind('(episode')
            if opi == -1: opi = g.rfind('(')
            if opi != -1:
                note = g[opi:].replace('_', '"').strip()
                g = g[:opi].strip()
        cr = u''
        cri = g.find('_ (qv), as ')
        if cri != -1:
            cr = g[cri+11:].replace('[unknown]', u'').strip()
            if cr and cr[-1] == ')':
                opi = cr.rfind('(')
                if opi != -1:
                    if note: note += ' '
                    note += cr[opi:]
                    cr = cr[:opi].strip()
        # As you can see, we've no notion of the movieID, here.
        m = Movie(title=titl[0], currentRole=cr, notes=note,
                    accessSystem='local')
        rlapp(m)
    return rl

def _parseBioBy(l):
    """Return a list of biographies."""
    bios = []
    biosappend = bios.append
    tmpbio = []
    tmpbioappend = tmpbio.append
    joiner = ' '.join
    for line in l:
        if line[:4] == 'BG: ':
            tmpbioappend(line[4:].strip())
        elif line[:4] == 'BY: ':
            if tmpbio:
                biosappend(line[4:].strip() + '::' + joiner(tmpbio))
                tmpbio[:] = []
    # Cut mini biographies up to 2**16-1 chars, to prevent errors with
    # some MySQL versions - when used by the imdbpy2sql.py script.
    bios[:] = [bio[:65535] for bio in bios]
    return bios


def _parseBiography(biol):
    """Parse the biographies.data file."""
    res = {}
    bio = ' '.join(_parseList(biol, 'BG', mline=0))
    bio = _parseBioBy(biol)
    if bio: res['mini biography'] = bio

    for x in biol:
        x4 = x[:4]
        x6 = x[:6]
        if x4 == 'DB: ':
            date, notes = date_and_notes(x[4:])
            if date:
                res['birth date'] = date
            if notes:
                res['birth notes'] = notes
            #bdate = x.strip()
            #i = bdate.find(',')
            #if i != -1:
            #    res['birth notes'] = bdate[i+1:].strip()
            #    bdate = bdate[:i]
            #res['birth date'] = bdate[4:]
        elif x4 == 'DD: ':
            date, notes = date_and_notes(x[4:])
            if date:
                res['death date'] = date
            if notes:
                res['death notes'] = notes
            #ddate = x.strip()
            #i = ddate.find(',')
            #if i != -1:
            #    res['death notes'] = ddate[i+1:].strip()
            #    ddate = ddate[:i]
            #res['death date'] = ddate[4:]
        elif x6 == 'SP: * ':
            res.setdefault('spouse', []).append(x[6:].strip())
        elif x4 == 'RN: ':
            n = x[4:].strip()
            if not n: continue
            rn = build_name(analyze_name(n, canonical=1), canonical=1)
            res['birth name'] = rn
        elif x6 == 'AT: * ':
            res.setdefault('articles', []).append(x[6:].strip())
        elif x4 == 'HT: ':
            res['height'] = x[4:].strip()
        elif x6 == 'PT: * ':
            res.setdefault('pictorials', []).append(x[6:].strip())
        elif x6 == 'CV: * ':
            res.setdefault('magazine covers', []).append(x[6:].strip())
        elif x4 == 'NK: ':
            res.setdefault('nick names', []).append(normalizeName(x[4:]))
        elif x6 == 'PI: * ':
            res.setdefault('portrayed', []).append(x[6:].strip())
        elif x6 == 'SA: * ':
            sal = x[6:].strip().replace(' -> ', '::')
            res.setdefault('salary history', []).append(sal)

    trl = _parseList(biol, 'TR')
    if trl: res['trivia'] = trl
    quotes = _parseList(biol, 'QU')
    if quotes: res['quotes'] = quotes
    otherworks = _parseList(biol, 'OW')
    if otherworks: res['other works'] = otherworks
    books = _parseList(biol, 'BO')
    if books: res['books'] = books
    agent = _parseList(biol, 'AG')
    if agent: res['agent address'] = agent
    wherenow = _parseList(biol, 'WN')
    if wherenow: res['where now'] = wherenow[0]
    biomovies = _parseList(biol, 'BT')
    if biomovies: res['biographical movies'] = biomovies
    guestapp = _buildGuests([x[6:].strip() for x in biol if x[:6] == 'GA: * '])
    if guestapp: res['notable tv guest appearances'] = guestapp
    tm = _parseList(biol, 'TM')
    if tm: res['trademarks'] = tm
    interv = _parseList(biol, 'IT')
    if interv: res['interviews'] = interv
    return res


def getBio(personID, indexF, dataF):
    """Get biography information for the given person."""
    bioidx = getFullIndex(indexF, personID)
    if bioidx is None: return {}
    try:
        fbio = open(dataF, 'r')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    fbio.seek(bioidx)
    fbio.readline()
    rlines = []
    while 1:
        line = latin2utf(fbio.readline())
        if not line or line[:4] == 'NM: ': break
        rlines.append(line)
    fbio.close()
    return _parseBiography(rlines)


def getFilmography(dataF, indexF, keyF, attrIF, attrKF, offset,
                    charNF=None, doCast=0, doWriters=0):
    """Gather information from the given files about the
    person entry found at offset; return a list of Movie objects,
    with the relevant attributes."""
    name, res = getRawData(dataF, offset, doCast, doWriters)
    resList = []
    for movie in res:
        title = getLabel(movie['movieID'], indexF, keyF)
        if not title: continue
        curRole =  movie.get('currentRole', u'')
        roleID = None
        if curRole and charNF:
            curRole, roleID = getCharactersIDs(curRole, charNF)
        m = Movie(title=title, movieID=movie['movieID'],
                    currentRole=curRole, roleID=roleID,
                    accessSystem='local')
        if movie.has_key('attributeID'):
            attr = getLabel(movie['attributeID'], attrIF, attrKF)
            if attr: m.notes = attr
        resList.append(m)
    return resList


def getAkaNames(personID, akaDF, namesIF, namesKF):
    """Return a list of aka names."""
    entries = getFullIndex(akaDF, personID, kind='akandb',
                        rindex=None, multi=1, default=[])
    res = []
    for entry in entries:
        akaName = getLabel(entry[1], namesIF, namesKF)
        if akaName: res.append(akaName)
    return res


