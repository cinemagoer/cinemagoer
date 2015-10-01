"""
helpers module (imdb package).

This module provides functions not used directly by the imdb package,
but useful for IMDbPY-based programs.

Copyright 2006-2012 Davide Alberani <da@erlug.linux.it>
               2012 Alberto Malagoli <albemala AT gmail.com>

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
import difflib
from cgi import escape
import gettext
from gettext import gettext as _
gettext.textdomain('imdbpy')

# The modClearRefs can be used to strip names and titles references from
# the strings in Movie and Person objects.
from imdb.utils import modClearRefs, re_titleRef, re_nameRef, \
                    re_characterRef, _tagAttr, _Container, TAGS_TO_MODIFY
import imdb.locale
from imdb.linguistics import COUNTRY_LANG
from imdb.Movie import Movie
from bs4 import BeautifulSoup


# An URL, more or less.
_re_href = re.compile(r'(http://.+?)(?=\s|$)', re.I)
_re_hrefsub = _re_href.sub

# links to the imdb.com web site.
_movieTxt = '<a href="' + imdbURL_movie_base + 'tt%(movieID)s">%(title)s</a>'

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
        if not isinstance(season, (tuple, list)):
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


# Idea and portions of code courtesy of Basil Shubin.
# Beware that these information are now available directly by
# the Movie/Person/Character instances.
def fullSizeCoverURL(obj):
    """Given an URL string or a Movie, Person or Character instance,
    returns an URL to the full-size version of the cover/headshot,
    or None otherwise.  This function is obsolete: the same information
    are available as keys: 'full-size cover url' and 'full-size headshot',
    respectively for movies and persons/characters."""
    if isinstance(obj, Movie):
        coverUrl = obj.get('cover url')
    else:
        coverUrl = obj
    if not coverUrl:
        return None
    return _Container._re_fullsizeURL.sub('', coverUrl)


def keyToXML(key):
    """Return a key (the ones used to access information in Movie and
    other classes instances) converted to the style of the XML output."""
    return _tagAttr(key, '')[0]


def translateKey(key):
    """Translate a given key."""
    return _(keyToXML(key))


# Maps tags to classes.
_MAP_TOP_OBJ = {
    'movie': Movie,
}

# Tags to be converted to lists.
_TAGS_TO_LIST = dict([(x[0], None) for x in TAGS_TO_MODIFY.values()])
_TAGS_TO_LIST.update(_MAP_TOP_OBJ)

def tagToKey(tag):
    """Return the name of the tag, taking it from the 'key' attribute,
    if present."""
    keyAttr = tag.get('key')
    if keyAttr:
        if tag.get('keytype') == 'int':
            keyAttr = int(keyAttr)
        return keyAttr
    return tag.name


def _valueWithType(tag, tagValue):
    """Return tagValue, handling some type conversions."""
    tagType = tag.get('type')
    if tagType == 'int':
        tagValue = int(tagValue)
    elif tagType == 'float':
        tagValue = float(tagValue)
    return tagValue


# Extra tags to get (if values were not already read from title/name).
_titleTags = ('imdbindex', 'kind', 'year')
_nameTags = ('imdbindex')
_companyTags = ('imdbindex', 'country')

def parseTags(tag, _topLevel=True, _as=None, _infoset2keys=None,
            _key2infoset=None):
    """Recursively parse a tree of tags."""
    # The returned object (usually a _Container subclass, but it can
    # be a string, an int, a float, a list or a dictionary).
    item = None
    if _infoset2keys is None:
        _infoset2keys = {}
    if _key2infoset is None:
        _key2infoset = {}
    name = tagToKey(tag)
    firstChild = tag.find(recursive=False)
    tagStr = (tag.string or u'').strip()
    if not tagStr and name == 'item':
        # Handles 'item' tags containing text and a 'notes' sub-tag.
        tagContent = tag.contents[0]
        if isinstance(tagContent, BeautifulSoup.NavigableString):
            tagStr = (unicode(tagContent) or u'').strip()
    tagType = tag.get('type')
    infoset = tag.get('infoset')
    if infoset:
        _key2infoset[name] = infoset
        _infoset2keys.setdefault(infoset, []).append(name)
    # Here we use tag.name to avoid tags like <item title="company">
    if tag.name in _MAP_TOP_OBJ:
        # One of the subclasses of _Container.
        item = _MAP_TOP_OBJ[name]()
        itemAs = tag.get('access-system')
        if itemAs:
            if not _as:
                _as = itemAs
        else:
            itemAs = _as
        item.accessSystem = itemAs
        tagsToGet = []
        theID = tag.get('id')
        if name == 'movie':
            item.movieID = theID
            tagsToGet = _titleTags
            theTitle = tag.find('title', recursive=False)
            if tag.title:
                item.set_title(tag.title.string)
                tag.title.extract()
        else:
            if name == 'person':
                item.personID = theID
                tagsToGet = _nameTags
                theName = tag.find('long imdb canonical name', recursive=False)
                if not theName:
                    theName = tag.find('name', recursive=False)
            elif name == 'character':
                item.characterID = theID
                tagsToGet = _nameTags
                theName = tag.find('name', recursive=False)
            elif name == 'company':
                item.companyID = theID
                tagsToGet = _companyTags
                theName = tag.find('name', recursive=False)
            if theName:
                item.set_name(theName.string)
            if theName:
                theName.extract()
        for t in tagsToGet:
            if t in item.data:
                continue
            dataTag = tag.find(t, recursive=False)
            if dataTag:
                item.data[tagToKey(dataTag)] = _valueWithType(dataTag,
                                                            dataTag.string)
        if tag.notes:
            item.notes = tag.notes.string
            tag.notes.extract()
        episodeOf = tag.find('episode-of', recursive=False)
        if episodeOf:
            item.data['episode of'] = parseTags(episodeOf, _topLevel=False,
                                        _as=_as, _infoset2keys=_infoset2keys,
                                        _key2infoset=_key2infoset)
            episodeOf.extract()
        cRole = tag.find('current-role', recursive=False)
        if cRole:
            cr = parseTags(cRole, _topLevel=False, _as=_as,
                        _infoset2keys=_infoset2keys, _key2infoset=_key2infoset)
            item.currentRole = cr
            cRole.extract()
        # XXX: big assumption, here.  What about Movie instances used
        #      as keys in dictionaries?  What about other keys (season and
        #      episode number, for example?)
        if not _topLevel:
            #tag.extract()
            return item
        _adder = lambda key, value: item.data.update({key: value})
    elif tagStr:
        if tag.notes:
            notes = (tag.notes.string or u'').strip()
            if notes:
                tagStr += u'::%s' % notes
        else:
            tagStr = _valueWithType(tag, tagStr)
        return tagStr
    elif firstChild:
        firstChildName = tagToKey(firstChild)
        if firstChildName in _TAGS_TO_LIST:
            item = []
            _adder = lambda key, value: item.append(value)
        else:
            item = {}
            _adder = lambda key, value: item.update({key: value})
    else:
        item = {}
        _adder = lambda key, value: item.update({name: value})
    for subTag in tag(recursive=False):
        subTagKey = tagToKey(subTag)
        # Exclude dinamically generated keys.
        if tag.name in _MAP_TOP_OBJ and subTagKey in item._additional_keys():
            continue
        subItem = parseTags(subTag, _topLevel=False, _as=_as,
                        _infoset2keys=_infoset2keys, _key2infoset=_key2infoset)
        if subItem:
            _adder(subTagKey, subItem)
    if _topLevel and name in _MAP_TOP_OBJ:
        # Add information about 'info sets', but only to the top-level object.
        item.infoset2keys = _infoset2keys
        item.key2infoset = _key2infoset
        item.current_info = _infoset2keys.keys()
    return item


def parseXML(xml):
    """Parse a XML string, returning an appropriate object (usually an
    instance of a subclass of _Container."""
    xmlObj = BeautifulSoup.BeautifulStoneSoup(xml,
                convertEntities=BeautifulSoup.BeautifulStoneSoup.XHTML_ENTITIES)
    if xmlObj:
        mainTag = xmlObj.find()
        if mainTag:
            return parseTags(mainTag)
    return None


_re_akas_lang = re.compile('(?:[(])([a-zA-Z]+?)(?: title[)])')
_re_akas_country = re.compile('\(.*?\)')

# akasLanguages, sortAKAsBySimilarity and getAKAsInLanguage code
# copyright of Alberto Malagoli (refactoring by Davide Alberani).
def akasLanguages(movie):
    """Given a movie, return a list of tuples in (lang, AKA) format;
    lang can be None, if unable to detect."""
    lang_and_aka = []
    akas = set((movie.get('akas') or []) +
                (movie.get('akas from release info') or []))
    for aka in akas:
        # split aka
        aka = aka.encode('utf8').split('::')
        # sometimes there is no countries information
        if len(aka) == 2:
            # search for something like "(... title)" where ... is a language
            language = _re_akas_lang.search(aka[1])
            if language:
                language = language.groups()[0]
            else:
                # split countries using , and keep only the first one (it's sufficient)
                country = aka[1].split(',')[0]
                # remove parenthesis
                country = _re_akas_country.sub('', country).strip()
                # given the country, get corresponding language from dictionary
                language = COUNTRY_LANG.get(country)
        else:
            language = None
        lang_and_aka.append((language, aka[0].decode('utf8')))
    return lang_and_aka


def sortAKAsBySimilarity(movie, title, _titlesOnly=True, _preferredLang=None):
    """Return a list of movie AKAs, sorted by their similarity to
    the given title.
    If _titlesOnly is not True, similarity information are returned.
    If _preferredLang is specified, AKAs in the given language will get
    a higher score.
    The return is a list of title, or a list of tuples if _titlesOnly is False."""
    language = movie.guessLanguage()
    # estimate string distance between current title and given title
    m_title = movie['title'].lower()
    l_title = title.lower()
    if isinstance(l_title, unicode):
        l_title = l_title.encode('utf8')
    scores = []
    score = difflib.SequenceMatcher(None, m_title.encode('utf8'), l_title).ratio()
    # set original title and corresponding score as the best match for given title
    scores.append((score, movie['title'], None))
    for language, aka in akasLanguages(movie):
        # estimate string distance between current title and given title
        m_title = aka.lower()
        if isinstance(m_title, unicode):
            m_title = m_title.encode('utf8')
        score = difflib.SequenceMatcher(None, m_title, l_title).ratio()
        # if current language is the same as the given one, increase score
        if _preferredLang and _preferredLang == language:
            score += 1
        scores.append((score, aka, language))
    scores.sort(reverse=True)
    if _titlesOnly:
        return [x[1] for x in scores]
    return scores


def getAKAsInLanguage(movie, lang, _searchedTitle=None):
    """Return a list of AKAs of a movie, in the specified language.
    If _searchedTitle is given, the AKAs are sorted by their similarity
    to it."""
    akas = []
    for language, aka in akasLanguages(movie):
        if lang == language:
            akas.append(aka)
    if _searchedTitle:
        scores = []
        if isinstance(_searchedTitle, unicode):
            _searchedTitle = _searchedTitle.encode('utf8')
        for aka in akas:
            m_aka = aka
            if isinstance(m_aka):
                m_aka = m_aka.encode('utf8')
            scores.append(difflib.SequenceMatcher(None, m_aka.lower(),
                            _searchedTitle.lower()), aka)
        scores.sort(reverse=True)
        akas = [x[1] for x in scores]
    return akas

