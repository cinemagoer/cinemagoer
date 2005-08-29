"""
parser.http.utils module (imdb package).

This module provides miscellaneous utilities used by
the imdb.parser.http classes.

Copyright 2004, 2005 Davide Alberani <da@erlug.linux.it>

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
from htmllib import HTMLParser
from formatter import NullFormatter

from imdb._exceptions import IMDbParserError

from imdb.Movie import Movie
from imdb.Person import Person

# Year, imdbIndex and kind.
re_yearKind_index = re.compile(r'(\([0-9\?]{4}(?:/[IVXLCDM]+)?\)(?: \(mini\)| \(TV\)| \(V\)| \(VG\))?)')

_ltype = type([])
_dtype = type({})
_stypes = (type(''), type(u''))
_destypes = (_ltype, _dtype)

def _subRefs(s, titlesL, namesL):
    """Replace titles in titlesL and names in namesL with
    their '(qv) versions' in the string s."""
    for title in titlesL:
        if s.find(title) != -1:
            s = s.replace(title, '_%s_ (qv)' % title)
    for name in namesL:
        if s.find(name) != -1:
            s = s.replace(name, "'%s' (qv)" % name)
    return s


def _putRefs(d, titlesL, namesL):
    """Iterate over the strings inside list items or dictionary values,
    and call _subRefs()."""
    td = type(d)
    if td is _ltype:
        for i in xrange(len(d)):
            ti = type(d[i])
            if ti in _stypes:
                d[i] = _subRefs(d[i], titlesL, namesL)
            elif ti in _destypes:
                _putRefs(d[i], titlesL, namesL)
    elif td is _dtype:
        for k, v in d.items():
            tv = type(v)
            if tv is _stypes:
                d[k] = _subRefs(v, titlesL, namesL)
            elif tv in _destypes:
                _putRefs(v, titlesL, namesL)


# XXX: this class inherits from HTMLParser; see the documentation for
#      the "htmllib" and "sgmllib" modules.
class ParserBase(HTMLParser):
    # The imdbID is a 7-ciphers number.
    re_imdbID = re.compile(r'(?<=nm|tt)([0-9]{7})\b')
    re_imdbIDonly = re.compile(r'\b([0-9]{7})\b')
    __re_imdbIDmatch = re.compile(r'(nm|tt)[0-9]{7}\b')

    # It's set when names and titles references must be collected.
    # It can be set to 0 for search parsers.
    getRefs = 1
    
    def __init__(self, formatter=NullFormatter(), verbose=0):
        self._init()
        HTMLParser.__init__(self, formatter, verbose)
        # Use a "normal" space in place of the non-breaking space (0240/0xA0).
        self.entitydefs['nbsp'] = ' '

    def handle_charref(self, name):
        # Stupids, stupids non-breaking spaces...
        if name == '160': self.handle_data(' ')
        return HTMLParser.handle_charref(self, name)

    def unknown_charref(self, ref):
        try:
            n = unichr(int(ref)).encode('utf-8')
            self.handle_data(n)
        except (TypeError, ValueError, OverflowError):
            return HTMLParser.unknown_charref(self, ref)

    def reset(self):
        """Reset the parser."""
        HTMLParser.reset(self)
        # Names and titles references.
        self._namesRefs = {}
        self._titlesRefs = {}
        self._titleRefCID = ''
        self._nameRefCID = ''
        self._titleCN = ''
        self._nameCN = ''
        self._inTTRef = 0
        self._inLinkTTRef = 0
        self._inNMRef = 0
        self._reset()

    def get_attr_value(self, attrs_list, searched_attr):
        """Given a list of attributes in the form ('attr_name', 'attr_value')',
        return the attr_value of the 'searched_attr' attribute or None if it's
        not found."""
        for attr in attrs_list:
            if attr[0] == searched_attr:
                return attr[1]
        return None

    def _init(self): pass

    def _reset(self): pass

    def get_data(self): return None

    def handle_data(self, data):
        """Gather information about movie titles and person names,
        and call the _handle_data method."""
        if self.getRefs:
            if self._inNMRef:
                self._nameCN += data
            elif self._inTTRef:
                if self._inLinkTTRef:
                    self._titleCN += data
                else:
                    sdata = data.strip()
                    yearK = re_yearKind_index.match(sdata)
                    if yearK and yearK.start() == 0:
                        self._titleCN += ' %s' % sdata[:yearK.end()]
                        self._add_ref('tt')
        self._handle_data(data)

    def _handle_data(self, data): pass

    def _add_ref(self, kind):
        """Add a reference entry to the names and titles dictionaries."""
        if kind == 'tt':
            if self._titleRefCID and self._titleCN:
                if not self._titlesRefs.has_key(self._titleCN):
                    try:
                        movie = Movie(movieID=self._titleRefCID,
                                    title=self._titleCN, accessSystem='http')
                        self._titlesRefs[self._titleCN] = movie
                    except IMDbParserError:
                        pass
                self._titleRefCID = ''
                self._titleCN = ''
                self._inTTRef = 0
                self._inLinkTTRef = 0
        elif self._nameRefCID and self._nameCN:
            # XXX: 'Neo' and 'Keanu Reeves' are two separated
            #      entry in the dictionary.  Check the value instead
            #      of the key?
            if not self._namesRefs.has_key(self._nameCN):
                try:
                    person = Person(name=self._nameCN,
                                    personID=self._nameRefCID,
                                    accessSystem='http')
                    self._namesRefs[self._nameCN] = person
                except IMDbParserError:
                    pass
            self._nameRefCID = ''
            self._nameCN = ''
            self._inNMRef = 0

    def _refs_anchor_bgn(self, attrs):
        """At the start of an 'a' tag, gather info for the
        references dictionaries."""
        if self._inTTRef: self._add_ref('tt')
        if self._inNMRef: self._add_ref('nm')
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        if href.startswith('/title/tt'):
            href = href[7:]
            if not self.__re_imdbIDmatch.match(href) or \
                    (len(href) > 10 and href[10:11] != '?'):
                return
            href = href[2:]
            if href[-1] == '/': href = href[:-1]
            self._titleRefCID = href
            self._inTTRef = 1
            self._inLinkTTRef = 1
        elif href.startswith('/name/nm'):
            href = href[6:]
            if not self.__re_imdbIDmatch.match(href) or \
                    (len(href) > 10 and href[10:11] != '?'):
                return
            href = href[2:]
            if href[-1] == '/': href = href[:-1]
            self._nameRefCID = href
            self._inNMRef = 1

    def _refs_anchor_end(self):
        """At the end of an 'a' tag, gather info for the
        references dictionaries."""
        self._add_ref('nm')
        self._inLinkTTRef = 0

    def handle_starttag(self, tag, method, attrs):
        if self.getRefs:
            if tag == 'a': self._refs_anchor_bgn(attrs)
        method(attrs)

    def handle_endtag(self, tag, method):
        if self.getRefs:
            if tag == 'a': self._refs_anchor_end()
        method()

    def anchor_bgn(self, href, name, type): pass

    def anchor_end(self): pass

    def handle_image(self, src, alt, *args): pass

    def error(self, message):
        raise IMDbParserError, 'HTML parser error: "%s"' % str(message)

    def parse(self, html_string):
        """Return the dictionary generated from the given html string."""
        self.reset()
        self.feed(html_string)
        if self.getRefs and self._inTTRef: self._add_ref('tt')
        data = self.get_data()
        if self.getRefs:
            _putRefs(data, self._titlesRefs.keys(), self._namesRefs.keys())
        # XXX: should I return a copy of data?
        return {'data': data, 'titlesRefs': self._titlesRefs,
                'namesRefs': self._namesRefs}


