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

from __future__ import generators
import re
import string
from types import UnicodeType, StringType, ListType, TupleType, DictType
from copy import copy, deepcopy
from time import strptime, strftime

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

re_episode_info = re.compile(r'{(.+?)?\s?(\([0-9\?]{4}-[0-9\?]{1,2}-[0-9\?]{1,2}\))?\s?(\(#[0-9]+\.[0-9]+\))?}')

# Common suffixes in surnames.
_sname_suffixes = ('de', 'la', 'der', 'den', 'del', 'y', 'da', 'van',
                    'e', 'von', 'the', 'di', 'du', 'el', 'al')

def canonicalName(name):
    """Return the given name in canonical "Surname, Name" format.
    It assumes that name is in the 'Name Surname' format."""
    # XXX: some statistics (over 1852406 names):
    #      - just a surname:                 51921
    #      - single surname, single name:  1792759
    #      - composed surname, composed name: 7726
    #      - composed surname, single name:  55623
    #        (2: 49259, 3: 5502, 4: 551)
    #      - single surname, composed name: 186604
    #        (2: 178315, 3: 6573, 4: 1219, 5: 352)
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
    name = name_dict.get('canonical name') or name_dict.get('name', '')
    if not name: return u''
    if not canonical:
        name = normalizeName(name)
    imdbIndex = name_dict.get('imdbIndex')
    if imdbIndex:
        name += ' (%s)' % imdbIndex
    return name


# List of articles.
# XXX: Managing titles in a lot of different languages, a function to recognize
# an initial article can't be perfect; sometimes we'll stumble upon a short
# word that is an article in some language, but it's not in another; in these
# situations we have to choose if we want to interpret this little word
# as an article or not (remember that we don't know what the original language
# of the title was).
# Example: 'da' is an article in (I think) Dutch and it's used as an article
# even in some American slangs.  Unfortunately it's also a preposition in
# Italian, and it's widely used in Mandarin (for whatever it means!).
# Running a script over the whole list of titles (and aliases), I've found
# that 'da' is used as an article only 20 times, and as another thing 255
# times, so I've decided to _always_ consider 'da' as a non article.
#
# Here is a list of words that are _never_ considered as articles, complete
# with the cound of times they are used in a way or another:
# 'en' (314 vs 507), 'to' (236 vs 589), 'as' (183 vs 231), 'et' (67 vs 79),
# 'des' (69 vs 123), 'al' (57 vs 247), 'egy' (28 vs 32), 'ye' (14 vs 55),
# 'da' (20 vs 255), "'n" (7 vs 12)
#
# I've left in the list 'i' (1614 vs 1707) and 'uno' (49 vs 51)
# I'm not sure what '-al' is, and so I've left it out...
#
# List of articles:
_articles = ('the', 'la', 'a', 'die', 'der', 'le', 'el',
            "l'", 'il', 'das', 'les', 'o', 'ein', 'i', 'un', 'los', 'de',
            'an', 'una', 'las', 'eine', 'den', 'gli', 'het', 'os', 'lo',
            'az', 'det', 'ha-', 'een', 'ang', 'oi', 'ta', 'al-', 'dem',
            'mga', 'uno', "un'", 'ett', u'\xcf', 'eines', u'\xc7', 'els',
            u'\xd4\xef', u'\xcf\xe9')

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


def _split_series_episode(title):
    """Return the series and the episode titles; if this is not a
    series' episode, the returned series title is empty.
    This function recognize two different styles:
        "The Series" An Episode (2005)
        "The Series" (2004) {An Episode (2005) (#season.episode)}"""
    series_title = ''
    episode_or_year = ''
    if title[-1:] == '}':
        # Title of the episode, as in the plain text data files.
        begin_eps = title.rfind('{')
        if begin_eps == -1: return '', ''
        series_title = title[:begin_eps].rstrip()
        # episode_or_year is returned with the {...}
        episode_or_year = title[begin_eps:]
        if episode_or_year[:12] == '{SUSPENDED}}': return '', ''
    # XXX: works only with tv series; it's still unclear whether
    #      IMDb will support episodes for tv mini series and tv movies...
    elif title[0:1] == '"':
        second_quot = title[1:].find('"') + 2
        if second_quot != 1: # a second " was found.
            episode_or_year = title[second_quot:].lstrip()
            first_char = episode_or_year[0:1]
            if not first_char: return '', ''
            if first_char != '(':
                # There is not a (year) but the title of the episode;
                # that means this is an episode title, as returned by
                # the web server.
                series_title = title[:second_quot]
            ##elif episode_or_year[-1:] == '}':
            ##        # Title of the episode, as in the plain text data files.
            ##        begin_eps = episode_or_year.find('{')
            ##        if begin_eps == -1: return series_title, episode_or_year
            ##        series_title = title[:second_quot+begin_eps].rstrip()
            ##        # episode_or_year is returned with the {...}
            ##        episode_or_year = episode_or_year[begin_eps:]
    return series_title, episode_or_year


