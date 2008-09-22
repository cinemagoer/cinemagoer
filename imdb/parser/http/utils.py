"""
parser.http.utils module (imdb package).

This module provides miscellaneous utilities used by
the imdb.parser.http classes.

Copyright 2004-2008 Davide Alberani <da@erlug.linux.it>
               2008 H. Turgut Uyar <uyar@tekir.org>

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
import warnings
from types import UnicodeType, StringType, ListType, DictType
from sgmllib import SGMLParser
from urllib import unquote

from imdb._exceptions import IMDbParserError, IMDbError

from imdb.utils import flatten, _Container
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.Character import Character


# Year, imdbIndex and kind.
re_yearKind_index = re.compile(r'(\([0-9\?]{4}(?:/[IVXLCDM]+)?\)(?: \(mini\)| \(TV\)| \(V\)| \(VG\))?)')

# Match imdb ids in href tags
re_imdbid = re.compile(r'(title/tt|name/nm|character/ch|company/co)([0-9]+)')

def analyze_imdbid(href):
    """Return an imdbID from an URL."""
    if not href:
        return None
    match = re_imdbid.search(href)
    if not match:
        return None
    return match.group(2)


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


class DOMParserBase(object):
    """Base parser to handle HTML data from the IMDb's web server -
    DOM/XPath version."""
    _defGetRefs = False
    _containsObjects = False
    _fixRowSpans = False

    preprocessors = []
    extractors = []

    def __init__(self, useModule=None):
        # Module to use.
        if useModule is None:
            useModule = ('lxml', 'BeautifulSoup')
        if not isinstance(useModule, (tuple, list)):
            useModule = [useModule]
        self._useModule = useModule
        nrMods = len(useModule)
        _gotError = False
        for idx, mod in enumerate(useModule):
            mod = mod.lower()
            try:
                if mod == 'lxml':
                    from lxmladapter import fromstring
                    from lxmladapter import tostring
                    from lxmladapter import fix_rowspans
                    from lxmladapter import apply_xpath
                elif mod == 'beautifulsoup':
                    from bsoupadapter import fromstring
                    from bsoupadapter import tostring
                    from bsoupadapter import fix_rowspans
                    from bsoupadapter import apply_xpath
                else:
                    warnings.warn('unknown module "%s".' % mod)
                    continue
                self.fromstring = fromstring
                self.tostring = tostring
                self.apply_xpath = apply_xpath
                self.fix_rowspans = fix_rowspans
                if _gotError:
                    warnings.warn('falling back to "%s".' % mod)
                break
            except ImportError, e:
                if idx+1 >= nrMods:
                    # Raise the exception, if we don't have any more
                    # options to try.
                    raise IMDbError, 'unable to use any parser in %s: %s' % (
                                                    str(useModule), str(e))
                else:
                    warnings.warn('unable to use "%s": %s' % (mod, str(e)))
                    _gotError = True
                continue
        else:
            raise IMDbError, 'unable to use parsers in %s' % str(useModule)
        # Fall-back defaults.
        self._modFunct = None
        self._as = 'http'
        self._init()
        self.reset()

    def reset(self):
        """Reset the parser."""
        # Names and titles references.
        self._namesRefs = {}
        self._titlesRefs = {}
        self._charactersRefs = {}
        self._reset()

    def _init(self):
        pass

    def _reset(self):
        pass

    def parse(self, html_string, getRefs=None, **kwds):
        """Return the dictionary generated from the given html string."""
        self.reset()
        if getRefs is not None:
            self.getRefs = getRefs
        else:
            self.getRefs = self._defGetRefs
        # XXX: useful only for the testsuite.
        if not isinstance(html_string, UnicodeType):
            html_string = unicode(html_string, 'latin_1', 'replace')
        html_string = subXMLRefs(html_string)
        ## Not required?
        ##html_string = subSGMLRefs(html_string)
        # Temporary fix: self.parse_dom must work even for empty strings.
        html_string = self.preprocess_string(html_string)
        if self.getRefs:
            self.gather_refs(html_string)
        html_string = html_string.strip()
        if html_string:
            data = self.parse_dom(html_string)
        else:
            data = {}
        data = self.postprocess_data(data)
        if self._containsObjects:
            self.set_objects_params(data)
        data = self.add_refs(data)
        return data

    def get_dom(self, html_string):
        return self.fromstring(html_string)

    def xpath(self, element, xpath):
        return self.apply_xpath(element, xpath)

    def _fix_rowspans(self, html_string):
        return self.fix_rowspans(html_string)

    def preprocess_string(self, html_string):
        """Here we can modify the text, before it's parsed."""
        if len(html_string) == 0:
            return html_string
        try:
            preprocessors = self.preprocessors
        except AttributeError:
            return html_string
        for src, sub in preprocessors:
            # re._pattern_type is present only since Python 2.5.
            if callable(getattr(src, 'sub', None)):
                html_string = src.sub(sub, html_string)
            elif isinstance(src, str):
                html_string = html_string.replace(src, sub)
            elif callable(src):
                html_string = src(html_string)
        if self._fixRowSpans:
            html_string = self._fix_rowspans(html_string)
        ##print html_string.encode('utf8')
        return html_string

    def gather_refs(self, html_string):
        """Collect refs."""
        # XXX: does this degrades performances?  Probably not at all.
        grParser = GatherRefs(useModule=self._useModule)
        grParser._as = self._as
        grParser._modFunct = self._modFunct
        refs = grParser.parse(html_string)
        self._namesRefs = refs['names refs']
        self._titlesRefs = refs['titles refs']
        self._charactersRefs = refs['characters refs']

    def parse_dom(self, html_string):
        """Parse the given string according to the rules specified
        in self.extractors."""
        dom = self.get_dom(html_string)
        result = {}
        for extractor in self.extractors:
            if extractor.group is None:
                elements = [(extractor.label, element)
                            for element in self.xpath(dom, extractor.path)]
            else:
                groups = self.xpath(dom, extractor.group)
                elements = []
                for group in groups:
                    group_key = self.xpath(group, extractor.group_key)
                    if not group_key: continue
                    group_key = group_key[0]
                    # XXX: always tries the conversion to unicode:
                    #      BeautifulSoup.NavigableString is a subclass
                    #      of unicode, and so it's never converted.
                    group_key = self.tostring(group_key)
                    normalizer = extractor.group_key_normalize
                    if normalizer is not None:
                        if callable(normalizer):
                            group_key = normalizer(group_key)
                    group_elements = self.xpath(group, extractor.path)
                    elements.extend([(group_key, element)
                                     for element in group_elements])
            for group_key, element in elements:
                for attr in extractor.attrs:
                    if isinstance(attr.path, dict):
                        data = {}
                        for field in attr.path.keys():
                            path = attr.path[field]
                            value = self.xpath(element, path)
                            if not value:
                                data[field] = None
                            else:
                                data[field] = ''.join(value)
                    else:
                        data = self.xpath(element, attr.path)
                        if not data:
                            data = None
                        else:
                            data = attr.joiner.join(data)
                    if not data:
                        continue
                    attr_postprocess = attr.postprocess
                    if callable(attr_postprocess):
                        data = attr_postprocess(data)
                    key = attr.key
                    if key is None:
                        key = group_key
                    elif key.startswith('.'):
                        # assuming this is an xpath
                        key = self.xpath(element, key)[0]
                    elif key.startswith('self.'):
                        key = getattr(self, key[5:])
                    if attr.multi:
                        if not result.has_key(key):
                            result[key] = []
                        result[key].append(data)
                    else:
                        if isinstance(data, dict):
                            result.update(data)
                        else:
                            result[key] = data
        return result

    def postprocess_data(self, data):
        """Here we can modify the data."""
        return data

    def set_objects_params(self, data):
        """Set parameters of Movie/Person/... instances, since they are
        not always set in the parser's code."""
        for obj in flatten(data, yieldDictKeys=True, scalar=_Container):
            obj.accessSystem = self._as
            obj.modFunct = self._modFunct

    def add_refs(self, data):
        """Modify data according to the expected output."""
        if self.getRefs:
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
        return {'data': data, 'titlesRefs': self._titlesRefs,
                'namesRefs': self._namesRefs,
                'charactersRefs': self._charactersRefs}


