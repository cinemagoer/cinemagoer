#!/usr/bin/env python
"""
companies4local.py script.

This script creates some files to access companies' information
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

import sys, os, anydbm
from struct import pack

HELP = """companies4local.py usage:
    %s /directory/with/local/files/

        # NOTE: you need read and write access to the specified directory.
                See README.companies for more information.
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


# Dictionary used to store companies information in the
# format: {'companyName': (companyID, (personID, movieID, ...))}
CACHE_CID = {}


def doCompanies(dataF, code, compCount=0):
    """Read the dataF file and populate the CACHE_CID dictionary."""
    print 'Start reading file %s.' % dataF
    try:
        fptr = open(dataF, 'rb')
    except IOError, e:
        print 'ERROR: unable to read file "%s"; skipping it: %s' % (dataF, e)
        return compCount
    fread = fptr.read
    while True:
        piddata = fread(3)
        if len(piddata) != 3:
            break
        # The movieID we're managing.
        movieID = toDec(piddata)
        length = ord(fread(1))
        curComp = fread(length)
        if curComp in CACHE_CID:
            CACHE_CID[curComp][1].append((code, movieID))
        else:
            CACHE_CID[curComp] = (compCount, [(code, movieID)])
            compCount += 1
        fread(3)
    fptr.close()
    print 'File %s closed.' % dataF
    return compCount

def counter(value=0):
    while True:
        yield value
        value += 1

def writeData(d, directory):
    """Write d data into files in the specified directory."""
    # Open files.
    print 'Start writing data to directory %s.' % directory
    comp2id = anydbm.open(os.path.join(directory, 'company2id.index'), 'n')
    findex = open(os.path.join(directory, 'companies.index'), 'wb')
    fdata = open(os.path.join(directory, 'companies.data'), 'wb')
    fdatawritelines = fdata.writelines
    fdatatell = fdata.tell
    fkey = open(os.path.join(directory, 'companies.key'), 'wb')
    # Auxiliary list used to store offsets in the fdata file.
    offsetList = []
    offsetListappend = offsetList.append
    dpopitem = d.popitem
    print 'Writing companies.key file...',
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
            name, (compID, items) = dpopitem()
        except KeyError:
            break
        d2[compID] = (name, items)
    # Probably this won't free-up any memory space, but...
    d = {}
    print 'DONE!'
    count = 1
    d2pop = d2.pop
    print 'Start writing data (this may take a while).'
    for compID in sorted(d2):
        name, items = d2pop(compID)
        offsetListappend(fdatatell())
        compIDBin = toBin3(compID)
        # Map company names to companyIDs.
        comp2id[name] = compIDBin
        fdatawritelines((compIDBin, # companyID: superfluous,
                                    # but useful for run-time checks.
                        pack('<H', len(name)), # Length of the name (2-bytes).
                        name, # Name of the company.
                        toBin3(len(items)))) # Number of 4-bytes-long items to
                                             # read.
        for kind, movieID in items:
            fdatawritelines((chr(kind), toBin3(movieID)))
        if count % 50000 == 0:
            print '* So far, %d companies were written.' % count
        count += 1
    fdata.close()
    comp2id.close()
    print 'Writing the companies.index file...',
    sys.stdout.flush()
    findex.writelines(pack('<L', x) for x in offsetList)
    findex.close()
    print 'DONE!'
    print 'Dump to directory %s complete.' % directory


lastCC = 0
for fname, code in (('distributors.data', 0),
                    ('production-companies.data', 1),
                    ('special-effects-companies.data', 2),
                    ('miscellaneous-companies.data', 3)):
    lastCC = doCompanies(os.path.join(DATA_DIR, fname), code, compCount=lastCC)

# Write output files.
writeData(CACHE_CID, DATA_DIR)


