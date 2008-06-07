"""
parser.http.utils module (imdb package).

This module provides miscellaneous utilities used by
the imdb.parser.http classes.

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

import re
from types import UnicodeType, StringType, ListType, DictType
from sgmllib import SGMLParser
from urllib import unquote

from imdb._exceptions import IMDbParserError

from imdb.Movie import Movie
from imdb.Person import Person
from imdb.Character import Character

# Year, imdbIndex and kind.
re_yearKind_index = re.compile(r'(\([0-9\?]{4}(?:/[IVXLCDM]+)?\)(?: \(mini\)| \(TV\)| \(V\)| \(VG\))?)')


_modify_keys = list(Movie.keys_tomodify_list) + list(Person.keys_tomodify_list)
def _putRefs(d, re_titles, re_names, re_characters, lastKey=None):
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
                    if re_characters:
                        d[i] = re_characters.sub(ur'#\1# (qv)', d[i])
            elif isinstance(d[i], (ListType, DictType)):
                _putRefs(d[i], re_titles, re_names, re_characters,
                        lastKey=lastKey)
    elif isinstance(d, DictType):
        for k, v in d.items():
            lastKey = k
            if isinstance(v, (UnicodeType, StringType)):
                if lastKey in _modify_keys:
                    if re_names:
                        d[k] = re_names.sub(ur"'\1' (qv)", v)
                    if re_titles:
                        d[k] = re_titles.sub(ur'_\1_ (qv)', v)
                    if re_characters:
                        d[k] = re_characters.sub(ur'#\1# (qv)', v)
            elif isinstance(v, (ListType, DictType)):
                _putRefs(d[k], re_titles, re_names, re_characters,
                        lastKey=lastKey)


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

# Matches XML-only single tags, like <br/> ; they are invalid in HTML,
# but widely used by IMDb web site. :-/
re_xmltags = re.compile('<([a-zA-Z]+)/>')


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


def build_person(txt, personID=None, billingPos=None,
                roleID=None, accessSystem='http', modFunct=None):
    """Return a Person instance from the tipical <tr>...</tr> strings
    found in the IMDb's web site."""
    notes = u''
    role = u''
    # Search the (optional) separator between name and role/notes.
    if txt.find('....') != -1:
        sep = '....'
    elif txt.find('...') != -1:
        sep = '...'
    else:
        sep = '...'
        # Replace the first parenthesis, assuming there are only
        # notes, after.
        # Rationale: no imdbIndex is (ever?) showed on the web site.
        txt = txt.replace('(', '...(', 1)
    txt_split = txt.split(sep, 1)
    name = txt_split[0].strip()
    if len(txt_split) == 2:
        role_comment = txt_split[1].strip()
        # Strip common endings.
        if role_comment[-4:] == ' and':
            role_comment = role_comment[:-4].rstrip()
        elif role_comment[-2:] == ' &':
            role_comment = role_comment[:-2].rstrip()
        elif role_comment[-6:] == '& ....':
            role_comment = role_comment[:-6].rstrip()
        # Get the notes.
        cmt_idx = role_comment.find('(')
        if cmt_idx != -1:
            role = role_comment[:cmt_idx].rstrip()
            notes = role_comment[cmt_idx:]
        else:
            # Just a role, without notes.
            role = role_comment
    if role == '....': role = u''
    # Manages multiple roleIDs.
    if isinstance(roleID, list):
        role = role.split(' / ')
        lr = len(role)
        lrid = len(roleID)
        if lr > lrid:
            roleID += [None] * (lrid - lr)
        elif lr < lrid:
            roleID = roleID[:lr]
        if lr == 1:
            role = role[0]
            roleID = roleID[0]
    # XXX: return None if something strange is detected?
    return Person(name=name, personID=personID, currentRole=role,
                    roleID=roleID, notes=notes, billingPos=billingPos,
                    modFunct=modFunct, accessSystem=accessSystem)


