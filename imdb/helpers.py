"""
helpers module (imdb package).

This module provides functions not used directly by the imdb package,
but useful for IMDbPY-based programs.

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
from cgi import escape

from utils import modClearRefs, re_titleRef, re_nameRef
from imdb.parser.http.utils import re_entcharrefssub, entcharrefsget


# An URL, more or less.
_re_href = re.compile(r'(http://.+?)(?=\s|$)', re.I)
_re_hrefsub = _re_href.sub

_uctype = type(u'')

def makeCgiPrintEncoding(encoding):
    """Make a function to pretty-print strings for the web."""
    def cgiPrint(s):
        """Encode the given string using the %s encoding, and replace
        chars outside the given codepage with XML char references.""" % encoding
        s = escape(s, quote=1)
        if type(s) is _uctype: s = s.encode(encoding, 'xmlcharrefreplace')
        return s
    return cgiPrint
# cgiPrint uses the latin_1 encoding.
cgiPrint = makeCgiPrintEncoding('latin_1')


def makeModCGILinks(movieTxt, personTxt):
    """Make a function used to pretty-print movies and persons refereces;
    movieTxt and personTxt are the strings used for the substitutions.
    movieTxt must contains %(movieID)s and %(title)s, while personTxt
    must contains %(personID)s and %(name)s."""
    def modCGILinks(s, titlesRefs, namesRefs):
        """Substitute movies and persons references."""
        def _replaceMovie(match):
            to_replace = match.group(1)
            item = titlesRefs.get(to_replace)
            if item:
                movieID = item.movieID
                to_replace = movieTxt % {'movieID': movieID,
                                        'title': unicode(cgiPrint(to_replace),
                                        'latin_1',
                                        'xmlcharrefreplace')}
            return to_replace
        def _replacePerson(match):
            to_replace = match.group(1)
            item = namesRefs.get(to_replace)
            if item:
                personID = item.personID
                to_replace = personTxt % {'personID': personID,
                                        'name': unicode(cgiPrint(to_replace),
                                        'latin_1',
                                        'xmlcharrefreplace')}
            return to_replace
        s = s.replace('<', '&lt;').replace('>', '&gt;')
        s = _re_hrefsub(r'<a href="\1">\1</a>', s)
        s = re_titleRef.sub(_replaceMovie, s)
        s = re_nameRef.sub(_replacePerson, s)
        return s
    return modCGILinks

modHtmlLinks = makeModCGILinks(
    movieTxt='<a href="http://akas.imdb.com/title/tt%(movieID)s">%s</a>',
    personTxt='<a href="http://akas.imdb.com/name/nm%(personID)s">%(name)s</a>')


def _replAllXMLRef(match):
    """Replace the matched XML references."""
    ref = match.group(1)
    value = entcharrefsget(ref)
    if value is None:
        if ref[0] == '#':
            ref_code = ref[1:]
            return unichr(int(ref[1:]))
        else:
            return ref
    return value

def subAllXMLRefs(s):
    """Return the given string with entity and char references
    replaced."""
    return re_entcharrefssub(_replAllXMLRef, s)


