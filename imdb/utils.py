# -*- coding: iso-8859-1 -*-
"""
utils module (imdb package).

This module provides basic utilities for the imdb package.

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
from types import InstanceType

from _exceptions import IMDbParserError


# The regular expression for the "long" year format of IMDb, like
# "(1998)" and "1986/II", where the optional roman number (that I call
# "imdbIndex" after the slash is used for movies with the same title
# and year of release.
# XXX: probably L, C, D and M are far too much! ;-)
re_year_index = re.compile(r'\(([0-9\?]{4}(/[IVXLCDM]+)?)\)')

# Match only the imdbIndex (for name strings).
re_index = re.compile(r'^\(([IVXLCDM]+)\)$')


# Common suffixes in surnames.
_sname_suffixes = ('de', 'la', 'der', 'den', 'del', 'y', 'da', 'van',
                    'e', 'von', 'the', 'di', 'du', 'el', 'al')

def canonicalName(name):
    """Return the given name in canonical "Surname, Name" format."""
    if name.find(', ') != -1: return name
    sname = name.split(' ')
    snl = len(sname)
    if snl == 2:
        name = '%s, %s' % (sname[1], sname[0])
    elif snl > 2:
        lsname = [x.lower() for x in sname]
        for suffix in _sname_suffixes:
            if suffix in lsname:
                name = '%s, %s' % (' '.join(sname[1:]), sname[0])
                break
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
    cpi = name.rfind(')')
    if opi != -1 and cpi != -1 and re_index.match(name[opi:cpi+1]):
        imdbIndex = name[opi+1:cpi]
        name = name[:opi].strip()
    if not name:
        raise IMDbParserError, 'invalid name: "%s"' % str(original_n)
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
    name = name_dict.get('name', '')
    if not canonical:
        name = normalizeName(name)
    imdbIndex = name_dict.get('imdbIndex')
    if imdbIndex:
        name += ' (%s)' % imdbIndex
    return name


# List of articles.
# XXX: are 'agapi mou' and  'liebling' articles?
_articles = ('the', 'la', 'a', 'die', 'der', 'le', 'el', "l'", 'il',
            'das', 'les', 'i', 'o', 'ein', 'un', 'de', 'los', 'an',
            'una', 'eine', 'las', 'den', 'gli', 'het', 'en', 'lo', 'to',
            'os', 'as', 'az', 'ha-', 'een', 'det', 'oi', 'ang', 'ta',
            'al-', 'et', 'des', 'dem', 'al', 'uno', "un'", 'ett',
            'mga', 'egy', 'Ï', 'Ç', 'ye', 'eines', 'da', 'els',
            'Ôï', 'Ïé', 'el-', '-al', "'n")

# Articles with spaces.
_spArticles = []
for article in _articles:
    if article[-1] not in ("'", '-'): article += ' '
    _spArticles.append(article)

def canonicalTitle(title):
    """Return the title in the canonic format 'Movie, The'."""
    try:
        if title.split(', ')[-1].lower() in _articles: return title
    except IndexError: pass
    ltitle = title.lower()
    for article in _spArticles:
        if ltitle.startswith(article):
            lart = len(article)
            title = '%s, %s' % (title[lart:], title[:lart])
            if article[-1] == ' ': title = title[:-1]
    return title

def normalizeTitle(title):
    """Return the title in the normal "The Title" format."""
    stitle = title.split(', ')
    if len(stitle) > 1 and stitle[-1].lower() in _articles:
        sep = ' '
        if stitle[-1][-1] in ("'", '-'): sep = ''
        title = '%s%s%s' % (stitle[-1], sep, ', '.join(stitle[:-1]))
    return title


def analyze_title(title, canonical=0):
    """Analyze the given title and return a dictionary with the
    "stripped" title, the kind of the show ("movie", "tv series", etc.),
    the year of production and the optional imdbIndex (a roman number
    used to distinguish between movies with the same title and year).
    If canonical is true, the title is converted to the canonical
    format.
    
    raise an IMDbParserError exception if the title is not valid.
    """
    original_t = title
    title = title.strip()
    year = ''
    kind = ''
    imdbIndex = ''
    # First of all, search for the kind of show.
    # XXX: Number of entries at 27 jan 2005:
    #      {'(mini)': 4858, '(V)': 35501, '(VG)': 4301, '(TV)': 58443}
    #      tv series: 42454
    if title.endswith('(TV)'):
        kind = 'tv movie'
        title = title[:-4]
    elif title.endswith('(V)'):
        kind = 'video movie'
        title = title[:-3]
    elif title.endswith('(mini)'):
        kind = 'tv mini series'
        title = title[:-6]
    elif title.endswith('(VG)'):
        kind = 'video game'
        title = title[:-4]
    title = title.strip()
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
            title = title[:i-1]
    title = title.strip()
    # This is a tv (mini) series: strip the '"' at the begin and at the end.
    # XXX: strip('"') is not used for compatibility with Python 2.0.
    if title and title[0] == title[-1] == '"':
        if not kind:
            kind = 'tv series'
        title = title[1:-1]
    title = title.strip()
    if not title:
        raise IMDbParserError, 'invalid title: "%s"' % str(original_t)
    if canonical:
        title = canonicalTitle(title)
    # 'kind' is one in ('movie', 'tv series', 'tv mini series', 'tv movie'
    #                   'video movie', 'video game')
    result = {'title': title, 'kind': kind or 'movie'}
    if year and year != '????':
        result['year'] = year
    if imdbIndex:
        result['imdbIndex'] = imdbIndex
    return result


def build_title(title_dict, canonical=0):
    """Given a dictionary that represents a "long" IMDb title,
    return a string.

    If canonical is not true, the title is returned in the
    normal format.
    """
    title = title_dict.get('title', '')
    if not canonical:
        title = normalizeTitle(title)
    kind = title_dict.get('kind')
    imdbIndex = title_dict.get('imdbIndex')
    year = title_dict.get('year', '????')
    if kind in ('tv series', 'tv mini series'):
        title = '"%s"' % title
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
    return title.strip()


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

def modHtmlLinks(s, titlesRefs, namesRefs):
    """Substitute references with links to the IMDb web server."""
    for title, movieO in titlesRefs.items():
        movieID = movieO.movieID
        if not movieID: continue
        s = s.replace('_%s_ (qv)' % title,
                        '<a href="http://akas.imdb.com/title/tt%s">%s</a>' %
                        (movieID, title))
    for name, personO in namesRefs.items():
        personID = personO.personID
        if not personID: continue
        s = s.replace("'%s' (qv)" % name,
                        '<a href="http://akas.imdb.com/name/nm%s">%s</a>' %
                        (personID, name))
    # Remove also non referenced entries.
    s = modClearRefs(s, {}, {})
    return s


_stypes = (type(''), type(u''))
_ltype = type([])
_dtype = type({})

def modifyStrings(o, modFunct, titlesRefs, namesRefs):
    """Modify a string (or strings values in a dictionary or strings
    in a list), using the provided modFunct function and titlesRefs
    and namesRefs references dictionaries."""
    to = type(o)
    if to in _stypes:
        return modFunct(o, titlesRefs, namesRefs)
    elif to is _ltype:
        no = []
        noapp = no.append
        for i in xrange(len(o)):
            ti = type(o[i])
            if ti is InstanceType:
                noapp(o[i])
            else:
                noapp(modifyStrings(o[i], modFunct, titlesRefs, namesRefs))
    elif to is _dtype:
        no = {}
        for k, v in o.items():
            tv = type(v)
            if tv is InstanceType:
                no[k] = v
            else:
                no[k] = modifyStrings(v, modFunct, titlesRefs, namesRefs)
    else:
        return o
    return no