def is_series_episode(title):
    """Return True if 'title' is an series episode."""
    title = title.strip()
    if _split_series_episode(title)[0]: return 1
    return 0


def analyze_title(title, canonical=None,
                    canonicalSeries=0, canonicalEpisode=0):
    """Analyze the given title and return a dictionary with the
    "stripped" title, the kind of the show ("movie", "tv series", etc.),
    the year of production and the optional imdbIndex (a roman number
    used to distinguish between movies with the same title and year).
    If canonical is true, the title is converted to the canonical
    format.

    raise an IMDbParserError exception if the title is not valid.
    """
    if canonical is not None:
        canonicalSeries = canonicalEpisode = canonical
    original_t = title
    result = {}
    title = title.strip()
    year = ''
    kind = ''
    imdbIndex = ''
    series_title, episode_or_year = _split_series_episode(title)
    if series_title:
        # It's an episode of a series.
        series_d = analyze_title(series_title, canonical=canonicalEpisode)
        oad = sen = ep_year = ''
        # Plain text data files format.
        if episode_or_year[0:1] == '{' and episode_or_year[-1:] == '}':
            match = re_episode_info.findall(episode_or_year)
            if match:
                # Episode title, original air date and #season.episode
                episode_or_year, oad, sen = match[0]
                if not oad:
                    # No year, but the title is something like (2005-04-12)
                    if episode_or_year and episode_or_year[0] == '(' and \
                                    episode_or_year[-1:] == ')' and \
                                    episode_or_year[1:2] != '#':
                        oad = episode_or_year
                        if oad[1:5] and oad[5:6] == '-':
                            ep_year = oad[1:5]
                if not oad and not sen and episode_or_year.startswith('(#'):
                    sen = episode_or_year
        elif episode_or_year.startswith('Episode dated'):
            oad = episode_or_year[14:]
            if oad[-4:].isdigit():
                ep_year = oad[-4:]
        episode_d = analyze_title(episode_or_year, canonical=canonicalEpisode)
        episode_d['kind'] = 'episode'
        episode_d['episode of'] = series_d
        if oad:
            episode_d['original air date'] = oad[1:-1]
            if ep_year and episode_d.get('year') is None:
                episode_d['year'] = ep_year
        if sen:
            seas, epn = sen[2:-1].split('.')
            if seas:
                # Set season and episode.
                try: seas = int(seas)
                except: pass
                try: epn = int(epn)
                except: pass
                episode_d['season'] = seas
                episode_d['episode'] = epn
        return episode_d
    # First of all, search for the kind of show.
    # XXX: Number of entries at 18 Mar 2006:
    #      movie:        344,892
    #      episode:      272,862
    #      tv movie:      53,269
    #      tv series:     37,065
    #      video movie:   44,062
    #      tv mini series: 4,757
    #      video game:     4,472
    #      More up-to-date statistics: http://us.imdb.com/database_statistics
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
    # 'kind' is one in ('movie', 'episode', 'tv series', 'tv mini series',
    #                   'tv movie', 'video movie', 'video game')
    result['title'] = title
    result['kind'] = kind or 'movie'
    if year and year != '????':
        result['year'] = str(year)
    if imdbIndex:
        result['imdbIndex'] = str(imdbIndex)
    return result


_web_format = '%d %B %Y'
_ptdf_format = '(%Y-%m-%d)'
def _convertTime(title, fromPTDFtoWEB=1):
    """Convert a time expressed in the pain text data files, to
    the 'Episode dated ...' format used on the web site; if
    fromPTDFtoWEB is false, the inverted conversion is applied."""
    try:
        if fromPTDFtoWEB:
            from_format = _ptdf_format
            to_format = _web_format
        else:
            from_format = 'Episode dated %s' % _web_format
            to_format = _ptdf_format
        t = strptime(title, from_format)
        title = strftime(to_format, t)
        if fromPTDFtoWEB:
            if title[0] == '0': title = title[1:]
            title = 'Episode dated %s' % title
    except ValueError:
        pass
    return title