# To shrink spaces.
re_spaces = re.compile(r'\s+')
def build_movie(txt, movieID=None, roleID=None, status=None,
                accessSystem='http', modFunct=None, _parsingCharacter=False,
                _parsingCompany=False):
    """Given a string as normally seen on the "categorized" page of
    a person on the IMDb's web site, returns a Movie instance."""
    if _parsingCharacter:
        _defSep = ' Played by '
    elif _parsingCompany:
        _defSep = ' ... '
    else:
        _defSep = '....'
    title = re_spaces.sub(' ', txt).strip()
    # Split the role/notes from the movie title.
    tsplit = title.split(_defSep, 1)
    role = u''
    notes = u''
    if len(tsplit) == 2:
        title = tsplit[0].rstrip()
        role = tsplit[1].lstrip()
        # Find notes in the role.
        if role[-1:] == ')':
            nidx = role.find('(')
            # XXX: check balanced parentheses?
            if nidx != -1:
                notes = role[nidx:]
                role = role[:nidx].rstrip()
    if title[-9:] == 'TV Series':
        title = title[:-9].rstrip()
    # Try to understand where the movie title ends.
    while True:
        if title[-1:] != ')':
            # Ignore the silly "TV Series" notice.
            if title[-9:] == 'TV Series':
                title = title[:-9].rstrip()
                continue
            else:
                # Just a title: stop here.
                break
        # Try to match paired parentheses; yes: sometimes there are
        # parentheses inside comments...
        nidx = title.rfind('(')
        while (nidx != -1 and \
                    title[nidx:].count('(') != title[nidx:].count(')')):
            nidx = title[:nidx].rfind('(')
        # Unbalanced parentheses: stop here.
        if nidx == -1: break
        # The last item in parentheses seems to be a year: stop here.
        first4 = title[nidx+1:nidx+5]
        if (first4.isdigit() or first4 == '????') and \
                title[nidx+5:nidx+6] in (')', '/'): break
        # The last item in parentheses is a known kind: stop here.
        if title[nidx+1:-1] in ('TV', 'V', 'mini', 'VG'): break
        # Else, in parentheses there are some notes.
        # XXX: should the notes in the role half be kept separated
        #      from the notes in the movie title half?
        if notes: notes = '%s %s' % (title[nidx:], notes)
        else: notes = title[nidx:]
        title = title[:nidx].rstrip()
    if _parsingCharacter and roleID and not role:
        roleID = None
    if not roleID:
        roleID = None
    elif len(roleID) == 1:
        roleID = roleID[0]
    # Manages multiple roleIDs.
    if isinstance(roleID, list):
        role = role.split(' / ')
        lr = len(role)
        lrid = len(roleID)
        if lr > lrid:
            roleID += [None] * (lrid - lr)
        elif lr < lrid:
            roleID = roleID[:lr]
        if lr == 1:
            role = role[0]
            roleID = roleID[0]
    m = Movie(title=title, movieID=movieID, notes=notes, currentRole=role,
                roleID=roleID, roleIsPerson=_parsingCharacter,
                modFunct=modFunct, accessSystem=accessSystem)
    # Status can't be checked here, and must be detected by the parser.
    if status:
        m['status'] = status
    return m


