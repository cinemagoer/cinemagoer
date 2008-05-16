"""
parser.local.utils module (imdb package).

This module provides miscellaneous utilities used by
the imdb.parser.local classes.

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
from sys import maxint
from struct import unpack, calcsize

from imdb._exceptions import IMDbDataAccessError


_int_type = type(0)

# List of typical binary types used in the imdb local database indexes.
POSITION = 1
BYTE = 2
TITLE_ID = 3
ATTR = 4
INT = 5
OFFSET = 6
FULL_OFFSET = 7
NAME_ID = 8
COUNT = 9
CHARACTER_ID = 10
COMPANY_ID = 11
NR_CHARACTER_ITEMS = 12
NR_COMPANY_ITEMS = 13

# The size of these binary types, in bytes.
_data_size = {POSITION: 1, BYTE: 1, INT: 2, TITLE_ID: 3, ATTR: 3,
            OFFSET: 3, NAME_ID: 3, FULL_OFFSET: 4, COUNT: 3,
            CHARACTER_ID: 3, COMPANY_ID: 3, NR_CHARACTER_ITEMS: 3,
            NR_COMPANY_ITEMS: 3}

# Groups of one or more contiguous binary types, with specific meanings.
_dataset_list = (('plot', (TITLE_ID, FULL_OFFSET)),
                ('rating', (TITLE_ID, ('s', 10), INT, BYTE)),
                ('idx2fidx', (TITLE_ID, FULL_OFFSET)),
                ('idx2idx', (TITLE_ID, OFFSET)),
                ('akatdb', (TITLE_ID, TITLE_ID, ATTR)),
                ('akandb', (NAME_ID, NAME_ID)),
                ('akatidx', (TITLE_ID, TITLE_ID)),
                ('akanidx', (NAME_ID, NAME_ID)),
                ('personID', (NAME_ID,)),
                ('movieID', (TITLE_ID,)),
                ('characterID', (CHARACTER_ID,)),
                ('companyID', (COMPANY_ID,)),
                ('attrID', (ATTR,)),
                ('position', (POSITION,)),
                ('fulloffset', (FULL_OFFSET,)),
                ('filmcount', (COUNT,)),
                ('length', (BYTE,)),
                ('longlength', (INT,)),
                ('nrCharacterItems', (NR_CHARACTER_ITEMS,)),
                ('nrCompanyItems', (NR_COMPANY_ITEMS,)),
                ('orderset', (BYTE, BYTE, BYTE)),
                ('mlinks', (TITLE_ID, BYTE, TITLE_ID)),
                ('moviedata', (TITLE_ID, INT, INT, ATTR)))

def _buildStruct(items):
    """Build a tuple of ('struct_string', struct_size, struct_items)."""
    res_l = []
    for item in items:
        # If the entry is expressed with an integer, it will be read
        # from a char.
        if type(item) is _int_type:
            length = _data_size.get(item, 0)
            item = 's'
        else:
            item, length = item
        res_l.append('%s%s' % (length, item))
    res_struct = ' '.join(res_l)
    return res_struct, calcsize(res_struct), items

# Indexes in the dataset_dict.
STRUCT_STR = 0
STRUCT_SIZE = 1
STRUCT_ITEMS = 2
# The dictionary used to recover information about data sets.
dataset_dict = dict([(kind, _buildStruct(dset))
                    for kind, dset in _dataset_list])


def _buildChrIntsList(length):
    """Build a list of dictionaries with 256 keys, one for every
    char in range 0-255 with the value set to its integer (or long)
    value to the power of i, where i is the index in the
    resulting list."""
    chi = []
    for j in xrange(length):
        chi.append({})
        for count in xrange(256):
            val = count << j*8L
            if val <= maxint: val = int(val)
            chi[j][chr(count)] = val
    return chi

_chr_ints = _buildChrIntsList(4)

# XXX: using the values in pre-built _chr_ints list is
#      equivalent - but faster - than using this function:
#def _StoL(s):
#    """Convert the string s to an integer value."""
#    data = 0L
#    for i in xrange(len(s)):
#        data |= ord(s[i]) << i*8L
#    return data


# FIXME: it's slow!  use _only_ the unpack function.
def convBin(s, kind):
    """Convert the string s in a tuple where int/long values
    are converted, while other types are left untouched.
    The number of items in the tuple depends on the structure
    specified with the kind argument.

    If the result contains a single elements, this is returned
    instead of the tuple."""
    kentry = dataset_dict[kind]
    out = unpack(kentry[STRUCT_STR], s)
    res = []
    app = res.append
    for i in xrange(len(out)):
        datum = out[i]
        if type(kentry[STRUCT_ITEMS][i]) is _int_type:
            value = 0
            for k in xrange(len(datum)):
                value |= _chr_ints[k][datum[k]]
            app(value)
        else:
            app(datum)
    if len(res) == 1: return res[0]
    return res


# FIXME: it's slow!  A better (a _real_!) algorithm is required!
def getFullIndex(fname, key, kind='idx2fidx', index=0, rindex=1,
                default=None, multi=0, mode='rb'):
    """Search fname (which contains data in the kind format),
    for key at the given index, returning the rindex or default
    if key is not found.  The file is opened in mode mode; if
    multi is set, it returns a list of entries where key matches;
    if rindex is None, the whole structure is returned.

    It's basically used to convert from an offset (TITLE_ID or
    NAME_ID) to a FULL_OFFSET."""
    try:
        fptr = open(fname, mode)
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    fread = fptr.read
    fseek = fptr.seek
    rsize = dataset_dict[kind][STRUCT_SIZE]
    curpos = 1L * key * rsize
    fsize = stat(fname)[ST_SIZE]
    multires = []
    if curpos >= (fsize - rsize):
        curpos = fsize - (rsize * 100L)
        if curpos < rsize: curpos = 0
    # Try to seek at a point where checkdata is lower
    # than the searched key.
    while 1:
        if curpos < rsize:
            curpos = 0
            break
        fseek(curpos)
        rdata = convBin(fread(rsize), kind)
        checkdata = rdata[index]
        if checkdata > key: curpos -= rsize * 1000L
        elif checkdata < key: break
        elif checkdata == key:
            if not multi:
                fptr.close()
                if rindex is None: return rdata
                else: return rdata[rindex]
            else:
                curpos -= rsize * 50L
    fseek(curpos)
    # Try to seek nearer the key we're searching.
    while 1:
        newpos = curpos + (rsize * 500L)
        if newpos >= fsize - rsize: break
        fseek(newpos)
        bdata = fread(rsize)
        if len(bdata) != rsize: break
        checkdata = convBin(bdata, kind)[index]
        if checkdata >= key: break
        curpos = newpos
    fseek(curpos)
    # Read every entry until the key value is found.
    while 1:
        bdata = fread(rsize)
        if len(bdata) != rsize: break
        rdata = convBin(bdata, kind)
        checkdata = rdata[index]
        if checkdata == key:
            if not multi:
                fptr.close()
                if rindex is None: return rdata
                else: return rdata[rindex]
            else:
                if rindex is None: multires.append(rdata)
                else: multires.append(rdata[rindex])
        elif checkdata > key: break
    fptr.close()
    return multires or default


def getRawData(dataF, offset, doCast=0, doWriters=0):
    """Collect data from the '.data' file dataF, reading the
    entry at offset; if doCast or doWriters are set, the related
    information are read.
    Return the personID and a list of dictionaries (of movieID and
    various other attributes) he worked in."""
    try:
        fptr = open(dataF, 'rb')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    fread = fptr.read
    fptr.seek(offset)
    piddata = fread(3)
    if len(piddata) != 3:
        fptr.close()
        return (None, ())
    personID = convBin(piddata, 'personID')
    filmcount = convBin(fread(3), 'filmcount')
    noWith = (filmcount >> 12) & 4095
    noWithout = filmcount & 4095
    resList = []
    resapp = resList.append
    for i in xrange(noWith):
        tmpd = {}
        movieID = convBin(fread(3), 'movieID')
        tmpd['movieID'] = movieID
        attrID = convBin(fread(3), 'attrID')
        tmpd['attributeID'] = attrID
        if doCast:
            length = convBin(fread(1), 'length')
            if length > 0:
                tmpd['currentRole'] = latin2utf(fread(length))
            tmpd['position'] = convBin(fread(1), 'position')
        if doWriters:
            orderset = convBin(fread(3), 'orderset')
            try:
                tmpd['position'] = orderset[2]*1000 + orderset[1]*100 + \
                                    orderset[0]
            except TypeError:
                pass
        resapp(tmpd)
    for i in xrange(noWithout):
        movieID = convBin(fread(3), 'movieID')
        tmpd = {'movieID': movieID}
        if doCast:
            length = convBin(fread(1), 'length')
            if length > 0:
                tmpd['currentRole'] = latin2utf(fread(length))
            tmpd['position'] = convBin(fread(1), 'position')
        if doWriters:
            orderset = convBin(fread(3), 'orderset')
            try:
                tmpd['position'] = orderset[2]*1000 + orderset[1]*100 + \
                                    orderset[0]
            except TypeError:
                pass
        resapp(tmpd)
    fptr.close()
    return personID, resList


def getLabel(ind, indexF, keyF):
    """Return the person name or movie title for the personID or
    movieID ind, searching the indexF and keyF files."""
    try:
        ifile = open(indexF, 'rb')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    ifile.seek(4L*ind)
    fodata = ifile.read(4)
    if len(fodata) != 4:
        ifile.close()
        return None
    idx = convBin(fodata, 'fulloffset')
    try:
        kfile = open(keyF, 'rt')
    except IOError, e:
        raise IMDbDataAccessError, str(e)
    kfile.seek(idx)
    line = kfile.readline().split('|')
    ifile.close()
    kfile.close()
    if line: return latin2utf(line[0])
    return None


class KeyFScan:
    """Create an index for the entries in the given file."""
    def __init__(self, keyF, granularity=1000):
        """Scan lines in keyF and create an index with granularity-1 entries.
        """
        posdb = []
        posdbapp = posdb.append
        self.keyF = keyF
        self.granularity = granularity
        try:
            kfile = open(keyF, 'rt')
        except IOError, e:
            raise IMDbDataAccessError, str(e)
        kfilesize = stat(keyF)[ST_SIZE]
        step = divmod(kfilesize, granularity)[0]
        for i in xrange(1, granularity):
            kfile.seek(step*i)
            kfile.readline()
            pos = kfile.tell()
            ton = latin2utf(kfile.readline().split('|')[0])
            posdbapp((ton.lower(), pos))
        kfile.close()
        self.posdb = posdb

    def getID(self, ton):
        """Return the ID for the given name or title or None if not found."""
        ton = ton.lower()
        cpos = 0
        for dbTon, dbPos in self.posdb:
            if ton <= dbTon: break
            cpos = dbPos
        try:
            kfile = open(self.keyF, 'rt')
        except IOError, e:
            raise IMDbDataAccessError, str(e)
        kfile.seek(cpos)
        line = kfile.readline()
        while line:
            curTon, curID = line.split('|')
            curTon = latin2utf(curTon.lower())
            if ton == curTon:
                kfile.close()
                return long(curID, 16)
            elif ton < curTon:
                kfile.close()
                return None
            line = kfile.readline()
        kfile.close()
        return None


def latin2utf(s):
    """Convert a latin_1 string to unicode."""
    return unicode(s, 'latin_1', 'replace')


