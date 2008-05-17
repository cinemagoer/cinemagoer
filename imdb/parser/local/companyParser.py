"""
parser.local.companyParser module (imdb package).

This module provides the functions used to parse the
information about companies in a local installation of the
IMDb database.

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

from imdb.Movie import Movie
from utils import convBin, latin2utf, getLabel
import anydbm


def getCompanyName(companyID, compIF, compDF):
    """Return the company name for the specified companyID or None."""
    try:
        ifptr = open(compIF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access companies information, '
                        'please run the companies4local.py script: %s' % e)
        return None
    ifptr.seek(4L*companyID)
    piddata = ifptr.read(4)
    ifptr.close()
    if len(piddata) != 4:
        return None
    idx = convBin(piddata, 'fulloffset')
    try:
        dfptr = open(compDF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access companies information, '
                        'please run the companies4local.py script: %s' % e)
        return None
    dfptr.seek(idx)
    # Check companyID.
    chID = dfptr.read(3)
    if companyID != convBin(chID, 'companyID'):
        return None
    length = convBin(dfptr.read(2), 'longlength')
    name = latin2utf(dfptr.read(length))
    dfptr.close()
    return name


def getCompanyFilmography(companyID, compIF, compDF, movieIF, movieKF):
    """Build a filmography list for the specified companyID."""
    try:
        ifptr = open(compIF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access companies information, '
                    'please run the companies4local.py script: %s' % e)
        return None
    ifptr.seek(4L*companyID)
    piddata = ifptr.read(4)
    ifptr.close()
    if len(piddata) != 4:
        return None
    idx = convBin(piddata, 'fulloffset')
    try:
        dfptr = open(compDF, 'rb')
    except IOError, e:
        import warnings
        warnings.warn('Unable to access companies information, '
                        'please run the companies4local.py script: %s' % e)
        return None
    dfptr.seek(idx)
    # Check companyID.
    chID = dfptr.read(3)
    if companyID != convBin(chID, 'companyID'):
        dfptr.close()
        return None
    length = convBin(dfptr.read(2), 'longlength')
    # Skip company name.
    latin2utf(dfptr.read(length))
    nrItems = convBin(dfptr.read(3), 'nrCompanyItems')
    filmography = {}
    # Yes: kindID values are hard-coded in the companies4local.py script.
    _kinds = {0: 'distributors', 1: 'production companies',
                2: 'special effect companies', 3: 'miscellaneous companies'}
    for i in xrange(nrItems):
        kind = _kinds.get(ord(dfptr.read(1)))
        if kind is None:
            import warnings
            warnings.warn('Unidentified kindID for a company.')
            break
        movieID = convBin(dfptr.read(3), 'movieID')
        title = getLabel(movieID, movieIF, movieKF)
        m = Movie(title=title, movieID=movieID, accessSystem='local')
        filmography.setdefault(kind, []).append(m)
    dfptr.close()
    return filmography


def _convChID(companyID):
    """Return a numeric value for the given string, or None."""
    if companyID is None:
        return None
    return convBin(companyID, 'companyID')


def getCompanyID(name, compNF):
    """Return a companyID for a name."""
    try:
        dbfile = anydbm.open(compNF, 'r')
    except (anydbm.error, IOError), e:
        import warnings
        warnings.warn('Unable to access companies information, '
                    'please run the companies4local.py script: %s' % e)
        return None
    chID = dbfile.get(name.encode('latin_1', 'ignore'), None)
    dbfile.close()
    return _convChID(chID)