class Extractor(object):
    """Instruct the DOM parser about how to parse a document."""
    def __init__(self, label, path, attrs, group=None, group_key=None,
                 group_key_normalize=None):
        """Initialize an Extractor object, used to instruct the DOM parser
        about how to parse a document."""
        # rarely (never?) used, mostly for debugging purposes.
        self.label = label
        self.group = group
        if group_key is None:
            self.group_key = ".//text()"
        else:
            self.group_key = group_key
        self.group_key_normalize = group_key_normalize
        self.path = path
        # A list of attributes to fetch.
        if isinstance(attrs, Attribute):
            attrs = [attrs]
        self.attrs = attrs

    def __repr__(self):
        """String representation of an Extractor object."""
        r = '<Extractor id:%s (label=%s, path=%s, attrs=%s, group=%s, ' \
                'group_key=%s group_key_normalize=%s)>' % (id(self),
                        self.label, self.path, repr(self.attrs), self.group,
                        self.group_key, self.group_key_normalize)
        return r


class Attribute(object):
    """The attribute to consider, for a given node."""
    def __init__(self, key, multi=False, path=None, joiner=None,
                 postprocess=None):
        """Initialize an Attribute object, used to specify the
        attribute to consider, for a given node."""
        # The key under which information will be saved; can be a string or an
        # XPath. If None, the label of the containing extractor will be used.
        self.key = key
        self.multi = multi
        self.path = path
        if joiner is None:
            joiner = ''
        self.joiner = joiner
        # Post-process this set of information.
        self.postprocess = postprocess

    def __repr__(self):
        """String representation of an Attribute object."""
        r = '<Attribute id:%s (key=%s, multi=%s, path=%s, joiner=%s, ' \
                'postprocess=%s)>' % (id(self), self.key,
                        self.multi, repr(self.path),
                        self.joiner, repr(self.postprocess))
        return r


