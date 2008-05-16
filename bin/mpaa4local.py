#!/usr/bin/env python

import os
import sys
from array import array
from gzip import GzipFile
import gzip
from struct import pack
from itertools import izip, chain

HELP = """companies4local.py usage:
    %s /directory/with/plain/text/data/files/ /directory/with/local/files/

        # NOTE: you need read and write access to the second directory.
""" % sys.argv[0]

if len(sys.argv) != 3:
    print 'Specify the target directory!'
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
    dataF = open(keyFile, 'r')
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


def doMPAA():
    MOVIE_IDS = getIDs(os.path.join(LOCAL_DATA_DIR, 'titles.key'))
    mpaaF = open(os.path.join(LOCAL_DATA_DIR, 'mpaa-ratings-reasons.data'), 'r')
    offsetList = []
    curOffset = 0L
    # NOTE: DON'T use "for line in file", since a read buffer will
    #       result in wrong tell() numbers.
    line = mpaaF.readline()
    while line:
        if not line.startswith('MV: '):
            line = mpaaF.readline()
            continue
        title = line[4:].strip()
        movieID = MOVIE_IDS.get(title)
        if movieID is None:
            print 'WARN: skipping movie %s.' % title
            line = mpaaF.readline()
            continue
        curOffset = mpaaF.tell() - len(line)
        offsetList.append((movieID, curOffset))
        line = mpaaF.readline()
    mpaaF.close()
    offsetList.sort()
    idxF = open(os.path.join(LOCAL_DATA_DIR, 'mpaa-ratings-reasons.index'),'wb')
    idxF.writelines('%s%s' % (toBin3(movieID), toBin3(ftell))
                    for movieID, ftell in offsetList)
    idxF.close()


mpaaFileGZ = gzip.open(os.path.join(IMDB_PTDF_DIR, 'mpaa-ratings-reasons.list.gz'))
mpaaFileOut = open(os.path.join(LOCAL_DATA_DIR, 'mpaa-ratings-reasons.data'), 'w')

for line in mpaaFileGZ:
    mpaaFileOut.write(line)

mpaaFileOut.close()
mpaaFileGZ.close()

doMPAA()