# XXX: this class inherits from SGMLParser; see the documentation for
#      the "sgmllib" modules.
class ParserBase(SGMLParser):
    """Base parser to handle HTML data from the IMDb's web server."""
    # The imdbID is a 7-ciphers number.
    re_imdbID = re.compile(r'(?<=nm|tt|ch|co)([0-9]{7})\b')
    re_imdbIDonly = re.compile(r'\b([0-9]{7})\b')
    re_airdate = re.compile(r'(.*)\s*\(season (\d+), episode (\d+)\)', re.I)
    _re_imdbIDmatch = re.compile(r'(nm|tt|ch|co)[0-9]{7}/?$')

    # It's set when names and titles references must be collected.
    # It can be set to 0 for search parsers.
    _defGetRefs = False
    entitydefs = sgmlentity

    def __init__(self, verbose=0):
        self._init()
        # Fall-back defaults.
        self._modFunct = None
        self._as = 'http'
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
        self._charactersRefs = {}
        self._titleRefCID = u''
        self._nameRefCID = u''
        self._characterRefCID = u''
        self._titleCN = u''
        self._nameCN = u''
        self._characterCN = u''
        self._inTTRef = 0
        self._inLinkTTRef = 0
        self._inNMRef = 0
        self._inCHRef = 0
        self._in_content = 0
        self._div_count = 0
        self._reset()

    def get_attr_value(self, attrs_list, searched_attr):
        """Given a list of attributes in the form ('attr_name', 'attr_value')',
        return the attr_value of the 'searched_attr' attribute or None if it's
        not found."""
        for attr in attrs_list:
            if attr[0] == searched_attr:
                attr = attr[1]
                try:
                    attr = unquote(str(attr))
                    attr = unicode(attr, 'latin_1')
                except UnicodeEncodeError:
                    pass
                return subSGMLRefs(attr)
        return None

    def _init(self): pass

    def _reset(self): pass

    def get_data(self): return None

    def handle_data(self, data):
        """Gather information about movie titles and person names,
        and call the _handle_data method."""
        if self.getRefs:
            if self._inNMRef:
                self._nameCN += data.replace('\n', ' ')
            elif self._inTTRef:
                if self._inLinkTTRef:
                    self._titleCN += data.replace('\n', ' ')
                else:
                    sdata = data.strip().replace('\n', ' ')
                    yearK = re_yearKind_index.match(sdata)
                    if yearK and yearK.start() == 0:
                        self._titleCN += ' %s' % sdata[:yearK.end()]
                        self._add_ref('tt')
            elif self._inCHRef:
                self._characterCN += data.replace('\n', ' ')
        self._handle_data(data)

    def _handle_data(self, data): pass

    def _add_ref(self, kind):
        """Add a reference entry to the names and titles dictionaries."""
        if kind == 'tt':
            if self._titleRefCID and self._titleCN:
                if not self._titlesRefs.has_key(self._titleCN):
                    try:
                        movie = Movie(movieID=str(self._titleRefCID),
                                    title=self._titleCN, accessSystem=self._as,
                                    modFunct=self._modFunct)
                        self._titlesRefs[self._titleCN] = movie
                    except IMDbParserError:
                        pass
                self._titleRefCID = u''
                self._titleCN = u''
                self._inTTRef = 0
                self._inLinkTTRef = 0
        elif kind == 'nm' and self._nameRefCID and self._nameCN:
            # XXX: 'Neo' and 'Keanu Reeves' are two separated
            #      entry in the dictionary.  Check the ID value instead
            #      of the key?
            if not self._namesRefs.has_key(self._nameCN):
                try:
                    person = Person(name=self._nameCN,
                                    personID=str(self._nameRefCID),
                                    accessSystem=self._as,
                                    modFunct=self._modFunct)
                    self._namesRefs[self._nameCN] = person
                except IMDbParserError:
                    pass
            self._nameRefCID = u''
            self._nameCN = u''
            self._inNMRef = 0
        elif kind == 'ch' and self._characterRefCID and self._characterCN:
            if not self._charactersRefs.has_key(self._characterCN):
                try:
                    character = Character(name=self._characterCN,
                                    characterID=str(self._characterRefCID),
                                    accessSystem='http')
                    self._charactersRefs[self._characterCN] = character
                except IMDbParserError:
                    pass
            self._characterRefCID = u''
            self._characterCN = u''
            self._inCHRef = 0

    def _refs_anchor_bgn(self, attrs):
        """At the start of an 'a' tag, gather info for the
        references dictionaries."""
        if self._inTTRef: self._add_ref('tt')
        if self._inNMRef: self._add_ref('nm')
        if self._inCHRef: self._add_ref('ch')
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
        elif href.startswith('/character/ch'):
            href = href[11:]
            if not self._re_imdbIDmatch.match(href):
                return
            href = href[2:]
            if href[-1] == '/': href = href[:-1]
            self._characterRefCID = href
            self._inCHRef = 1

    def _refs_anchor_end(self):
        """At the end of an 'a' tag, gather info for the
        references dictionaries."""
        # XXX: check if self.getRefs is True?
        self._add_ref('nm')
        self._add_ref('ch')
        self._inLinkTTRef = 0

    def handle_starttag(self, tag, method, attrs):
        if self.getRefs:
            # XXX: restrict collection to links in self._in_content ?
            if tag == 'a': self._refs_anchor_bgn(attrs)
        if tag == 'div':
            if not self._in_content:
                # In the new IMDb's layout the content is nicely tagged. :-)
                if self.get_attr_value(attrs, 'id') == 'tn15content':
                    self._in_content = 1
                    self._div_count = 1
                    self._begin_content()
            else:
                # Another div tag inside the content.
                self._div_count += 1
        method(attrs)

    def handle_endtag(self, tag, method):
        if self.getRefs:
            if tag == 'a': self._refs_anchor_end()
        # Count div tags inside the 'tn15content' one, and set
        # self._in_content to False only when the count drops to zero.
        if tag == 'div':
            if self._in_content:
                self._div_count -= 1
                if self._div_count <= 0:
                    self._end_content()
                    self._in_content = 0
        method()

    def _begin_content(self): pass
    def _end_content(self): pass

    def start_a(self, attrs): pass
    def end_a(self): pass

    def start_div(self, attrs): pass
    def end_div(self): pass

    def anchor_bgn(self, href, name, type): pass

    def anchor_end(self): pass

    def handle_image(self, src, alt, *args): pass

    def error(self, message):
        raise IMDbParserError, 'HTML parser error: "%s"' % str(message)

    def parse(self, html_string, getRefs=None, **kwds):
        """Return the dictionary generated from the given html string."""
        self.reset()
        if getRefs is not None:
            self.getRefs = getRefs
        else:
            self.getRefs = self._defGetRefs
        for key, value in kwds.items():
            setattr(self, key, value)
        # XXX: useful only for the testsuite.
        if not isinstance(html_string, UnicodeType):
            html_string = unicode(html_string, 'latin_1', 'replace')
        html_string = subXMLRefs(html_string)
        # Fix invalid HTML single tags like <br/>
        html_string = re_xmltags.sub('<\\1 />', html_string)
        self.feed(html_string)
        # Fallback measure for wrong HTML - not sure why, but here
        # self._in_content seems to be always False.
        if self._div_count > 0:
            self._end_content()
            self._in_content = 0
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
            chr_re = ur'(%s)' % '|'.join([re.escape(x) for x
                                            in self._charactersRefs.keys()])
            if chr_re != ur'()': re_characters = re.compile(chr_re, re.U)
            else: re_characters = None
            _putRefs(data, re_titles, re_names, re_characters)
        # XXX: should I return a copy of data?  Answer: NO!
        return {'data': data, 'titlesRefs': self._titlesRefs,
                'namesRefs': self._namesRefs,
                'charactersRefs': self._charactersRefs}


