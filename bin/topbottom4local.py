#!/usr/bin/env python
"""
topbottom4local.py script.

This script creates some files to access top 250/bottom 10 information
from the 'local' data access system.

Copyright 2009 Davide Alberani <da@erlug.linux.it>

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
import shelve


HELP = """topbottom4local.py usage:
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

beforeTop = 'TOP 250 MOVIES'
beforeBottom = 'BOTTOM 10 MOVIES'
beforeList = 'New'


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


print 'Reading titles.key...',
sys.stdout.flush()
MOVIEIDS = getIDs(os.path.join(LOCAL_DATA_DIR, 'titles.key'))
print 'DONE!'


def manageLine(l):
    """Extract information from a single line of the lists."""
    ls = filter(None, l.split('  '))
    if len(ls) != 4:
        return None
    distrib, votes, rating, title = ls
    distrib = unicode(distrib)
    votes = int(votes)
    rating = float(rating)
    movieID = MOVIEIDS.get(title)
    if movieID is None:
        return None
    return {'votes distribution': distrib, 'votes': votes, 'rating': rating,
            'movieID': movieID}


def getLines(fd, before):
    """Retrieve information from the lists."""
    seenFirst = False
    seenSecond = False
    lines = []
    for line in fd:
        if seenSecond:
            line = line.strip()
            if not line:
                break
            info = manageLine(line)
            if info:
                lines.append(info)
            continue
        if seenFirst:
            if line.startswith(beforeList):
                seenSecond = True
            continue
        if line.startswith(before):
            seenFirst = True
    return lines


def saveList():
    """Save information from the top/bottom lists."""
    fd = gzip.open(os.path.join(IMDB_PTDF_DIR, 'ratings.list.gz'))
    outShlv = shelve.open(os.path.join(LOCAL_DATA_DIR, 'topbottom.db'), 'n')
    print 'Saving top 250 list...',
    sys.stdout.flush()
    top = getLines(fd, beforeTop)
    outShlv['top 250 rank'] = top
    print 'DONE!'
    print 'Saving bottom 10 list...',
    sys.stdout.flush()
    fd.seek(0)
    bottom = getLines(fd, beforeBottom)
    bottom.reverse()
    outShlv['bottom 10 rank'] = bottom
    print 'DONE!'
    fd.close()
    outShlv.close()


saveList()


