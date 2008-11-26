#!/usr/bin/env python
"""
mpaa4local.py script.

This script creates some files to access mpaa's information
from the 'local' data access system.

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
import gzip

HELP = """companies4local.py usage:
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
    """Process mpaa information."""
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
    print 'Creating the mpaa-ratings-reasons.index file...',
    idxF = open(os.path.join(LOCAL_DATA_DIR, 'mpaa-ratings-reasons.index'),'wb')
    print 'DONE!'
    idxF.writelines('%s%s' % (toBin3(movieID), toBin3(ftell))
                    for movieID, ftell in offsetList)
    idxF.close()


mpaaFileGZ = gzip.open(os.path.join(IMDB_PTDF_DIR,
                                    'mpaa-ratings-reasons.list.gz'))
print 'Creating the mpaa-ratings-reasons.data file...',
mpaaFileOut = open(os.path.join(LOCAL_DATA_DIR,
                                'mpaa-ratings-reasons.data'), 'w')

for aLine in mpaaFileGZ:
    mpaaFileOut.write(aLine)
print 'DONE!'

mpaaFileOut.close()
mpaaFileGZ.close()

doMPAA()

