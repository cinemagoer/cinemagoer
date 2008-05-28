#!/usr/bin/env python
"""
misc-companies4local.py script.

This script creates some files to access miscellaneous companies'
information from the 'local' data access system.

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



import os
import sys
from array import array
from gzip import GzipFile
from struct import pack
from itertools import izip, chain

HELP = """misc-companies4local.py usage:
    %s /directory/with/plain/text/data/files/ /directory/with/local/files/

        # NOTE: you need read and write access to the second directory.
""" % sys.argv[0]

if len(sys.argv) != 3:
    print 'Specify both source and target directories!'
    print HELP
    sys.exit(1)

# Directory containing the IMDb's Plain Text Data Files.
IMDB_PTDF_DIR = sys.argv[1]
LOCAL_DATA_DIR = sys.argv[2]


MISC_START = ('MISCELLANEOUS COMPANY LIST', '==========================')
MISC_COMP_FILE = 'miscellaneous-companies.list.gz'
MISC_COMP_IDX = 'miscellaneous-companies.index'
MISC_COMP_KEY = 'miscellaneous-companies.key'
MISC_COMP_DATA = 'miscellaneous-companies.data'
MISC_STOP = '---------------'
TITLES_KEY_FILE = 'titles.key'
ATTRS_KEY_FILE = 'attributes.key'
ATTRS_IDX_FILE = 'attributes.index'

GzipFileRL = GzipFile.readline
class SourceFile(GzipFile):
    """Instances of this class are used to read gzipped files,
    starting from a defined line to a (optionally) given end."""
    def __init__(self, filename=None, mode=None, start=(), stop=None,
                    pwarning=1, *args, **kwds):
        filename = os.path.join(IMDB_PTDF_DIR, filename)
        try:
            GzipFile.__init__(self, filename, mode, *args, **kwds)
        except IOError, e:
            if not pwarning: raise
            print 'WARNING WARNING WARNING'
            print 'WARNING unable to read the "%s" file.' % filename
            print 'WARNING The file will be skipped, and the contained'
            print 'WARNING information will NOT be stored in the database.'
            print 'WARNING Complete error: ', e
            # re-raise the exception.
            raise
        self.start = start
        for item in start:
            itemlen = len(item)
            for line in self:
                if line[:itemlen] == item: break
        self.set_stop(stop)

    def set_stop(self, stop):
        if stop is not None:
            self.stop = stop
            self.stoplen = len(self.stop)
            self.readline = self.readline_checkEnd
        else:
            self.readline = self.readline_NOcheckEnd

    def readline_NOcheckEnd(self, size=-1):
        line = GzipFile.readline(self, size)
        return unicode(line, 'latin_1').encode('utf_8')

    def readline_checkEnd(self, size=-1):
        line = GzipFile.readline(self, size)
        if self.stop is not None and line[:self.stoplen] == self.stop: return ''
        return line
        ##return unicode(line, 'latin_1').encode('utf_8')


def getIDs(keyFile):
    """Return a dictionary mapping values to IDs, as taken from a .key
    plain text data file."""
    theDict = {}
    dataF = open(os.path.join(LOCAL_DATA_DIR, keyFile), 'r')
    for line in dataF:
        lsplit = line.split('|')
        if len(lsplit) != 2:
            continue
        data, idHex = lsplit
        theDict[data] = int(idHex, 16)
    dataF.close()
    return theDict


def toBin3(v):
    """Return a string (little-endian) from a numeric value."""
    return '%s%s%s' % (chr(v & 255), chr((v >> 8) & 255), chr((v >> 16) & 255))


def doMiscCompanies(MOVIE_IDS, ATTR_IDS):
    """Scan the miscellaneous-companies.list.gz file, creates the
    miscellaneous-companies.(index|data) files and updates the
    attributes.(index|key) files."""
    MOVIE_IDSget = MOVIE_IDS.get
    ATTR_IDSget = ATTR_IDS.get
    AUX_ATTR_IDS = {}
    AUX_ATTR_IDSget = AUX_ATTR_IDS.get
    currAttrID = len(ATTR_IDS)
    COMPANIES_IDS = {}
    COMPANIES_IDSget = COMPANIES_IDS.get
    AUX_MOVIE_IDS = {}
    AUX_MOVIE_IDSpop = AUX_MOVIE_IDS.pop
    currCompanyID = 0

    print 'INFO: The first attributeID used will be %d.' % currAttrID

    print 'Reading the miscellaneous-companies.list.gz file...',
    sys.stdout.flush()
    miscCompF = SourceFile(os.path.join(IMDB_PTDF_DIR, MISC_COMP_FILE),
                            start=MISC_START, stop=MISC_STOP)
    for line in miscCompF:
        linesplit = filter(None, line.rstrip().split('\t'))
        lslen = len(linesplit)
        if lslen == 2:
            linesplit.append('')
        elif lslen != 3:
            print 'WARN: discarding line: "%s"' % line
            continue
        movie, company, attr = linesplit
        movieID = MOVIE_IDSget(movie)
        if movieID is None:
            # Prevent some inconsistencies with movies.list.gz.
            print 'WARN: unable to find movieID for "%s"' % movie
            continue
        # First, check in the dictionary we're building: attributes
        # seem to be very specific.
        if attr:
            attrID = AUX_ATTR_IDSget(attr)
        else:
            attrID = 0xffffff
        if attrID is None:
            # Check the main list of attributes.
            attrID = ATTR_IDSget(attr)
            if attrID is None:
                attrID = currAttrID
                AUX_ATTR_IDS[attr] = attrID
                currAttrID += 1
        companyID = COMPANIES_IDSget(company)
        if companyID is None:
            companyID = currCompanyID
            COMPANIES_IDS[company] = companyID
            currCompanyID += 1
        if movieID not in AUX_MOVIE_IDS:
            # Movies to be added to the miscellaneous-companies.data file.
            AUX_MOVIE_IDS[movieID] = array('I', (companyID, attrID))
        else:
            AUX_MOVIE_IDS[movieID].extend((companyID, attrID))
    miscCompF.close()
    print 'DONE!'
    print 'INFO: %d companies, %d attributes read.' % (len(COMPANIES_IDS),
                                                        len(AUX_ATTR_IDS))
    # Invert COMPANIES_IDS dictionary.
    COMPANIES_IDS = dict(izip(COMPANIES_IDS.itervalues(),
                        COMPANIES_IDS.iterkeys()))
    # Auxiliary list used to store offsets in the fdata file.
    offsetList = []
    offsetListappend = offsetList.append
    fdata = open(os.path.join(LOCAL_DATA_DIR, MISC_COMP_DATA), 'wb')
    fdatawritelines = fdata.writelines
    fdatatell = fdata.tell
    # Create the miscellaneous-companies.data file.
    print 'Creating the miscellaneous-companies.data file...',
    sys.stdout.flush()
    for movieID in sorted(AUX_MOVIE_IDS):
        items = AUX_MOVIE_IDSpop(movieID)
        offsetListappend((movieID, fdatatell()))
        for companyID, attrID in izip(*[chain(items, [0xffffff])]*2):
            companyName = COMPANIES_IDS[companyID][:255]
            fdatawritelines((toBin3(movieID),
                            chr(len(companyName)),
                            companyName,
                            toBin3(attrID)))
    fdata.close()
    print 'DONE!'
    print 'Writing the miscellaneous-companies.index file...',
    sys.stdout.flush()
    findex = open(os.path.join(LOCAL_DATA_DIR, MISC_COMP_IDX), 'wb')
    findex.writelines('%s%s' % (toBin3(movieID), toBin3(ftell))
                        for movieID, ftell in offsetList)
    findex.close()
    print 'DONE!'
    del AUX_MOVIE_IDS
    del COMPANIES_IDS
    offsetList = []
    offsetListappend = offsetList.append
    print 'Updating the attributes.key file...',
    sys.stdout.flush()
    akeyF = open(os.path.join(LOCAL_DATA_DIR, ATTRS_KEY_FILE), 'ab')
    aidxF = open(os.path.join(LOCAL_DATA_DIR, ATTRS_IDX_FILE), 'ab')
    AUX_ATTR_IDS = dict(izip(AUX_ATTR_IDS.itervalues(),
                        AUX_ATTR_IDS.iterkeys()))
    for attrID in sorted(AUX_ATTR_IDS):
        attr = AUX_ATTR_IDS[attrID]
        offsetListappend(akeyF.tell())
        akeyF.write('%s|%x\n' % (attr, attrID))
    akeyF.close()
    print 'DONE!'
    print 'Updating the attributes.index file...',
    sys.stdout.flush()
    aidxF.writelines(pack('<L', x) for x in offsetList)
    aidxF.close()
    print 'DONE!'


if __name__ == '__main__':
    movieIDsDict = getIDs(TITLES_KEY_FILE)
    attrsIDsDict = getIDs(ATTRS_KEY_FILE)
    doMiscCompanies(movieIDsDict, attrsIDsDict)

