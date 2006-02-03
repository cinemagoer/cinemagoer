"""
utils module (imdb package).

This module provides basic utilities for the imdb package.

Copyright 2004-2006 Davide Alberani <da@erlug.linux.it>

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

import re
from copy import copy, deepcopy

from imdb._exceptions import IMDbParserError


# The regular expression for the "long" year format of IMDb, like
# "(1998)" and "(1986/II)", where the optional roman number (that I call
# "imdbIndex" after the slash is used for movies with the same title
# and year of release.
# XXX: probably L, C, D and M are far too much! ;-)
re_year_index = re.compile(r'\(([0-9\?]{4}(/[IVXLCDM]+)?)\)')

# Match only the imdbIndex (for name strings).
re_index = re.compile(r'^\(([IVXLCDM]+)\)$')

# Match the number of episodes.
re_episodes = re.compile('\s?\((\d+) episodes\)', re.I)

# Common suffixes in surnames.
_sname_suffixes = ('de', 'la', 'der', 'den', 'del', 'y', 'da', 'van',
                    'e', 'von', 'the', 'di', 'du', 'el', 'al')

def canonicalName(name):
    """Return the given name in canonical "Surname, Name" format.
    It assumes that name is in the 'Name Surname' format."""
    # XXX: some statistics (over 1698193 names):
    #      - just a surname:                 36614
    #      - single surname, single name:  1461621
    #      - composed surname, composed name: 6126
    #      - composed surname, single name:  44597
    #        (2: 39998, 3: 4175, 4: 356)
    #      - single surname, composed name: 149235
    #        (2: 143522, 3: 4787, 4: 681, 5: 165)
    # Don't convert names already in the canonical format.
    if name.find(', ') != -1: return name
    sname = name.split(' ')
    snl = len(sname)
    if snl == 2:
        # Just a name and a surname: how boring...
        name = '%s, %s' % (sname[1], sname[0])
    elif snl > 2:
        lsname = [x.lower() for x in sname]
        if snl == 3: _indexes = (0, snl-2)
        else: _indexes = (0, snl-2, snl-3)
        # Check for common surname prefixes at the beginning and near the end.
        for index in _indexes:
            if lsname[index] not in _sname_suffixes: continue
            try:
                # Build the surname.
                surn = '%s %s' % (sname[index], sname[index+1])
                del sname[index]
                del sname[index]
                try:
                    # Handle the "Jr." after the name.
                    if lsname[index+2].startswith('jr'):
                        surn += ' %s' % sname[index]
                        del sname[index]
                except (IndexError, ValueError):
                    pass
                name = '%s, %s' % (surn, ' '.join(sname))
                break
            except ValueError:
                continue
        else:
            name = '%s, %s' % (sname[-1], ' '.join(sname[:-1]))
    return name

def normalizeName(name):
    """Return a name in the normal "Name Surname" format."""
    sname = name.split(', ')
    if len(sname) == 2:
        name = '%s %s' % (sname[1], sname[0])
    return name

def analyze_name(name, canonical=0):
    """Return a dictionary with the name and the optional imdbIndex
    keys, from the given string.
    If canonical is true, it tries to convert the  name to
    the canonical "Surname, Name" format.
    
    raise an IMDbParserError exception if the name is not valid.
    """
    original_n = name
    name = name.strip()
    res = {}
    imdbIndex = ''
    opi = name.rfind('(')
    if opi != -1:
        cpi = name.rfind(')')
        if cpi > opi and re_index.match(name[opi:cpi+1]):
            imdbIndex = name[opi+1:cpi]
            name = name[:opi].rstrip()
    if not name:
        raise IMDbParserError, 'invalid name: "%s"' % original_n
    if canonical:
        name = canonicalName(name)
    res['name'] = name
    if imdbIndex:
        res['imdbIndex'] = imdbIndex
    return res


def build_name(name_dict, canonical=0):
    """Given a dictionary that represents a "long" IMDb name,
    return a string.
    If canonical is not set, the name is returned in the normal
    "Name Surname" format.
    """
    name = name_dict.get('name', '')
    if not canonical:
        name = normalizeName(name)
    imdbIndex = name_dict.get('imdbIndex')
    if imdbIndex:
        name += ' (%s)' % imdbIndex
    return name


# List of articles.
# XXX: are 'agapi mou' and  'liebling' articles?
# XXX: removed 'en', 'to', 'as', 'et', 'des', 'al', 'egy', 'ye', 'da'
#      and "'n" because they are more commonly used as non-articles
#      at the begin of a title.
_articles = ('the', 'la', 'a', 'die', 'der', 'le', 'el', "l'", 'il',
            'das', 'les', 'i', 'o', 'ein', 'un', 'los', 'de', 'an',
            'una', 'eine', 'las', 'den', 'gli', 'het', 'lo',
            'os', 'az', 'ha-', 'een', 'det', 'oi', 'ang', 'ta',
            'al-', 'dem', 'uno', "un'", 'ett', 'mga', u'\xcf', u'\xc7',
            'eines', 'els', u'\xd4\xef', u'\xcf\xe9')

# Articles in a dictionary.
_articlesDict = dict([(x, x) for x in _articles])
_spArticles = []
for article in _articles:
    if article[-1] not in ("'", '-'): article += ' '
    _spArticles.append(article)

def canonicalTitle(title):
    """Return the title in the canonic format 'Movie Title, The'."""
    try:
        if _articlesDict.has_key(title.split(', ')[-1].lower()): return title
    except IndexError: pass
    ltitle = title.lower()
    for article in _spArticles:
        if ltitle.startswith(article):
            lart = len(article)
            title = '%s, %s' % (title[lart:], title[:lart])
            if article[-1] == ' ': title = title[:-1]
            break
    ## XXX: an attempt using a dictionary lookup.
    ##for artSeparator in (' ', "'", '-'):
    ##    article = _articlesDict.get(ltitle.split(artSeparator)[0])
    ##    if article is not None:
    ##        lart = len(article)
    ##        # check titles like "una", "I'm Mad" and "L'abbacchio".
    ##        if title[lart:] == '' or (artSeparator != ' ' and
    ##                                title[lart:][1] != artSeparator): continue
    ##        title = '%s, %s' % (title[lart:], title[:lart])
    ##        if artSeparator == ' ': title = title[1:]
    ##        break
    return title

def normalizeTitle(title):
    """Return the title in the normal "The Title" format."""
    stitle = title.split(', ')
    if len(stitle) > 1 and _articlesDict.has_key(stitle[-1].lower()):
        sep = ' '
        if stitle[-1][-1] in ("'", '-'): sep = ''
        title = '%s%s%s' % (stitle[-1], sep, ', '.join(stitle[:-1]))
    return title


def analyze_title(title, canonical=0):
    """Analyze the given title and return a dictionary with the
    "stripped" title, the kind of the show ("movie", "tv series", etc.),
    the year of production and the optional imdbIndex (a roman number
    used to distinguish between movies with the same title and year).
    If canonical is true, the title is converted to the canonical
    format.
    
    raise an IMDbParserError exception if the title is not valid.
    """
    original_t = title
    title = title.strip()
    year = ''
    kind = ''
    imdbIndex = ''
    # First of all, search for the kind of show.
    # XXX: Number of entries at 27 jan 2005:
    #      {'(mini)': 4858, '(V)': 35501, '(VG)': 4301, '(TV)': 58443}
    #      tv series: 42454
    # XXX: more up-to-date statistics: http://us.imdb.com/database_statistics
    if title.endswith('(TV)'):
        kind = 'tv movie'
        title = title[:-4].rstrip()
    elif title.endswith('(V)'):
        kind = 'video movie'
        title = title[:-3].rstrip()
    elif title.endswith('(mini)'):
        kind = 'tv mini series'
        title = title[:-6].rstrip()
    elif title.endswith('(VG)'):
        kind = 'video game'
        title = title[:-4].rstrip()
    # Search for the year and the optional imdbIndex (a roman number).
    yi = re_year_index.findall(title)
    if yi:
        last_yi = yi[-1]
        year = last_yi[0]
        if last_yi[1]:
            imdbIndex = last_yi[1][1:]
            year = year[:-len(imdbIndex)-1]
        i = title.rfind('(%s)' % last_yi[0])
        if i != -1:
            title = title[:i-1].rstrip()
    # This is a tv (mini) series: strip the '"' at the begin and at the end.
    # XXX: strip('"') is not used for compatibility with Python 2.0.
    if title and title[0] == title[-1] == '"':
        if not kind:
            kind = 'tv series'
        title = title[1:-1].strip()
    if not title:
        raise IMDbParserError, 'invalid title: "%s"' % original_t
    if canonical:
        title = canonicalTitle(title)
    # 'kind' is one in ('movie', 'tv series', 'tv mini series', 'tv movie'
    #                   'video movie', 'video game')
    result = {'title': title, 'kind': kind or 'movie'}
    if year and year != '????':
        result['year'] = str(year)
    if imdbIndex:
        result['imdbIndex'] = str(imdbIndex)
    return result


def build_title(title_dict, canonical=0):
    """Given a dictionary that represents a "long" IMDb title,
    return a string.

    If canonical is not true, the title is returned in the
    normal format.
    """
    title = title_dict.get('title', '')
    if not canonical:
        title = normalizeTitle(title)
    kind = title_dict.get('kind')
    imdbIndex = title_dict.get('imdbIndex')
    year = title_dict.get('year', '????')
    if kind in ('tv series', 'tv mini series'):
        title = '"%s"' % title
    title += ' (%s' % year
    if imdbIndex:
        title += '/%s' % imdbIndex
    title += ')'
    if kind:
        if kind == 'tv movie':
            title += ' (TV)'
        elif kind == 'video movie':
            title += ' (V)'
        elif kind == 'tv mini series':
            title += ' (mini)'
        elif kind == 'video game':
            title += ' (VG)'
    return title


class _LastC:
    """Size matters."""
    def __cmp__(self, other):
        if isinstance(other, self.__class__): return 0
        return 1

_last = _LastC()

def sortMovies(m1, m2):
    """Sort movies by year, in reverse order; the imdbIndex is checked
    for movies with the same year of production and title."""
    m1y = int(m1.get('year', 0))
    m2y = int(m2.get('year', 0))
    if m1y > m2y: return -1
    if m1y < m2y: return 1
    # Ok, these movies have the same production year...
    m1t = m1.get('canonical title', _last)
    m2t = m2.get('canonical title', _last)
    if m1t < m2t: return -1
    if m1t > m2t: return 1
    # Ok, these movies have the same title...
    m1i = m1.get('imdbIndex', _last)
    m2i = m2.get('imdbIndex', _last)
    if m1i > m2i: return -1
    if m1i < m2i: return 1
    return 0


def sortPeople(p1, p2):
    """Sort people by billingPos, name and imdbIndex."""
    p1b = p1.billingPos
    if p1b is None: p1b = _last
    p2b = p2.billingPos
    if p2b is None: p2b = _last
    if p1b > p2b: return 1
    if p1b < p2b: return -1
    p1n = p1.get('canonical name', _last)
    p2n = p2.get('canonical name', _last)
    if p1n > p2n: return 1
    if p1n < p2n: return -1
    p1i = p1.get('imdbIndex', _last)
    p2i = p2.get('imdbIndex', _last)
    if p1i > p2i: return 1
    if p1i < p2i: return -1
    return 0


# References to titles and names.
# XXX: find better regexp!
re_titleRef = re.compile(r'_(.+?(?: \([0-9\?]{4}(?:/[IVXLCDM]+)?\))?(?: \(mini\)| \(TV\)| \(V\)| \(VG\))?)_ \(qv\)')
# FIXME: doesn't match persons with ' in the name.
re_nameRef = re.compile(r"'([^']+?)' \(qv\)")

# Functions used to filter the text strings.
def modNull(s, titlesRefs, namesRefs):
    """Do nothing."""
    return s

def modClearTitleRefs(s, titlesRefs, namesRefs):
    """Remove titles references."""
    return re_titleRef.sub(r'\1', s)

def modClearNameRefs(s, titlesRefs, namesRefs):
    """Remove names references."""
    return re_nameRef.sub(r'\1', s)

def modClearRefs(s, titlesRefs, namesRefs):
    """Remove both titles and names references."""
    s = modClearTitleRefs(s, {}, {})
    return modClearNameRefs(s, {}, {})

_stypes = (type(u''), type(''))
_ltype = type([])
_dtype = type({})
_todescend = (_ltype, _dtype)

def modifyStrings(o, modFunct, titlesRefs, namesRefs):
    """Modify a string (or string values in a dictionary or strings
    in a list), using the provided modFunct function and titlesRefs
    and namesRefs references dictionaries."""
    to = type(o)
    if to in _stypes:
        return modFunct(o, titlesRefs, namesRefs)
    elif to in _todescend:
        _stillorig = 1
        if to is _ltype: keys = xrange(len(o))
        else: keys = o.keys()
        for i in keys:
            v = o[i]
            tv = type(v)
            if tv in _stypes:
                if _stillorig:
                    o = copy(o)
                    _stillorig = 0
                o[i] = modFunct(v, titlesRefs, namesRefs)
            elif tv in _todescend:
                modifyStrings(o[i], modFunct, titlesRefs, namesRefs)
    return o


class _Container:
    """Base class for Movie and Person classes."""
     # The default sets of information retrieved.
    default_info = ()

    # Aliases for some not-so-intuitive keys.
    keys_alias = {}

    # List of keys to modify.
    keys_tomodify_list = ()

    def __init__(self, myID=None, data=None, currentRole=u'', notes=u'',
                accessSystem=None, titlesRefs=None, namesRefs=None,
                modFunct=None, *args, **kwds):
        """Initialize a Movie or a Person object.
        *myID* -- your personal identifier for this object.
        *data* -- a dictionary used to initialize the object.
        *currentRole* -- a string representing the current role or duty
                        of a person in this/a movie.
        *notes* -- notes for the person referred in the currentRole
                    attribute; e.g.: '(voice)' or the alias used in the
                    movie credits.
        *accessSystem* -- a string representing the data access system used.
        *titlesRefs* -- a dictionary with references to movies.
        *namesRefs* -- a dictionary with references to persons.
        *modFunct* -- function called returning text fields.
        """
        self.reset()
        self.myID = myID
        if data is None: data = {}
        self.set_data(data, override=1)
        self.currentRole = currentRole
        self.notes = notes
        self.accessSystem = accessSystem
        if titlesRefs is None: titlesRefs = {}
        self.update_titlesRefs(titlesRefs)
        if namesRefs is None: namesRefs = {}
        self.update_namesRefs(namesRefs)
        self.set_mod_funct(modFunct)
        self.keys_tomodify = {}
        for item in self.keys_tomodify_list:
            self.keys_tomodify[item] = None
        self._init(*args, **kwds)

    def _init(self, **kwds): pass

    def reset(self):
        """Reset the object."""
        self.data = {}
        self.myID = None
        self.currentRole = u''
        self.notes = u''
        self.titlesRefs = {}
        self.namesRefs = {}
        self.modFunct = modClearRefs
        self.current_info = []
        self._reset()

    def _reset(self): pass

    def clear(self):
        """Reset the dictionary."""
        self.data.clear()
        self.currentRole = u''
        self.notes = u''
        self.titlesRefs = {}
        self.namesRefs = {}
        self.current_info = []
        self._clear()

    def _clear(self): pass

    def get_current_info(self):
        """Return the current set of information retrieved."""
        return self.current_info

    def set_current_info(self, ci):
        """Set the current set of information retrieved."""
        self.current_info = ci

    def add_to_current_info(self, val):
        """Add a set of information to the current list."""
        if val not in self.current_info:
            self.current_info.append(val)

    def has_current_info(self, val):
        """Return true if the given set of information is in the list."""
        return val in self.current_info
    
    def set_mod_funct(self, modFunct):
        """Set the fuction used to modify the strings."""
        if modFunct is None: modFunct = modClearRefs
        self.modFunct = modFunct

    def update_titlesRefs(self, titlesRefs):
        """Update the dictionary with the references to movies."""
        self.titlesRefs.update(titlesRefs)
    
    def get_titlesRefs(self):
        """Return the dictionary with the references to movies."""
        return self.titlesRefs

    def update_namesRefs(self, namesRefs):
        """Update the dictionary with the references to names."""
        self.namesRefs.update(namesRefs)

    def get_namesRefs(self):
        """Return the dictionary with the references to names."""
        return self.namesRefs

    def set_data(self, data, override=0):
        """Set the movie data to the given dictionary; if 'override' is
        set, the previous data is removed, otherwise the two dictionary
        are merged.
        """
        if not override:
            self.data.update(data)
        else:
            self.data = data

    def __cmp__(self, other):
        """Compare two Movie or Person objects."""
        # XXX: only check the title/name and the movieID/personID?
        # XXX: comparison should be used to sort movies/person?
        if not isinstance(other, self.__class__):
            return -1
        if self.data == other.data:
            return 0
        return 1

    def __len__(self):
        return len(self.data)

    def _getitem(self, key):
        """Handle special keys."""
        return None

    def __getitem__(self, key):
        """Return the value for a given key, checking key aliases;
        a KeyError exception is raised if the key is not found.
        """
        value = self._getitem(key)
        if value is not None: return value
        # Handle key aliases.
        key = self.keys_alias.get(key, key)
        rawData = self.data[key]
        if self.keys_tomodify.has_key(key) and \
                self.modFunct not in (None, modNull):
            return modifyStrings(rawData, self.modFunct, self.titlesRefs,
                                self.namesRefs)
        return rawData

    def __setitem__(self, key, item):
        """Directly store the item with the given key."""
        self.data[key] = item

    def __delitem__(self, key):
        """Remove the given section or key."""
        # XXX: how to remove an item of a section?
        del self.data[key]

    def _additional_keys(self):
        """Valid keys to append to the data.keys() list."""
        return []

    def keys(self):
        """Return a list of valid keys."""
        return self.data.keys() + self._additional_keys()

    def items(self):
        """Return the items in the dictionary."""
        return [(k, self.get(k)) for k in self.keys()]

    # XXX: implement!
    ##def iteritems(self): return self.data.iteritems()
    ##def iterkeys(self): return self.data.iterkeys()
    ##def itervalues(self): return self.data.itervalues()

    def values(self):
        """Return the values in the dictionary."""
        return [self.get(k) for k in self.keys()]

    def has_key(self, key):
        """Return true if a given section is defined."""
        try:
            self.__getitem__(key)
        except KeyError:
            return 0
        return 1

    def update(self, dict):
        self.data.update(dict)

    def get(self, key, failobj=None):
        """Return the given section, or default if it's not found."""
        try:
            return self.__getitem__(key)
        except KeyError:
            return failobj

    def setdefault(self, key, failobj=None):
        if not self.has_key(key):
            self[key] = failobj
        return self[key]

    def pop(self, key, *args):
        return self.data.pop(key, *args)

    def popitem(self):
        return self.data.popitem()
    
    def __contains__(self, key):
        raise NotImplementedError, 'override this method'

    def append_item(self, key, item):
        """The item is appended to the list identified by the given key."""
        self.data.setdefault(key, []).append(item)

    def set_item(self, key, item):
        """Directly store the item with the given key."""
        self.data[key] = item

    def __nonzero__(self):
        """Return true if self.data contains something."""
        if self.data: return 1
        return 0

    def __deepcopy__(self, memo):
        raise NotImplementedError, 'override this method'

    def copy(self):
        """Return a deep copy of the object itself."""
        return deepcopy(self)


