"""
parser.local.characterParser module (imdb package).

This module provides the functions used to parse the
information about characters in a local installation of the
IMDb database.

Copyright 2007-2008 Davide Alberani <da@erlug.linux.it>

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
from utils import convBin, latin2utf, getLabel
import anydbm


def getCharacterName(characterID, charIF, charDF):
    """Return the character name for the specified characterID or None."""
    try:
        ifptr = open(charIF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access characters information, '
                        'please run the characters4local.py script: %s' % e)
        return None
    ifptr.seek(4L*characterID)
    piddata = ifptr.read(4)
    ifptr.close()
    if len(piddata) != 4:
        return None
    idx = convBin(piddata, 'fulloffset')
    try:
        dfptr = open(charDF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access characters information, '
                        'please run the characters4local.py script: %s' % e)
        return None
    dfptr.seek(idx)
    # Check characterID.
    chID = dfptr.read(3)
    if characterID != convBin(chID, 'characterID'):
        return None
    length = convBin(dfptr.read(2), 'longlength')
    name = latin2utf(dfptr.read(length))
    dfptr.close()
    return name


def getCharacterFilmography(characterID, charIF, charDF, movieIF, movieKF,
                            personIF, personKF, limit=None):
    """Build a filmography list for the specified characterID."""
    try:
        ifptr = open(charIF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access characters information, '
                    'please run the characters4local.py script: %s' % e)
        return None
    ifptr.seek(4L*characterID)
    piddata = ifptr.read(4)
    ifptr.close()
    if len(piddata) != 4:
        return None
    idx = convBin(piddata, 'fulloffset')
    try:
        dfptr = open(charDF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access characters information, '
                        'please run the characters4local.py script: %s' % e)
        return None
    dfptr.seek(idx)
    # Check characterID.
    chID = dfptr.read(3)
    if characterID != convBin(chID, 'characterID'):
        dfptr.close()
        return None
    length = convBin(dfptr.read(2), 'longlength')
    # Skip character name.
    latin2utf(dfptr.read(length))
    nrItems = convBin(dfptr.read(3), 'nrCharacterItems')
    if limit is not None and nrItems/2 > limit:
        nrItems = limit*2
    filmography = []
    for i in xrange(nrItems/2):
        personID = convBin(dfptr.read(3), 'personID')
        name = getLabel(personID, personIF, personKF)
        movieID = convBin(dfptr.read(3), 'movieID')
        title = getLabel(movieID, movieIF, movieKF)
        # XXX: notes are not retrieved: they can be found scanning
        # actors.list and acresses.list, but it will slow down everything.
        m = Movie(title=title, movieID=movieID, currentRole=name,
                    roleID=personID, roleIsPerson=True, accessSystem='local')
        filmography.append(m)
    dfptr.close()
    return filmography


def _convChID(characterID):
    """Return a numeric value for the given string, or None."""
    if characterID is None:
        return None
    return convBin(characterID, 'characterID')


def getCharactersIDs(names_string, charNF):
    """Returns a tuple (name, roleID) if the supplied string contains
    only one character, otherwise returns a tuple of lists:
    ([name1, name2, ...], [roleID1, roleID2, ...])"""
    try:
        dbfile = anydbm.open(charNF, 'r')
    except (anydbm.error, IOError), e:
        import warnings
        warnings.warn('Unable to access characters information, '
                'please run the characters4local.py script: %s' % e)
        return [names_string, None]
    names = [nm.strip() for nm in names_string.split('/')]
    chids = [_convChID(dbfile.get(nm.encode('latin_1', 'ignore'), None))
            for nm in names]
    dbfile.close()
    if len(names) == 1:
        return names[0], chids[0]
    return names, chids


