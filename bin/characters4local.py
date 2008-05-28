#!/usr/bin/env python
"""
characters4local.py script.

This script creates some files to access characters' information
from the 'local' data access system.

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

import sys, os, anydbm
from array import array
from struct import pack

HELP = """characters4local.py usage:
    %s /directory/with/local/files/

        # NOTE: you need read and write access to the specified directory.
                See README.currentRole for more information.
""" % sys.argv[0]

if len(sys.argv) != 2:
    print 'Specify the target directory!'
    print HELP
    sys.exit(1)

DATA_DIR = sys.argv[1]


def _buildChrIntsList(length):
    """Auxiliary table for fast conversion from 3-bytes strings to integers."""
    chi = []
    for j in xrange(length):
        chi.append({})
        for count in xrange(256):
            val = count << j*8L
            if val <= sys.maxint: val = int(val)
            chi[j][chr(count)] = val
    return chi

_chr_ints = _buildChrIntsList(3)

def toDec(v):
    """"Convert string v to integer."""
    value = 0
    for i in xrange(len(v)):
        value |= _chr_ints[i][v[i]]
    return value


def toBin3(v):
    """Return a string (little-endian) from a numeric value."""
    return '%s%s%s' % (chr(v & 255), chr((v >> 8) & 255), chr((v >> 16) & 255))


# Dictionary used to store characters information in the
# format: {'characterName': (characterID, (personID, movieID, ...))}
CACHE_CID = {}


def doCast(dataF, roleCount=0):
    """Read the dataF file and populate the CACHE_CID dictionary."""
    print 'Start reading file %s.' % dataF
    fptr = open(dataF, 'rb')
    fread = fptr.read
    while True:
        piddata = fread(3)
        if len(piddata) != 3:
            break
        # The personID we're managing.
        personID = toDec(piddata)
        filmCount = toDec(fread(3))
        # Number of movies with and without attributes.
        noWith = (filmCount >> 12) & 4095
        noWithout = filmCount & 4095
        for i in xrange(noWith + noWithout):
            movieID = toDec(fread(3))
            if i < noWith:
                # Eat 'attributeID'.
                fread(3)
            try:
                length = ord(fread(1))
            except TypeError:
                # Prevent the strange case where fread(1) returns '';
                # it should not happen; maybe there's some garbage in
                # the files...
                length = 0
            if length > 0:
                curRole = fread(length)
                noterixd = curRole.rfind('(')
                if noterixd != -1:
                    # Don't strip notes, if they are not associated to
                    # the last character.
                    if curRole.rfind('/') < noterixd:
                        curRole = curRole[:noterixd]
                for role in curRole.split('/'):
                    role = role.strip()
                    if not role:
                        continue
                    if role in CACHE_CID:
                        CACHE_CID[role][1].extend((personID, movieID))
                    else:
                        CACHE_CID[role] = (roleCount,
                                            array('I', (personID, movieID)))
                        roleCount += 1
                        if roleCount % 100000 == 0:
                            print '* So far, %d characters were read.' % \
                                        roleCount
            # Eat 'position'
            fread(1)
        ##if roleCount > 70000: break
    fptr.close()
    print 'File %s closed.' % dataF
    return roleCount


def writeData(d, directory):
    """Write d data into files in the specified directory."""
    # Open files.
    print 'Start writing data to directory %s.' % directory
    char2id = anydbm.open(os.path.join(directory, 'character2id.index'), 'n')
    findex = open(os.path.join(directory, 'characters.index'), 'wb')
    fdata = open(os.path.join(directory, 'characters.data'), 'wb')
    fdatawritelines = fdata.writelines
    fdatatell = fdata.tell
    fkey = open(os.path.join(directory, 'characters.key'), 'wb')
    # Auxiliary list used to store offsets in the fdata file.
    offsetList = []
    offsetListappend = offsetList.append
    dpopitem = d.popitem
    print 'Writing characters.key file...',
    sys.stdout.flush()
    fkey.writelines('%s|%x\n' % (name, d[name][0]) for name in sorted(d))
    fkey.close()
    print 'DONE!'
    print 'Converting received dictionary...',
    sys.stdout.flush()
    # Convert the received dictionary in another format, simpler/faster
    # to process.  It's faster and requires less memory than a
    # sorted(d.iteritems(), key=operator.itemgetter(1)) call.
    d2 = {}
    while True:
        try:
            name, (charID, items) = dpopitem()
        except KeyError:
            break
        d2[charID] = (name, items)
    # Probably this won't free-up any memory space, but...
    d = {}
    print 'DONE!'
    count = 1
    d2pop = d2.pop
    print 'Start writing data (this may take a while).'
    for charID in sorted(d2):
        name, items = d2pop(charID)
        offsetListappend(fdatatell())
        charIDBin = toBin3(charID)
        # Map character names to characterIDs.
        char2id[name] = charIDBin
        fdatawritelines((charIDBin, # characterID: superfluous,
                                    # but useful for run-time checks.
                        pack('<H', len(name)), # Length of the name (2-bytes).
                        name, # Name of the character.
                        toBin3(len(items)))) # Number of 3-bytes-long items to
                                             # read; 24-bits, because some
                                             # characters (like "Himself")
                                             # appear in many movies.
        fdatawritelines(toBin3(x) for x in items)
        if count % 100000 == 0:
            print '* So far, %d characters were written.' % count
        count += 1
    fdata.close()
    char2id.close()
    print 'Writing the characters.index file...',
    sys.stdout.flush()
    findex.writelines(pack('<L', x) for x in offsetList)
    findex.close()
    print 'DONE!'
    print 'Dump to directory %s complete.' % directory


# Read actors.data.
lastRC = doCast(DATA_DIR + 'actors.data')
# Read actresses.data.
doCast(DATA_DIR + 'actresses.data', roleCount=lastRC)
# Write output files.
writeData(CACHE_CID, DATA_DIR)


