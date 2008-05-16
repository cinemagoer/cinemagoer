"""
helpers module (imdb package).

This module provides functions not used directly by the imdb package,
but useful for IMDbPY-based programs.

Copyright 2006-2008 Davide Alberani <da@erlug.linux.it>

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
from imdb.utils import modClearRefs, re_titleRef, re_nameRef, re_characterRef
from imdb import IMDb, imdbURL_movie_base, imdbURL_person_base, \
                    imdbURL_character_base
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.Character import Character
from imdb.Company import Company
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

# Regular expression for %(varname)s substitutions.
re_subst = re.compile(r'%\((.+?)\)s')
# Regular expression for <if condition>....</if condition> clauses.
re_conditional = re.compile(r'<if\s+(.+?)\s*>(.+?)</if\s+\1\s*>')

def makeObject2Txt(movieTxt=None, personTxt=None, characterTxt=None,
               companyTxt=None, joiner=' / ',
               applyToValues=lambda x: x, _recurse=True):
    """"Return a function useful to pretty-print Movie, Person and
    Character instances.

    *movieTxt* -- how to format a Movie object.
    *personTxt* -- how to format a Person object.
    *characterTxt* -- how to format a Character object.
    *companyTxt* -- how to format a Company object.
    *joiner* -- string used to join a list of objects.
    *applyToValues* -- function to apply to values.
    *_recurse* -- if True (default) manage only the given object.
    """
    # Some useful defaults.
    if movieTxt is None:
        movieTxt = '%(long imdb title)s'
    if personTxt is None:
        personTxt = '%(long imdb name)s'
    if characterTxt is None:
        characterTxt = '%(long imdb name)s'
    if companyTxt is None:
        companyTxt = '%(long imdb name)s'
    def object2txt(obj, _limitRecursion=None):
        """Pretty-print objects."""
        # Prevent unlimited recursion.
        if _limitRecursion is None:
            _limitRecursion = 0
        elif _limitRecursion > 5:
            return u''
        _limitRecursion += 1
        if isinstance(obj, (list, tuple)):
            return joiner.join([object2txt(o, _limitRecursion=_limitRecursion)
                                for o in obj])
        elif isinstance(obj, dict):
            # XXX: not exactly nice, neither useful, I fear.
            return joiner.join([u'%s::%s' %
                            (object2txt(k, _limitRecursion=_limitRecursion),
                            object2txt(v, _limitRecursion=_limitRecursion))
                            for k, v in obj.items()])
        objData = {}
        if isinstance(obj, Movie):
            objData['movieID'] = obj.movieID
            outs = movieTxt
        elif isinstance(obj, Person):
            objData['personID'] = obj.personID
            outs = personTxt
        elif isinstance(obj, Character):
            objData['characterID'] = obj.characterID
            outs = characterTxt
        elif isinstance(obj, Company):
            objData['companyID'] = obj.companyID
            outs = companyTxt
        else:
            return obj
        def _excludeFalseConditionals(matchobj):
            # Return an empty string if the conditional is false/empty.
            condition = matchobj.group(1)
            proceed = obj.get(condition) or getattr(obj, condition, None)
            if proceed:
                return matchobj.group(2)
            else:
                return u''
            return matchobj.group(2)
        while re_conditional.search(outs):
            outs = re_conditional.sub(_excludeFalseConditionals, outs)
        for key in re_subst.findall(outs):
            value = obj.get(key) or getattr(obj, key, None)
            if not isinstance(value, (unicode, str)):
                if not _recurse:
                    if value:
                        value =  unicode(value)
                if value:
                    value = object2txt(value, _limitRecursion=_limitRecursion)
            elif value:
                value = applyToValues(unicode(value))
            if not value:
                value = u''
            elif not isinstance(value, (unicode, str)):
                value = unicode(value)
            outs = outs.replace(u'%(' + key + u')s', value)
        return outs
    return object2txt


def makeModCGILinks(movieTxt, personTxt, characterTxt=None,
                    encoding='latin_1'):
    """Make a function used to pretty-print movies and persons refereces;
    movieTxt and personTxt are the strings used for the substitutions.
    movieTxt must contains %(movieID)s and %(title)s, while personTxt
    must contains %(personID)s and %(name)s and characterTxt %(characterID)s
    and %(name)s; characterTxt is optional, for backward compatibility."""
    _cgiPrint = makeCgiPrintEncoding(encoding)
    def modCGILinks(s, titlesRefs, namesRefs, characterRefs=None):
        """Substitute movies and persons references."""
        if characterRefs is None: characterRefs = {}
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
        def _replaceCharacter(match):
            to_replace = match.group(1)
            if characterTxt is None:
                return to_replace
            item = characterRefs.get(to_replace)
            if item:
                characterID = item.characterID
                if characterID is None:
                    return to_replace
                to_replace = characterTxt % {'characterID': characterID,
                                        'name': unicode(_cgiPrint(to_replace),
                                                        encoding,
                                                        'xmlcharrefreplace')}
            return to_replace
        s = s.replace('<', '&lt;').replace('>', '&gt;')
        s = _re_hrefsub(r'<a href="\1">\1</a>', s)
        s = re_titleRef.sub(_replaceMovie, s)
        s = re_nameRef.sub(_replacePerson, s)
        s = re_characterRef.sub(_replaceCharacter, s)
        return s
    modCGILinks.movieTxt = movieTxt
    modCGILinks.personTxt = personTxt
    modCGILinks.characterTxt = characterTxt
    return modCGILinks

# links to the imdb.com web site.
_movieTxt = '<a href="' + imdbURL_movie_base + 'tt%(movieID)s">%(title)s</a>'
_personTxt = '<a href="' + imdbURL_person_base + 'nm%(personID)s">%(name)s</a>'
_characterTxt = '<a href="' + imdbURL_character_base + \
                'ch%(characterID)s">%(name)s</a>'
modHtmlLinks = makeModCGILinks(movieTxt=_movieTxt, personTxt=_personTxt,
                                characterTxt=_characterTxt)
modHtmlLinksASCII = makeModCGILinks(movieTxt=_movieTxt, personTxt=_personTxt,
                                    characterTxt=_characterTxt,
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
_re_imdbIDurl = re.compile(r'\b(nm|tt|ch|co)([0-9]{7})\b')
def get_byURL(url, info=None, args=None, kwds=None):
    """Return a Movie, Person, Character or Company object for the given URL;
    info is the info set to retrieve, args and kwds are respectively a list
    and a dictionary or arguments to initialize the data access system.
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
    elif imdbtype == 'ch':
        return ia.get_character(imdbID, info=info)
    elif imdbtype == 'co':
        return ia.get_company(imdbID, info=info)
    return None