def _parse_ref(text, link, info):
    """Manage links to references."""
    if link.find('/title/tt') != -1:
        yearK = re_yearKind_index.match(info)
        if yearK and yearK.start() == 0:
            text += ' %s' % info[:yearK.end()]
    return (text.replace('\n', ' '), link)


class GatherRefs(DOMParserBase):
    """Parser used to gather references to movies, persons and characters."""
    _attrs = [Attribute(key=None, multi=True,
                        path={
                            'text': './text()',
                            'link': './@href',
                            'info': './following::text()[1]'
                            },
        postprocess=lambda x: _parse_ref(x.get('text'), x.get('link'),
                                         (x.get('info') or u'').strip()))]
    extractors = [
        Extractor(label='names refs',
            path="//a[starts-with(@href, '/name/nm')][string-length(@href)=16]",
            attrs=_attrs),

        Extractor(label='titles refs',
            path="//a[starts-with(@href, '/title/tt')]" \
                    "[string-length(@href)=17]",
            attrs=_attrs),

        Extractor(label='characters refs',
            path="//a[starts-with(@href, '/character/ch')]" \
                    "[string-length(@href)=21]",
            attrs=_attrs),
            ]

    def postprocess_data(self, data):
        result = {}
        for item in ('names refs', 'titles refs', 'characters refs'):
            result[item] = {}
            for k, v in data.get(item, []):
                if not v.endswith('/'): continue
                imdbID = str(analyze_imdbid(v))
                if item == 'names refs':
                    obj = Person(personID=imdbID, name=k,
                                accessSystem=self._as, modFunct=self._modFunct)
                elif item == 'titles refs':
                    obj = Movie(movieID=imdbID, title=k,
                                accessSystem=self._as, modFunct=self._modFunct)
                else:
                    obj = Character(characterID=imdbID, name=k,
                                accessSystem=self._as, modFunct=self._modFunct)
                result[item][k] = obj
        return result

    def add_refs(self, data):
        return data


