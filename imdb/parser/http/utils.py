"""
parser.http.utils module (imdb package).

This module provides miscellaneous utilities used by
the imdb.parser.http classes.

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
from types import UnicodeType, StringType, ListType, TupleType, DictType
from sgmllib import SGMLParser

from imdb._exceptions import IMDbParserError

from imdb.Movie import Movie
from imdb.Person import Person

# Year, imdbIndex and kind.
re_yearKind_index = re.compile(r'(\([0-9\?]{4}(?:/[IVXLCDM]+)?\)(?: \(mini\)| \(TV\)| \(V\)| \(VG\))?)')


_modify_keys = list(Movie.keys_tomodify_list) + list(Person.keys_tomodify_list)
def _putRefs(d, re_titles, re_names, lastKey=None):
    """Iterate over the strings inside list items or dictionary values,
    substitutes movie titles and person names with the (qv) references."""
    if isinstance(d, ListType):
        for i in xrange(len(d)):
            if isinstance(d[i], (UnicodeType, StringType)):
                if lastKey in _modify_keys:
                    if re_names:
                        d[i] = re_names.sub(ur"'\1' (qv)", d[i])
                    if re_titles:
                        d[i] = re_titles.sub(ur'_\1_ (qv)', d[i])
            elif isinstance(d[i], (ListType, DictType)):
                _putRefs(d[i], re_titles, re_names, lastKey=lastKey)
    elif isinstance(d, DictType):
        for k, v in d.items():
            lastKey = k
            if isinstance(v, (UnicodeType, StringType)):
                if lastKey in _modify_keys:
                    if re_names:
                        d[k] = re_names.sub(ur"'\1' (qv)", v)
                    if re_titles:
                        d[k] = re_titles.sub(ur'_\1_ (qv)', v)
            elif isinstance(v, (ListType, DictType)):
                _putRefs(d[k], re_titles, re_names, lastKey=lastKey)


# Handle HTML/XML/SGML entities.
from htmlentitydefs import entitydefs
entitydefs = entitydefs.copy()
entitydefsget = entitydefs.get
entitydefs['nbsp'] = ' '

sgmlentity = SGMLParser.entitydefs.copy()
sgmlentityget = sgmlentity.get
_sgmlentkeys = sgmlentity.keys()

entcharrefs = {}
entcharrefsget = entcharrefs.get
for _k, _v in entitydefs.items():
    if _k in _sgmlentkeys: continue
    if _v[0:2] == '&#':
        dec_code = _v[1:-1]
        _v = unichr(int(_v[2:-1]))
        entcharrefs[dec_code] = _v
    else:
        dec_code = '#' + str(ord(_v))
        _v = unicode(_v, 'latin_1', 'replace')
        entcharrefs[dec_code] = _v
    entcharrefs[_k] = _v
del _sgmlentkeys, _k, _v
entcharrefs['#160'] = u' '

re_entcharrefs = re.compile('&(%s|\#160|\#\d{1,5});' %
                            '|'.join(map(re.escape, entcharrefs)))
re_entcharrefssub = re_entcharrefs.sub

sgmlentity.update(dict([('#34', u'"'), ('#38', u'&'),
                        ('#60', u'<'), ('#62', u'>'), ('#39', u"'")]))
re_sgmlref = re.compile('&(%s);' % '|'.join(map(re.escape, sgmlentity)))
re_sgmlrefsub = re_sgmlref.sub


def _replXMLRef(match):
    """Replace the matched XML/HTML entities and references;
    replace everything except sgml entities like &lt;, &gt;, ..."""
    ref = match.group(1)
    value = entcharrefsget(ref)
    if value is None:
        if ref[0] == '#':
            ref_code = ref[1:]
            if ref_code in ('34', '38', '60', '62', '39'): return match.group(0)
            else: return unichr(int(ref[1:]))
        else:
            return ref
    return value

def subXMLRefs(s):
    """Return the given html string with entity and char references
    replaced."""
    return re_entcharrefssub(_replXMLRef, s)

def _replSGMLRefs(match):
    """Replace the matched SGML entity."""
    ref = match.group(1)
    return sgmlentityget(ref, ref)

def subSGMLRefs(s):
    """Return the given html string with sgml entity and char references
    replaced."""
    return re_sgmlrefsub(_replSGMLRefs, s)


# XXX: this class inherits from SGMLParser; see the documentation for
#      the "sgmllib" modules.
class ParserBase(SGMLParser):
    # The imdbID is a 7-ciphers number.
    re_imdbID = re.compile(r'(?<=nm|tt)([0-9]{7})\b')
    re_imdbIDonly = re.compile(r'\b([0-9]{7})\b')
    re_airdate = re.compile(r'(.*)\(season (\d+), episode (\d+)\)', re.I)
    _re_imdbIDmatch = re.compile(r'(nm|tt)[0-9]{7}\b')

    # It's set when names and titles references must be collected.
    # It can be set to 0 for search parsers.
    getRefs = 1
    entitydefs = sgmlentity

    def __init__(self, verbose=0):
        self._init()
        SGMLParser.__init__(self, verbose)

    def handle_charref(self, name):
        # Handles "quotes", "less than", "greater than" and so on.
        try:
            ret = unichr(int(name))
            self.handle_data(ret)
            return
        except (ValueError, TypeError, OverflowError):
            pass
        return SGMLParser.handle_charref(self, name)

    def unknown_charref(self, ref):
        try:
            n = unichr(int(ref))
            self.handle_data(n)
        except (TypeError, ValueError, OverflowError):
            return SGMLParser.unknown_charref(self, ref)

    def reset(self):
        """Reset the parser."""
        SGMLParser.reset(self)
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
                return subSGMLRefs(attr[1])
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
                        movie = Movie(movieID=str(self._titleRefCID),
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
            #      entry in the dictionary.  Check the ID value instead
            #      of the key?
            if not self._namesRefs.has_key(self._nameCN):
                try:
                    person = Person(name=self._nameCN,
                                    personID=str(self._nameRefCID),
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
            if not self._re_imdbIDmatch.match(href) or \
                    (len(href) > 10 and href[10:11] != '?'):
                return
            href = href[2:]
            if href[-1] == '/': href = href[:-1]
            self._titleRefCID = href
            self._inTTRef = 1
            self._inLinkTTRef = 1
        elif href.startswith('/name/nm'):
            href = href[6:]
            if not self._re_imdbIDmatch.match(href) or \
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

    def start_a(self, attrs): pass
    def end_a(self): pass

    def anchor_bgn(self, href, name, type): pass

    def anchor_end(self): pass

    def handle_image(self, src, alt, *args): pass

    def error(self, message):
        raise IMDbParserError, 'HTML parser error: "%s"' % str(message)

    def parse(self, html_string):
        """Return the dictionary generated from the given html string."""
        self.reset()
        # XXX: useful only for the testsuite.
        if not isinstance(html_string, UnicodeType):
            html_string = unicode(html_string, 'latin_1', 'replace')
        html_string = subXMLRefs(html_string)
        self.feed(html_string)
        if self.getRefs and self._inTTRef: self._add_ref('tt')
        data = self.get_data()
        if self.getRefs:
            # It would be nice to use ur'\b(%s)\b', but it seems that
            # some references are lost.
            titl_re = ur'(%s)' % '|'.join([re.escape(x) for x
                                            in self._titlesRefs.keys()])
            if titl_re != ur'()': re_titles = re.compile(titl_re, re.U)
            else: re_titles = None
            nam_re = ur'(%s)' % '|'.join([re.escape(x) for x
                                            in self._namesRefs.keys()])
            if nam_re != ur'()': re_names = re.compile(nam_re, re.U)
            else: re_names = None
            _putRefs(data, re_titles, re_names)
        # XXX: should I return a copy of data?  Answer: NO!
        return {'data': data, 'titlesRefs': self._titlesRefs,
                'namesRefs': self._namesRefs}