def build_title(title_dict, canonical=None,
                canonicalSeries=0, canonicalEpisode=0, ptdf=0, _doYear=1):
    """Given a dictionary that represents a "long" IMDb title,
    return a string.

    If canonical is not true, the title is returned in the
    normal format.

    If ptdf is true, the plain text data files format is used.
    """
    if canonical is not None:
        canonicalSeries = canonicalEpisode = canonical
    pre_title = ''
    kind = title_dict.get('kind')
    episode_of = title_dict.get('episode of')
    if kind == 'episode' and episode_of is not None:
        # Works with both Movie instances and plain dictionaries.
        doYear = 0
        if ptdf:
            doYear = 1
        pre_title = build_title(episode_of, canonical=canonicalSeries,
                                ptdf=0, _doYear=doYear)
        ep_dict = {'title': title_dict.get('title', ''),
                    'imdbIndex': title_dict.get('imdbIndex')}
        ep_title = ep_dict['title']
        if not ptdf:
            doYear = 1
            ep_dict['year'] = title_dict.get('year') or '????'
            if ep_title[0:1] == '(' and ep_title[-1:] == ')' and \
                    ep_title[1:5].isdigit():
                ep_dict['title'] = _convertTime(ep_title, fromPTDFtoWEB=1)
        else:
            doYear = 0
            if ep_title.startswith('Episode dated'):
                ep_dict['title'] = _convertTime(ep_title, fromPTDFtoWEB=0)
        episode_title = build_title(ep_dict,
                            canonical=canonicalEpisode, ptdf=ptdf,
                            _doYear=doYear)
        if ptdf:
            oad = title_dict.get('original air date', '')
            if len(oad) == 10 and oad[4] == '-' and oad[7] == '-' and \
                        episode_title.find(oad) == -1:
                episode_title += ' (%s)' % oad
            seas = title_dict.get('season')
            if seas is not None:
                episode_title += ' (#%s' % seas
                episode = title_dict.get('episode')
                if episode is not None:
                    episode_title += '.%s' % episode
                episode_title += ')'
            episode_title = '{%s}' % episode_title
        return '%s %s' % (pre_title, episode_title)
    title = title_dict.get('canonical title') or title_dict.get('title', '')
    if not title: return u''
    if not canonical:
        title = normalizeTitle(title)
    if pre_title:
        title = '%s %s' % (pre_title, title)
    if kind in ('tv series', 'tv mini series'):
        title = '"%s"' % title
    if _doYear:
        imdbIndex = title_dict.get('imdbIndex')
        year = title_dict.get('year') or '????'
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
    # It should works also with normal dictionaries (returned from searches).
    if m1t is _last and m2t is _last:
        m1t = m1.get('title', _last)
        m2t = m2.get('title', _last)
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
    if p1n is _last and p2n is _last:
        p1n = p1.get('name', _last)
        p2n = p2.get('name', _last)
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


def modifyStrings(o, modFunct, titlesRefs, namesRefs):
    """Modify a string (or string values in a dictionary or strings
    in a list), using the provided modFunct function and titlesRefs
    and namesRefs references dictionaries."""
    if isinstance(o, (UnicodeType, StringType)):
        return modFunct(o, titlesRefs, namesRefs)
    elif isinstance(o, (ListType, TupleType)):
        _stillorig = 1
        if isinstance(o, ListType): keys = xrange(len(o))
        else: keys = o.keys()
        for i in keys:
            v = o[i]
            if isinstance(v, (UnicodeType, StringType)):
                if _stillorig:
                    o = copy(o)
                    _stillorig = 0
                o[i] = modFunct(v, titlesRefs, namesRefs)
            elif isinstance(v, (ListType, TupleType)):
                modifyStrings(o[i], modFunct, titlesRefs, namesRefs)
    return o


def flatten(seq, to_descend=(ListType, DictType, TupleType),
            yieldDictKeys=0, scalar=None):
    """Iterate over nested lists and dictionaries; to_descend is a type
    of a tuple of types to be considered non-scalar; if yieldDictKeys is
    true, also dictionaries' keys are yielded; if scalar is not None, only
    items of the given type(s) are yielded."""
    if not isinstance(seq, to_descend):
        if scalar is None or isinstance(seq, scalar):
            yield seq
    else:
        if isinstance(seq, DictType):
            if yieldDictKeys:
                # Yield also the keys of the dictionary.
                for key in seq.iterkeys():
                    for k in flatten(key, to_descend=to_descend,
                                yieldDictKeys=yieldDictKeys, scalar=scalar):
                        yield k
            for value in seq.itervalues():
                for v in flatten(value, to_descend=to_descend,
                                yieldDictKeys=yieldDictKeys, scalar=scalar):
                    yield v
        else:
            for item in seq:
                for i in flatten(item, to_descend=to_descend,
                                yieldDictKeys=yieldDictKeys, scalar=scalar):
                    yield i


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

    def getID(self):
        """Return movie or person ID."""
        raise NotImplementedError, 'override this method'

    def __cmp__(self, other):
        """Compare two Movie or Person objects."""
        # XXX: only check the title/name and the movieID/personID?
        # XXX: comparison should be used to sort movies/person?
        if not isinstance(other, self.__class__):
            return -1
        if self.data == other.data:
            return 0
        return 1

    def __hash__(self):
        """Hash for this object."""
        # XXX: does it always work correctly?
        theID = self.getID()
        if theID is not None and self.accessSystem not in ('UNKNOWN', None):
            s4h = '%s:%s' % (self.accessSystem, theID)
        else:
            s4h = repr(self)
        return hash(s4h)

    def isSame(self, other):
        if not isinstance(other, self.__class__): return 0
        if hash(self) == hash(other): return 1
        return 0

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

    def __repr__(self):
        """String representation of an object."""
        raise NotImplementedError, 'override this method'

    def __str__(self):
        """Movie title or person name."""
        raise NotImplementedError, 'override this method'

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


