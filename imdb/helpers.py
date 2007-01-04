"""
helpers module (imdb package).

This module provides functions not used directly by the imdb package,
but useful for IMDbPY-based programs.

Copyright 2006 Davide Alberani <da@erlug.linux.it>

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

# XXX: find better names for the functions in this modules.

import re
from cgi import escape
from types import UnicodeType, TupleType, ListType

# The modClearRefs can be used to strip names and titles references from
# the strings in Movie and Person objects.
from utils import modClearRefs, re_titleRef, re_nameRef
from imdb import IMDb
from imdb.parser.http.utils import re_entcharrefssub, entcharrefs, \
                                    entcharrefsget, subXMLRefs, subSGMLRefs


# An URL, more or less.
_re_href = re.compile(r'(http://.+?)(?=\s|$)', re.I)
_re_hrefsub = _re_href.sub


def makeCgiPrintEncoding(encoding):
    """Make a function to pretty-print strings for the web."""
    def cgiPrint(s):
        """Encode the given string using the %s encoding, and replace
        chars outside the given charset with XML char references.""" % encoding
        s = escape(s, quote=1)
        if isinstance(s, UnicodeType):
            s = s.encode(encoding, 'xmlcharrefreplace')
        return s
    return cgiPrint

# cgiPrint uses the latin_1 encoding.
cgiPrint = makeCgiPrintEncoding('latin_1')


def makeModCGILinks(movieTxt, personTxt, encoding='latin_1'):
    """Make a function used to pretty-print movies and persons refereces;
    movieTxt and personTxt are the strings used for the substitutions.
    movieTxt must contains %(movieID)s and %(title)s, while personTxt
    must contains %(personID)s and %(name)s."""
    _cgiPrint = makeCgiPrintEncoding(encoding)
    def modCGILinks(s, titlesRefs, namesRefs):
        """Substitute movies and persons references."""
        # XXX: look ma'... more nested scopes! <g>
        def _replaceMovie(match):
            to_replace = match.group(1)
            item = titlesRefs.get(to_replace)
            if item:
                movieID = item.movieID
                to_replace = movieTxt % {'movieID': movieID,
                                        'title': unicode(_cgiPrint(to_replace),
                                                        encoding,
                                                        'xmlcharrefreplace')}
            return to_replace
        def _replacePerson(match):
            to_replace = match.group(1)
            item = namesRefs.get(to_replace)
            if item:
                personID = item.personID
                to_replace = personTxt % {'personID': personID,
                                        'name': unicode(_cgiPrint(to_replace),
                                                        encoding,
                                                        'xmlcharrefreplace')}
            return to_replace
        s = s.replace('<', '&lt;').replace('>', '&gt;')
        s = _re_hrefsub(r'<a href="\1">\1</a>', s)
        s = re_titleRef.sub(_replaceMovie, s)
        s = re_nameRef.sub(_replacePerson, s)
        return s
    return modCGILinks

# links to the imdb.com web site.
_movieTxt = '<a href="http://akas.imdb.com/title/tt%(movieID)s">%(title)s</a>'
_personTxt = '<a href="http://akas.imdb.com/name/nm%(personID)s">%(name)s</a>'
modHtmlLinks = makeModCGILinks(movieTxt=_movieTxt, personTxt=_personTxt)
modHtmlLinksASCII = makeModCGILinks(movieTxt=_movieTxt, personTxt=_personTxt,
                                    encoding='ascii')


everyentcharrefs = entcharrefs.copy()
for k, v in {'lt':u'<','gt':u'>','amp':u'&','quot':u'"','apos':u'\''}.items():
    everyentcharrefs[k] = v
    everyentcharrefs['#%s' % ord(v)] = v
everyentcharrefsget = everyentcharrefs.get
re_everyentcharrefs = re.compile('&(%s|\#160|\#\d{1,5});' %
                            '|'.join(map(re.escape, everyentcharrefs)))
re_everyentcharrefssub = re_everyentcharrefs.sub

def _replAllXMLRef(match):
    """Replace the matched XML reference."""
    ref = match.group(1)
    value = everyentcharrefsget(ref)
    if value is None:
        if ref[0] == '#':
            return unichr(int(ref[1:]))
        else:
            return ref
    return value

def subXMLHTMLSGMLRefs(s):
    """Return the given string with XML/HTML/SGML entity and char references
    replaced."""
    return re_everyentcharrefssub(_replAllXMLRef, s)


def sortedSeasons(m):
    """Return a sorted list of seasons of the given series."""
    seasons = m.get('episodes', {}).keys()
    seasons.sort()
    return seasons


def sortedEpisodes(m, season=None):
    """Return a sorted list of episodes of the given series,
    considering only the specified season(s) (every season, if None)."""
    episodes = []
    seasons = season
    if season is None:
        seasons = sortedSeasons(m)
    else:
        if not isinstance(season, (TupleType, ListType)):
            seasons = [season]
    for s in seasons:
        eps_indx = m.get('episodes', {}).get(s, {}).keys()
        eps_indx.sort()
        for e in eps_indx:
            episodes.append(m['episodes'][s][e])
    return episodes


# Idea and portions of the code courtesy of none none (dclist at gmail.com)
_re_imdbIDurl = re.compile(r'\b(nm|tt)([0-9]{7})\b')
def get_byURL(url, info=None, args=None, kwds=None):
    """Return a Movie or Person object for the given URL; info is the
    info set to retrieve, args and kwds are respectively a list and a
    dictionary or arguments to initialize the data access system.
    Returns None if unable to correctly parse the url; can raise
    exceptions if unable to retrieve the data."""
    if args is None: args = []
    if kwds is None: kwds = {}
    ia = IMDb(*args, **kwds)
    match = _re_imdbIDurl.search(url)
    if not match:
        return None
    imdbtype = match.group(1)
    imdbID = match.group(2)
    if imdbtype == 'tt':
        return ia.get_movie(imdbID, info=info)
    elif imdbtype == 'nm':
        return ia.get_person(imdbID, info=info)
    return None


