"""
parser.local.personParser module (imdb package).

This module provides the functions, used to parse the
information about people in a local installation of the
IMDb database.

Copyright 2004, 2005 Davide Alberani <da@erlug.linux.it>

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

from imdb.Movie import Movie
from imdb._exceptions import IMDbDataAccessError
from utils import getRawData, getLabel, getFullIndex


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
    for line in l:
        if line.startswith(fistl):
            parsing = 1
            if ltmp:
                reslapp(' '.join(ltmp))
                ltmp[:] = []
            ltmpapp(line[firstlen:].strip())
        elif mline and line.startswith(otherl):
                ltmpapp(line[otherlen:].strip())
        else:
            if ltmp:
                reslapp(' '.join(ltmp))
                ltmp[:] = []
            if parsing:
                if ltmp: reslapp(' '.join(ltmp))
                break
    return resl


def _parseBioBy(l):
    """Return a list of biographies."""
    bios = []
    tmpbio = []
    for line in l:
        if line.startswith('BG: '):
            tmpbio.append(line[4:].strip())
        elif line.startswith('BY: '):
            if tmpbio:
                bios.append(line[4:].strip() + '::' + ' '.join(tmpbio))
                tmpbio[:] = []
    return bios


def _parseBiography(biol):
    """Parse the biographies.data file."""
    res = {}
    bio = ' '.join(_parseList(biol, 'BG', mline=0))
    bio = _parseBioBy(biol)
    if bio:
        res['mini biography'] = bio
    height = [x for x in biol if x[:4] == 'HT: ']
    if height: res['height'] = height[0][4:].strip()
    bdate = [x for x in biol if x[:4] == 'DB: ']
    if bdate:
        bdate = bdate[0].strip()
        i = bdate.find(',')
        if i != -1:
            res['birth notes'] = bdate[i+1:].strip()
            bdate = bdate[:i]
        res['birth date'] = bdate[4:]
    ddate = [x for x in biol if x[:4] == 'DD: ']
    if ddate:
        ddate = ddate[0].strip()
        i = ddate.find(',')
        if i != -1:
            res['death notes'] = ddate[i+1:].strip()
            ddate = ddate[:i]
        res['death date'] = ddate[4:]
    trl = _parseList(biol, 'TR')
    if trl: res['trivia'] = trl
    spouses = [x[6:].strip() for x in biol if x.startswith('SP: * ')]
    if spouses: res['spouse'] = spouses
    quotes = _parseList(biol, 'QU')
    if quotes: res['quotes'] = quotes
    otherworks = _parseList(biol, 'OW')
    if otherworks: res['other works'] = otherworks
    realname = [x[4:].strip() for x in biol if x.startswith('RN: ')]
    if realname: res['birth name'] = realname[0]
    sal = [x[6:].strip().replace(' -> ', '::')
            for x in biol if x.startswith('SA: * ')]
    if sal: res['salary history'] = sal
    nicks = [x[4:].strip() for x in biol if x.startswith('NK: ')]
    if nicks: res['nick names'] = nicks
    books = _parseList(biol, 'BO')
    if books: res['books'] = books
    agent = _parseList(biol, 'AG')
    if agent: res['agent address'] = agent
    biomovies = _parseList(biol, 'BT')
    if biomovies: res['biographical movies'] = biomovies
    portr = [x[6:].strip() for x in biol if x.startswith('PI: * ')]
    if portr: res['portrayed'] = portr
    guestapp = [x[6:].strip() for x in biol if x.startswith('GA: * ')]
    if guestapp: res['notable tv guest appearances'] = guestapp
    wheren = [x[6:].strip() for x in biol if x.startswith('WN: * ')]
    if wheren: res['where now'] = wheren
    tm = _parseList(biol, 'TM')
    if tm: res['trademarks'] = tm
    interv = _parseList(biol, 'IT')
    if interv: res['interviews'] = interv
    articl = [x[6:].strip() for x in biol if x.startswith('AT: * ')]
    if articl: res['articles'] = articl
    cv = [x[6:].strip() for x in biol if x.startswith('CV: * ')]
    if cv: res['magazine covers'] = cv
    pict = [x[6:].strip() for x in biol if x.startswith('PT: * ')]
    if pict: res['pictorials'] = pict
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
        line = fbio.readline()
        if not line or line.startswith('NM: '): break
        rlines.append(line)
    fbio.close()
    return _parseBiography(rlines)


def getFilmography(dataF, indexF, keyF, attrIF, attrKF, offset,
                    doCast=0, doWriters=0):
    """Gather information from the given files about the
    person entry found at offset; return a list of Movie objects,
    with the relevant attributes."""
    name, res = getRawData(dataF, offset, doCast, doWriters)
    resList = []
    for movie in res:
        title = getLabel(movie['movieID'], indexF, keyF)
        if not title: continue
        m = Movie(title=title, movieID=movie['movieID'],
                    currentRole=movie.get('currentRole', ''),
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


