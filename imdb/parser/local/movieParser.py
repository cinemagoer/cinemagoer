"""
parser.local.movieParser module (imdb package).

This module provides the functions used to parse the
information about movies in a local installation of the
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

from stat import ST_SIZE
from os import stat

from imdb.Person import Person
from imdb.Movie import Movie
from imdb._exceptions import IMDbDataAccessError
from characterParser import getCharactersIDs
from utils import convBin, getRawData, getFullIndex, getLabel, latin2utf


def parseMinusList(movieID, dataF, indexF):
    """Parser for lists like goofs.data, crazy-credits.data and so on."""
    offset = getFullIndex(indexF, movieID)
    if offset is None: return []
    try:
        fdata = open(dataF, 'rt')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    fdata.seek(offset)
    fsize = stat(dataF)[ST_SIZE]
    rlist = []
    tmplist = []
    line = fdata.readline()
    while line:
        line = latin2utf(fdata.readline())
        if line.startswith('# '):
            if tmplist: rlist.append(' '.join(tmplist))
            break
        elif line.startswith('- '):
            if tmplist: rlist.append(' '.join(tmplist))
            l = line[2:].strip()
            if l: tmplist[:] = [l]
            else: tmplist[:] = []
        else:
            l = line.strip()
            if l: tmplist.append(l)
            elif fdata.tell() > fsize:
                if tmplist: rlist.append(' '.join(tmplist))
                break
    fdata.close()
    return rlist


def getMovieCast(dataF, movieID, indexF, keyF, attrIF, attrKF, offsList=[],
                charNF=None, doCast=0, doWriters=0):
    """Read the specified files and return a list of Person objects,
    one for every people in offsList."""
    resList = []
    _globoff = []
    for offset in offsList:
        # One round for person is enough.
        if offset not in _globoff: _globoff.append(offset)
        else: continue
        personID, movies = getRawData(dataF, offset, doCast, doWriters)
        # Consider only the current movie.
        movielist = [x for x in movies if x.get('movieID') == movieID]
        # XXX: a person can be listed more than one time for a single movie:
        #      think about directors of TV series.
        # XXX: here, 'movie' is a dictionary as returned by the getRawData
        #      function, not a Movie class instance.
        for movie in movielist:
            name = getLabel(personID, indexF, keyF)
            if not name: continue
            curRole = movie.get('currentRole', u'')
            roleID = None
            if curRole and charNF:
                curRole, roleID = getCharactersIDs(curRole, charNF)
            p = Person(name=name, personID=personID,
                        currentRole=curRole, roleID=roleID,
                        accessSystem='local')
            if movie.has_key('attributeID'):
                attr = getLabel(movie['attributeID'], attrIF, attrKF)
                if attr: p.notes = attr
            # Used to sort cast.
            if movie.has_key('position'):
                p.billingPos = movie['position'] or None
            resList.append(p)
    return resList


def getRatingData(movieID, ratingDF):
    """Return a dictionary with rating information."""
    rd = getFullIndex(ratingDF, movieID, kind='rating', rindex=None)
    if rd is None: return {}
    rating = {}
    rd[:] = rd[1:]
    rd[2] = rd[2] / 10.0
    rating = {'votes distribution': rd[0],
                'votes': rd[1],
                'rating': rd[2]}
    return rating


def getPlot(movieID, plotIF, plotDF):
    """Return a list of plot strings."""
    idx = getFullIndex(plotIF, movieID, 'plot')
    if idx is None: return []
    plotl = []
    plotltmp = []
    try:
        dataf = open(plotDF, 'rt')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    dataf.seek(idx)
    # Eat the first ("MV: long imdb title") line.
    dataf.readline()
    while 1:
        line = latin2utf(dataf.readline().rstrip())
        if line.startswith('PL: '):
            plotltmp.append(line[4:])
        elif line.startswith('BY: '):
            plotl.append('%s::%s' % (line[4:].strip(), ' '.join(plotltmp)))
            plotltmp[:] = []
        elif line.startswith('MV: ') or not line: break
    dataf.close()
    return plotl


def getTaglines(movieID, indexF, dataF):
    """Return a list of taglines."""
    index = getFullIndex(indexF, movieID)
    tgL = []
    if index is not None:
        try:
            tgf = open(dataF, 'rt')
        except IOError, e:
            raise IMDbDataAccessError, str(e)
        tgf.seek(index)
        tgf.readline()
        while 1:
            line = latin2utf(tgf.readline().strip())
            if not line: break
            tgL.append(line)
        tgf.close()
    return tgL


def _parseColonList(movieID, indexF, dataF, stopKey, replaceKeys):
    """Parser for lists with "COMMA: value" strings."""
    index = getFullIndex(indexF, movieID, kind='idx2idx')
    out = {}
    if index is None: return out
    try:
        fd = open(dataF, 'rt')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    fd.seek(index)
    fd.readline()
    while 1:
        line = latin2utf(fd.readline())
        if not line or line.startswith(stopKey): break
        line = line.strip()
        if not line: continue
        cols = line.split(':', 1)
        if len(cols) < 2: continue
        k = cols[0]
        k = replaceKeys.get(k, k)
        v = ' '.join(cols[1:]).strip()
        out.setdefault(k, []).append(v)
    fd.close()
    return out


_lit = {'SCRP': 'screenplay/teleplay',
        'NOVL': 'novel',
        'ADPT': 'adaption',
        'BOOK': 'book',
        'PROT': 'production process protocol',
        'IVIW': 'interviews',
        'CRIT': 'printed media reviews',
        'ESSY': 'essays',
        'OTHR': 'other literature'
}

def getLiterature(movieID, indexF, dataF):
    """Return literature information for a movie."""
    return _parseColonList(movieID, indexF, dataF, 'MOVI: ', _lit)


def getMPAA(movieID, indexF, dataF):
    """Return MPAA reason information for a movie."""
    try:
        mpaa = _parseColonList(movieID, indexF, dataF, 'MV: ', {'RE': 'mpaa'})
        if mpaa:
            mpaa = mpaa.get('mpaa', u'')
            mpaa = {'mpaa': u' '.join(mpaa)}
        else:
            mpaa = None
        return mpaa
    except IMDbDataAccessError:
        import warnings
        warnings.warn('MPAA info not accessible; please run the '
                    'mpaa4local.py script.')
        return {}


_bus = {'BT': 'budget',
        'WG': 'weekend gross',
        'GR': 'gross',
        'OW': 'opening weekend',
        'RT': 'rentals',
        'AD': 'admissions',
        'SD': 'filming dates',
        'PD': 'production dates',
        'ST': 'studios',
        'CP': 'copyright holder'
}

def getBusiness(movieID, indexF, dataF):
    """Return business information for a movie."""
    bd = _parseColonList(movieID, indexF, dataF, 'MV: ', _bus)
    for k in bd.keys():
        nv = []
        for v in bd[k]:
            v = v.replace('USD ', '$')
            v = v.replace('GBP ', u'\xa3').replace('EUR', u'\u20ac')
            nv.append(v)
        bd[k] = nv
    return bd


_ldk = {'OT': 'original title',
        'PC': 'production country',
        'YR': 'year',
        'CF': 'certification',
        'CA': 'category',
        'GR': 'group (genre)',
        'LA': 'language',
        'SU': 'subtitles',
        'LE': 'length',
        'RD': 'release date',
        'ST': 'status of availablility',
        'PR': 'official retail price',
        'RC': 'release country',
        'VS': 'video standard',
        'CO': 'color information',
        'SE': 'sound encoding',
        'DS': 'digital sound',
        'AL': 'analog left',
        'AR': 'analog right',
        'MF': 'master format',
        'PP': 'pressing plant',
        'SZ': 'disc size',
        'SI': 'number of sides',
        'DF': 'disc format',
        'PF': 'picture format',
        'AS': 'aspect ratio',
        'CC': 'close captions/teletext/ld+g',
        'CS': 'number of chapter stops',
        'QP': 'quality program',
        'IN': 'additional information',
        'SL': 'supplement',
        'RV': 'review',
        'V1': 'quality of source',
        'V2': 'contrast',
        'V3': 'color rendition',
        'V4': 'sharpness',
        'V5': 'video noise',
        'V6': 'video artifacts',
        'VQ': 'video quality',
        'A1': 'frequency response',
        'A2': 'dynamic range',
        'A3': 'spaciality',
        'A4': 'audio noise',
        'A5': 'dialogue intellegibility',
        'AQ': 'audio quality',
        'LN': 'number',
        'LB': 'label',
        'CN': 'catalog number',
        'LT': 'laserdisc title'
}

def getLaserdisc(movieID, indexF, dataF):
    """Return laserdisc information for a movie."""
    ld = _parseColonList(movieID, indexF, dataF, '--', _ldk)
    if ld and ld.has_key('original title'): del ld['original title']
    return ld


def getQuotes(movieID, dataF, indexF):
    """Return a list of quotes."""
    index = getFullIndex(indexF, movieID)
    qtL = []
    if index is not None:
        try:
            qtf = open(dataF, 'rt')
        except IOError, e:
            raise IMDbDataAccessError, str(e)
        fsize = stat(dataF)[ST_SIZE]
        qtf.seek(index)
        qtf.readline()
        qttl = []
        while 1:
            line = latin2utf(qtf.readline())
            line = line.rstrip()
            if line:
                if line.startswith('  ') and qttl[-1] and \
                        not qttl[-1].endswith('::'):
                    line = line.lstrip()
                    if line: qttl[-1] += ' %s' % line
                elif line.startswith('# '):
                    if qttl: qtL.append('::'.join(qttl))
                    break
                else:
                    line = line.lstrip()
                    if line: qttl.append(line)
            elif qttl:
                qtL.append('::'.join(qttl))
                qttl[:] = []
            elif qtf.tell() > fsize: break
        qtf.close()
    # Filter out some crap in the plain text data files.
    return [x for x in qtL if x != ':']


def getAkaTitles(movieID, akaDF, titlesIF, titlesKF, attrIF , attrKF):
    """Return a list of aka titles."""
    entries = getFullIndex(akaDF, movieID, kind='akatdb',
                        rindex=None, multi=1, default=[])
    res = []
    for entry in entries:
        akaTitle = getLabel(entry[1], titlesIF, titlesKF)
        if not akaTitle: continue
        attr = getLabel(entry[2], attrIF, attrKF)
        if attr: akaTitle += '::%s' % attr
        if akaTitle: res.append(akaTitle)
    return res


# Values for movie connections entries.
_links_sect = {
    0:  'follows',
    1:  'followed by',
    2:  'remake of',
    3:  'remade as',
    4:  'references',
    5:  'referenced in',
    6:  'spoofs',
    7:  'spoofed in',
    8:  'features',
    9:  'featured in',
    10: 'spin off from',
    11: 'spin off',
    12: 'version of',
    13: 'similar to',
    14: 'edited into',
    15: 'edited from',
    16: 'alternate language version of',
    17: 'unknown link'
}

def getMovieLinks(movieID, dataF, movieTitlIF, movieTitlKF):
    """Return a dictionary with movie connections."""
    entries = getFullIndex(dataF, movieID, kind='mlinks',
                            rindex=None, multi=1, default=[])
    res = {}
    for entry in entries:
        title = getLabel(entry[2], movieTitlIF, movieTitlKF)
        if not title: continue
        m = Movie(title=title, movieID=entry[2],
                    accessSystem='local')
        sect = _links_sect.get(entry[1])
        if not sect: continue
        res.setdefault(sect, []).append(m)
    return res


def getMovieMisc(movieID, dataF, indexF, attrIF, attrKF):
    """Return information from files like production-companies.data,
    keywords.data and so on."""
    index = getFullIndex(indexF, movieID, kind='idx2idx')
    if index is None: return []
    result = []
    try:
        fdata = open(dataF, 'rb')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    fdata.seek(index)
    # Eat the first offset.
    if len(fdata.read(3)) != 3:
        fdata.close()
        return []
    while 1:
        length = convBin(fdata.read(1), 'length')
        strval = latin2utf(fdata.read(length))
        attrid = convBin(fdata.read(3), 'attrID')
        if attrid != 0xffffff:
            attr = getLabel(attrid, attrIF, attrKF)
            if attr: strval += ' %s' % attr
        result.append(strval)
        nextBin = fdata.read(3)
        # There can be multiple values.
        if not (len(nextBin) == 3 and \
                convBin(nextBin, 'movieID') == movieID):
            break
    fdata.close()
    return result


