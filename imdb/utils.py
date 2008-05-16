"""
utils module (imdb package).

This module provides basic utilities for the imdb package.

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

from __future__ import generators
import re
from types import UnicodeType, StringType, ListType, TupleType, DictType
from copy import copy, deepcopy
from time import strptime, strftime

from imdb._exceptions import IMDbParserError, IMDbError

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
    # XXX: some statistics (as of 17 Apr 2008, over 2288622 names):
    #      - just a surname:                 69476
    #      - single surname, single name:  2209656
    #      - composed surname, composed name: 9490
    #      - composed surname, single name:  67606
    #        (2: 59764, 3: 6862, 4: 728)
    #      - single surname, composed name: 242310
    #        (2: 229467, 3: 9901, 4: 2041, 5: 630)
    #      - Jr.: 8025
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
    if not name: return ''
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
# that 'da' is used as an article only 23 times, and as another thing 298
# times, so I've decided to _always_ consider 'da' as a non article.
#
# Here is a list of words that are _never_ considered as articles, complete
# with the cound of times they are used in a way or another:
# 'en' (376 vs 594), 'to' (399 vs 727), 'as' (198 vs 276), 'et' (79 vs 99),
# 'des' (75 vs 150), 'al' (78 vs 304), 'ye' (14 vs 70),
# 'da' (23 vs 298), "'n" (8 vs 12)
#
# I've left in the list 'i' (1939 vs 2151) and 'uno' (52 vs 56)
# I'm not sure what '-al' is, and so I've left it out...
#
# List of articles:
_articles = ('the', 'la', 'a', 'die', 'der', 'le', 'el',
            "l'", 'il', 'das', 'les', 'i', 'o', 'ein', 'un', 'de', 'los',
            'an', 'una', 'las', 'eine', 'den', 'het', 'gli', 'lo', 'os',
            'ang', 'oi', 'az', 'een', 'ha-', 'det', 'ta', 'al-',
            'mga', "un'", 'uno', 'ett', 'dem', 'egy', 'els', 'eines', u'\xcf',
            u'\xc7', u'\xd4\xef', u'\xcf\xe9')

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
                    canonicalSeries=0, canonicalEpisode=0,
                    _emptyString=u''):
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
    year = _emptyString
    kind = _emptyString
    imdbIndex = _emptyString
    series_title, episode_or_year = _split_series_episode(title)
    if series_title:
        # It's an episode of a series.
        series_d = analyze_title(series_title, canonical=canonicalSeries)
        oad = sen = ep_year = _emptyString
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
        episode_d['kind'] = u'episode'
        episode_d['episode of'] = series_d
        if oad:
            episode_d['original air date'] = oad[1:-1]
            if ep_year and episode_d.get('year') is None:
                episode_d['year'] = ep_year
        if sen and sen[2:-1].find('.') != -1:
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
    # XXX: Number of entries at 17 Apr 2008:
    #      movie:        379,871
    #      episode:      483,832
    #      tv movie:      61,119
    #      tv series:     44,795
    #      video movie:   57,915
    #      tv mini series: 5,497
    #      video game:     5,490
    #      More up-to-date statistics: http://us.imdb.com/database_statistics
    if title.endswith('(TV)'):
        kind = u'tv movie'
        title = title[:-4].rstrip()
    elif title.endswith('(V)'):
        kind = u'video movie'
        title = title[:-3].rstrip()
    elif title.endswith('(mini)'):
        kind = u'tv mini series'
        title = title[:-6].rstrip()
    elif title.endswith('(VG)'):
        kind = u'video game'
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
            kind = u'tv series'
        title = title[1:-1].strip()
    if not title:
        raise IMDbParserError, 'invalid title: "%s"' % original_t
    if canonical:
        title = canonicalTitle(title)
    # 'kind' is one in ('movie', 'episode', 'tv series', 'tv mini series',
    #                   'tv movie', 'video movie', 'video game')
    result['title'] = title
    result['kind'] = kind or u'movie'
    if year and year != '????':
        result['year'] = year
    if imdbIndex:
        result['imdbIndex'] = imdbIndex
    if isinstance(_emptyString, str):
        result['kind'] = str(kind or 'movie')
        if year and year != '????': result['year'] = str(year)
    return result


_web_format = '%d %B %Y'
_ptdf_format = '(%Y-%m-%d)'
def _convertTime(title, fromPTDFtoWEB=1, _emptyString=u''):
    """Convert a time expressed in the pain text data files, to
    the 'Episode dated ...' format used on the web site; if
    fromPTDFtoWEB is false, the inverted conversion is applied."""
    try:
        if fromPTDFtoWEB:
            from_format = _ptdf_format
            to_format = _web_format
        else:
            from_format = u'Episode dated %s' % _web_format
            to_format = _ptdf_format
        t = strptime(title, from_format)
        title = strftime(to_format, t)
        if fromPTDFtoWEB:
            if title[0] == '0': title = title[1:]
            title = u'Episode dated %s' % title
    except ValueError:
        pass
    if isinstance(_emptyString, str):
        try:
            title = str(title)
        except UnicodeDecodeError:
            pass
    return title


def build_title(title_dict, canonical=None, canonicalSeries=0,
                canonicalEpisode=0, ptdf=0, _doYear=1, _emptyString=u''):
    """Given a dictionary that represents a "long" IMDb title,
    return a string.

    If canonical is not true, the title is returned in the
    normal format.

    If ptdf is true, the plain text data files format is used.
    """
    if canonical is not None:
        canonicalSeries = canonical
    pre_title = _emptyString
    kind = title_dict.get('kind')
    episode_of = title_dict.get('episode of')
    if kind == 'episode' and episode_of is not None:
        # Works with both Movie instances and plain dictionaries.
        doYear = 0
        if ptdf:
            doYear = 1
        pre_title = build_title(episode_of, canonical=canonicalSeries,
                                ptdf=0, _doYear=doYear,
                                _emptyString=_emptyString)
        ep_dict = {'title': title_dict.get('title', ''),
                    'imdbIndex': title_dict.get('imdbIndex')}
        ep_title = ep_dict['title']
        if not ptdf:
            doYear = 1
            ep_dict['year'] = title_dict.get('year') or '????'
            if ep_title[0:1] == '(' and ep_title[-1:] == ')' and \
                    ep_title[1:5].isdigit():
                ep_dict['title'] = _convertTime(ep_title, fromPTDFtoWEB=1,
                                                _emptyString=_emptyString)
        else:
            doYear = 0
            if ep_title.startswith('Episode dated'):
                ep_dict['title'] = _convertTime(ep_title, fromPTDFtoWEB=0,
                                                _emptyString=_emptyString)
        episode_title = build_title(ep_dict,
                            canonical=canonicalEpisode, ptdf=ptdf,
                            _doYear=doYear, _emptyString=_emptyString)
        if ptdf:
            oad = title_dict.get('original air date', _emptyString)
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
    if not title: return _emptyString
    if not canonical:
        title = normalizeTitle(title)
    if pre_title:
        title = '%s %s' % (pre_title, title)
    if kind in (u'tv series', u'tv mini series'):
        title = '"%s"' % title
    if _doYear:
        imdbIndex = title_dict.get('imdbIndex')
        year = title_dict.get('year') or u'????'
        if isinstance(_emptyString, str):
            year = str(year)
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


def split_company_name_notes(name):
    """Return two strings, the first representing the company name,
    and the other representing the (optional) notes."""
    name = name.strip()
    notes = u''
    if name.endswith(')'):
        fpidx = name.find('(')
        if fpidx != -1:
            notes = name[fpidx:]
            name = name[:fpidx].rstrip()
    return name, notes


def analyze_company_name(name, stripNotes=False):
    """Return a dictionary with the name and the optional 'country'
    keys, from the given string.
    If stripNotes is true, tries to not consider optional notes.

    raise an IMDbParserError exception if the name is not valid.
    """
    if stripNotes:
        name = split_company_name_notes(name)[0]
    o_name = name
    name = name.strip()
    country = None
    if name.endswith(']'):
        idx = name.rfind('[')
        if idx != -1:
            country = name[idx:]
            name = name[:idx-1].rstrip()
    if not name:
        raise IMDbParserError, 'invalid name: "%s"' % o_name
    result = {'name': name}
    if country:
        result['country'] = country
    return result


def build_company_name(name_dict, _emptyString=u''):
    """Given a dictionary that represents a "long" IMDb company name,
    return a string.
    """
    name = name_dict.get('name')
    if not name:
        return _emptyString
    country = name_dict.get('country')
    if country is not None:
        name += ' %s' % country
    return name


class _LastC:
    """Size matters."""
    def __cmp__(self, other):
        if isinstance(other, self.__class__): return 0
        return 1

_last = _LastC()

def cmpMovies(m1, m2):
    """Compare two movies by year, in reverse order; the imdbIndex is checked
    for movies with the same year of production and title."""
    # Sort tv series' episodes.
    m1e = m1.get('episode of')
    m2e = m2.get('episode of')
    if m1e is not None and m2e is not None:
        cmp_series = cmpMovies(m1e, m2e)
        if cmp_series != 0:
            return cmp_series
        m1s = m1.get('season')
        m2s = m2.get('season')
        if m1s is not None and m2s is not None:
            if m1s < m2s:
                return 1
            elif m1s > m2s:
                return -1
            m1p = m1.get('episode')
            m2p = m2.get('episode')
            if m1p < m2p:
                return 1
            elif m1p > m2p:
                return -1
    if m1e is None: m1y = int(m1.get('year', 0))
    else: m1y = int(m1e.get('year', 0))
    if m2e is None: m2y = int(m2.get('year', 0))
    else: m2y = int(m2e.get('year', 0))
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


def cmpPeople(p1, p2):
    """Compare two people by billingPos, name and imdbIndex."""
    p1b = getattr(p1, 'billingPos', None) or _last
    p2b = getattr(p2, 'billingPos', None) or _last
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


def cmpCompanies(p1, p2):
    """Compare two companies."""
    p1n = p1.get('long imdb name', _last)
    p2n = p2.get('long imdb name', _last)
    if p1n is _last and p2n is _last:
        p1n = p1.get('name', _last)
        p2n = p2.get('name', _last)
    if p1n > p2n: return 1
    if p1n < p2n: return -1
    p1i = p1.get('country', _last)
    p2i = p2.get('country', _last)
    if p1i > p2i: return 1
    if p1i < p2i: return -1
    return 0


# References to titles, names and characters.
# XXX: find better regexp!
re_titleRef = re.compile(r'_(.+?(?: \([0-9\?]{4}(?:/[IVXLCDM]+)?\))?(?: \(mini\)| \(TV\)| \(V\)| \(VG\))?)_ \(qv\)')
# FIXME: doesn't match persons with ' in the name.
re_nameRef = re.compile(r"'([^']+?)' \(qv\)")
# XXX: good choice?  Are there characters with # in the name?
re_characterRef = re.compile(r"#([^']+?)# \(qv\)")

# Functions used to filter the text strings.
def modNull(s, titlesRefs, namesRefs, charactersRefs):
    """Do nothing."""
    return s

def modClearTitleRefs(s, titlesRefs, namesRefs, charactersRefs):
    """Remove titles references."""
    return re_titleRef.sub(r'\1', s)

def modClearNameRefs(s, titlesRefs, namesRefs, charactersRefs):
    """Remove names references."""
    return re_nameRef.sub(r'\1', s)

def modClearCharacterRefs(s, titlesRefs, namesRefs, charactersRefs):
    """Remove characters references"""
    return re_characterRef.sub(r'\1', s)

def modClearRefs(s, titlesRefs, namesRefs, charactersRefs):
    """Remove titles, names and characters references."""
    s = modClearTitleRefs(s, {}, {}, {})
    s = modClearCharacterRefs(s, {}, {}, {})
    return modClearNameRefs(s, {}, {}, {})


def modifyStrings(o, modFunct, titlesRefs, namesRefs, charactersRefs):
    """Modify a string (or string values in a dictionary or strings
    in a list), using the provided modFunct function and titlesRefs
    namesRefs and charactersRefs references dictionaries."""
    if isinstance(o, (UnicodeType, StringType)):
        return modFunct(o, titlesRefs, namesRefs, charactersRefs)
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
                o[i] = modFunct(v, titlesRefs, namesRefs, charactersRefs)
            elif isinstance(v, (ListType, TupleType)):
                modifyStrings(o[i], modFunct, titlesRefs, namesRefs,
                            charactersRefs)
    return o


def date_and_notes(s):
    """Parse (birth|death) date and notes; returns a tuple in the
    form (date, notes)."""
    s = s.strip()
    if not s: return (u'', u'')
    notes = u''
    if s[0].isdigit() or s.split()[0].lower() in ('c.', 'january', 'february',
                                                'march', 'april', 'may', 'june',
                                                'july', 'august', 'september',
                                                'october', 'november',
                                                'december', 'ca.', 'circa',
                                                '????,'):
        i = s.find(',')
        if i != -1:
            notes = s[i+1:].strip()
            s = s[:i]
    else:
        notes = s
        s = u''
    if s == '????': s = u''
    return s, notes


class RolesList(list):
    """A list of Person or Character instances, used for the currentRole
    property."""
    def __unicode__(self):
        return u' / '.join([unicode(x) for x in self])

    def __str__(self):
        # FIXME: does it make sense at all?  Return a unicode doesn't
        #        seem right, in __str__.
        return u' / '.join([unicode(x).encode('utf8') for x in self])


class _Container(object):
    """Base class for Movie, Person and Character classes."""
     # The default sets of information retrieved.
    default_info = ()

    # Aliases for some not-so-intuitive keys.
    keys_alias = {}

    # List of keys to modify.
    keys_tomodify_list = ()

    cmpFunct = None

    def __init__(self, myID=None, data=None, notes=u'',
                currentRole=u'', roleID=None, roleIsPerson=False,
                accessSystem=None, titlesRefs=None, namesRefs=None,
                charactersRefs=None, modFunct=None, *args, **kwds):
        """Initialize a Movie, Person or Character object.
        *myID* -- your personal identifier for this object.
        *data* -- a dictionary used to initialize the object.
        *notes* -- notes for the person referred in the currentRole
                    attribute; e.g.: '(voice)' or the alias used in the
                    movie credits.
        *accessSystem* -- a string representing the data access system used.
        *currentRole* -- a Character instance representing the current role
                         or duty of a person in this movie, or a Person
                         object representing the actor/actress who played
                         a given character in a Movie.  If a string is
                         passed, an object is automatically build.
        *roleID* -- if available, the characterID/personID of the currentRole
                    object.
        *roleIsPerson* -- when False (default) the currentRole is assumed
                          to be a Character object, otherwise a Person.
        *titlesRefs* -- a dictionary with references to movies.
        *namesRefs* -- a dictionary with references to persons.
        *charactersRefs* -- a dictionary with references to characters.
        *modFunct* -- function called returning text fields.
        """
        self.reset()
        self.accessSystem = accessSystem
        self.myID = myID
        if data is None: data = {}
        self.set_data(data, override=1)
        self.notes = notes
        if titlesRefs is None: titlesRefs = {}
        self.update_titlesRefs(titlesRefs)
        if namesRefs is None: namesRefs = {}
        self.update_namesRefs(namesRefs)
        if charactersRefs is None: charactersRefs = {}
        self.update_charactersRefs(charactersRefs)
        self.set_mod_funct(modFunct)
        self.keys_tomodify = {}
        for item in self.keys_tomodify_list:
            self.keys_tomodify[item] = None
        self._roleIsPerson = roleIsPerson
        if not roleIsPerson:
            from imdb.Character import Character
            self._roleClass = Character
        else:
            from imdb.Person import Person
            self._roleClass = Person
        self.currentRole = currentRole
        if roleID:
            self.roleID = roleID
        self._init(*args, **kwds)

    def _get_roleID(self):
        """Return the characterID or personID of the currentRole object."""
        if not self.__role:
            return None
        if isinstance(self.__role, list):
            return [x.getID() for x in self.__role]
        return self.currentRole.getID()

    def _set_roleID(self, roleID):
        """Set the characterID or personID of the currentRole object."""
        if not self.__role:
            # XXX: needed?  Just ignore it?  It's probably safer to
            #      ignore it, to prevent some bugs in the parsers.
            raise IMDbError, "Can't set ID of an empty Character/Person object."
        if not self._roleIsPerson:
            if not isinstance(roleID, (list, tuple)):
                self.currentRole.characterID = roleID
            else:
                for index, item in enumerate(roleID):
                    self.__role[index].characterID = item
        else:
            if not isinstance(roleID, (list, tuple)):
                self.currentRole.personID = roleID
            else:
                for index, item in enumerate(roleID):
                    self.__role[index].personID = item

    roleID = property(_get_roleID, _set_roleID,
                doc="the characterID or personID of the currentRole object.")

    def _get_currentRole(self):
        """Return a Character or Person instance."""
        if self.__role:
            return self.__role
        return self._roleClass(name=u'', accessSystem=self.accessSystem,
                                modFunct=self.modFunct)

    def _set_currentRole(self, role):
        """Set self.currentRole to a Character or Person instance."""
        if isinstance(role, (UnicodeType, StringType)):
            if not role:
                self.__role = None
            else:
                self.__role = self._roleClass(name=role, modFunct=self.modFunct,
                                        accessSystem=self.accessSystem)
        elif isinstance(role, (list, tuple)):
            self.__role = RolesList()
            for item in role:
                if isinstance(item, (UnicodeType, StringType)):
                    self.__role.append(self._roleClass(name=item,
                                        accessSystem=self.accessSystem,
                                        modFunct=self.modFunct))
                else:
                    self.__role.append(item)
            if not self.__role:
                self.__role = None
        else:
            self.__role = role

    currentRole = property(_get_currentRole, _set_currentRole,
                            doc="The role of a Person in a Movie" + \
                            " or the interpreter of a Character in a Movie.")

    def _init(self, **kwds): pass

    def reset(self):
        """Reset the object."""
        self.data = {}
        self.myID = None
        self.notes = u''
        self.titlesRefs = {}
        self.namesRefs = {}
        self.charactersRefs = {}
        self.modFunct = modClearRefs
        self.current_info = []
        self.__role = None
        self._reset()

    def _reset(self): pass

    def clear(self):
        """Reset the dictionary."""
        self.data.clear()
        self.notes = u''
        self.titlesRefs = {}
        self.namesRefs = {}
        self.charactersRefs = {}
        self.current_info = []
        self.__role = None
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

    def update_charactersRefs(self, charactersRefs):
        """Update the dictionary with the references to characters."""
        self.charactersRefs.update(charactersRefs)

    def get_charactersRefs(self):
        """Return the dictionary with the references to characters."""
        return self.charactersRefs

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
        """Return movieID, personID, characterID or companyID."""
        raise NotImplementedError, 'override this method'

    def __cmp__(self, other):
        """Compare two Movie, Person, Character or Company objects."""
        # XXX: raise an exception?
        if self.cmpFunct is None: return -1
        if not isinstance(other, self.__class__): return -1
        return self.cmpFunct(other)

    def __hash__(self):
        """Hash for this object."""
        # XXX: does it always work correctly?
        theID = self.getID()
        if theID is not None and self.accessSystem not in ('UNKNOWN', None):
            # Handle 'http' and 'mobile' as they are the same access system.
            acs = self.accessSystem
            if acs in ('mobile', 'httpThin'):
                acs = 'http'
            s4h = '%s:%s' % (acs, theID)
        else:
            s4h = repr(self)
        return hash(s4h)

    def isSame(self, other):
        """Return True if the two represent the same object."""
        if not isinstance(other, self.__class__): return 0
        if hash(self) == hash(other): return 1
        return 0

    def __len__(self):
        """Number of items in the data dictionary."""
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
            try:
                return modifyStrings(rawData, self.modFunct, self.titlesRefs,
                                    self.namesRefs, self.charactersRefs)
            except RuntimeError, e:
                # Symbian/python 2.2 has a poor regexp implementation.
                import warnings
                warnings.warn('RuntimeError in '
                        "imdb.utils._Container.__getitem__; if it's not "
                        "a recursion limit exceeded or we're not running "
                        "in a Symbian environment, it's a bug:\n%s" % e)
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

    # XXX: is this enough?
    def iteritems(self): return self.data.iteritems()
    def iterkeys(self): return self.data.iterkeys()
    def itervalues(self): return self.data.itervalues()

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

    # XXX: really useful???
    #      consider also that this will confuse people who meant to
    #      call ia.update(movieObject, 'data set') instead.
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


def flatten(seq, toDescend=(ListType, DictType, TupleType),
            yieldDictKeys=0, onlyKeysType=(_Container,), scalar=None):
    """Iterate over nested lists and dictionaries; toDescend is a list
    or a tuple of types to be considered non-scalar; if yieldDictKeys is
    true, also dictionaries' keys are yielded; if scalar is not None, only
    items of the given type(s) are yielded."""
    if not isinstance(seq, toDescend):
        if scalar is None or isinstance(seq, scalar):
            yield seq
    else:
        if isinstance(seq, (DictType, _Container)):
            if yieldDictKeys:
                # Yield also the keys of the dictionary.
                for key in seq.iterkeys():
                    for k in flatten(key, toDescend=toDescend,
                                yieldDictKeys=yieldDictKeys,
                                onlyKeysType=onlyKeysType, scalar=scalar):
                        if onlyKeysType and isinstance(k, onlyKeysType):
                            yield k
            for value in seq.itervalues():
                for v in flatten(value, toDescend=toDescend,
                                yieldDictKeys=yieldDictKeys,
                                onlyKeysType=onlyKeysType, scalar=scalar):
                    yield v
        else:
            for item in seq:
                for i in flatten(item, toDescend=toDescend,
                                yieldDictKeys=yieldDictKeys,
                                onlyKeysType=onlyKeysType, scalar=scalar):
                    yield i


