"""
locsql module (imdb.parser.common package).

This module provides some functions and classes shared amongst
"local" and "sql" parsers.

Copyright 2005-2008 Davide Alberani <da@erlug.linux.it>

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
from difflib import SequenceMatcher
from codecs import lookup

from imdb import IMDbBase
from imdb.Person import Person
from imdb.Movie import Movie
from imdb.utils import analyze_title, build_title, analyze_name, \
                        build_name, canonicalTitle, canonicalName, \
                        normalizeName, normalizeTitle, re_titleRef, \
                        re_nameRef, re_year_index, _articles, \
                        analyze_company_name

re_nameIndex = re.compile(r'\(([IVXLCDM]+)\)')


class IMDbLocalAndSqlAccessSystem(IMDbBase):
    """Base class for methods shared by the 'local' and the 'sql'
    data access systems."""

    def _getTitleID(self, title):
        raise NotImplementedError, 'override this method'

    def _getNameID(self, name):
        raise NotImplementedError, 'override this method'

    def _findRefs(self, o, trefs, nrefs):
        """Find titles or names references in strings."""
        if isinstance(o, (UnicodeType, StringType)):
            for title in re_titleRef.findall(o):
                a_title = analyze_title(title, canonical=1)
                rtitle = build_title(a_title, canonical=1, ptdf=1)
                if trefs.has_key(rtitle): continue
                movieID = self._getTitleID(rtitle)
                if movieID is None:
                    movieID = self._getTitleID(title)
                if movieID is None:
                    continue
                m = Movie(title=rtitle, movieID=movieID,
                            accessSystem=self.accessSystem)
                trefs[rtitle] = m
                rtitle2 = canonicalTitle(a_title.get('title', u''))
                if rtitle2 and rtitle2 != rtitle and rtitle2 != title:
                    trefs[rtitle2] = m
                if title != rtitle:
                    trefs[title] = m
            for name in re_nameRef.findall(o):
                a_name = analyze_name(name, canonical=1)
                rname = build_name(a_name, canonical=1)
                if nrefs.has_key(rname): continue
                personID = self._getNameID(rname)
                if personID is None:
                    personID = self._getNameID(name)
                if personID is None: continue
                p = Person(name=rname, personID=personID,
                            accessSystem=self.accessSystem)
                nrefs[rname] = p
                rname2 = normalizeName(a_name.get('name', u''))
                if rname2 and rname2 != rname:
                    nrefs[rname2] = p
                if name != rname and name != rname2:
                    nrefs[name] = p
        elif isinstance(o, (ListType, TupleType)):
            for item in o:
                self._findRefs(item, trefs, nrefs)
        elif isinstance(o, DictType):
            for value in o.values():
                self._findRefs(value, trefs, nrefs)
        return (trefs, nrefs)

    def _extractRefs(self, o):
        """Scan for titles or names references in strings."""
        trefs = {}
        nrefs = {}
        try:
            return self._findRefs(o, trefs, nrefs)
        except RuntimeError, e:
            # Symbian/python 2.2 has a poor regexp implementation.
            import warnings
            warnings.warn('RuntimeError in '
                    "imdb.parser.common.locsql.IMDbLocalAndSqlAccessSystem; "
                    "if it's not a recursion limit exceeded or we're not "
                    "running in a Symbian environment, it's a bug:\n%s" % e)
            return (trefs, nrefs)

    def _changeAKAencoding(self, akanotes, akatitle):
        """Return akatitle in the correct charset, as specified in
        the akanotes field; if akatitle doesn't need to be modified,
        return None."""
        oti = akanotes.find('(original ')
        if oti == -1: return None
        ote = akanotes[oti+10:].find(' title)')
        if ote != -1:
            cs_info = akanotes[oti+10:oti+10+ote].lower().split()
            for e in cs_info:
                # excludes some strings that clearly are not encoding.
                if e in ('script', '', 'cyrillic', 'greek'): continue
                if e.startswith('iso-') and e.find('latin') != -1:
                    e = e[4:].replace('-', '')
                try:
                    lookup(e)
                    lat1 = akatitle.encode('latin_1', 'replace')
                    return unicode(lat1, e, 'replace')
                except (LookupError, ValueError, TypeError):
                    continue
        return None


def titleVariations(title, fromPtdf=0):
    """Build title variations useful for searches; if fromPtdf is true,
    the input is assumed to be in the plain text data files format."""
    if fromPtdf: title1 = u''
    else: title1 = title
    title2 = title3 = u''
    if fromPtdf or re_year_index.search(title):
        # If it appears to have a (year[/imdbIndex]) indication,
        # assume that a long imdb canonical name was provided.
        titldict = analyze_title(title, canonical=1)
        # title1: the canonical name.
        title1 = titldict['title']
        if titldict['kind'] != 'episode':
            # title3: the long imdb canonical name.
            if fromPtdf: title3 = title
            else: title3 = build_title(titldict, canonical=1, ptdf=1)
        else:
            title1 = normalizeTitle(title1)
            title3 = build_title(titldict, canonical=1, ptdf=1)
    else:
        # Just a title.
        # title1: the canonical title.
        title1 = canonicalTitle(title)
        title3 = u''
    # title2 is title1 without the article, or title1 unchanged.
    if title1:
        title2 = title1
        t2s = title2.split(u', ')
        if t2s[-1].lower() in _articles:
            title2 = u', '.join(t2s[:-1])
    return title1, title2, title3


def nameVariations(name, fromPtdf=0):
    """Build name variations useful for searches; if fromPtdf is true,
    the input is assumed to be in the plain text data files format."""
    name1 = name2 = name3 = u''
    if fromPtdf or re_nameIndex.search(name):
        # We've a name with an (imdbIndex)
        namedict = analyze_name(name, canonical=1)
        # name1 is the name in the canonical format.
        name1 = namedict['name']
        # name3 is the canonical name with the imdbIndex.
        if fromPtdf:
            if namedict.has_key('imdbIndex'):
                name3 = name
        else:
            name3 = build_name(namedict, canonical=1)
    else:
        # name1 is the name in the canonical format.
        name1 = canonicalName(name)
        name3 = u''
    # name2 is the name in the normal format, if it differs from name1.
    name2 = normalizeName(name1)
    if name1 == name2: name2 = u''
    return name1, name2, name3


try:
    from cutils import ratcliff as _ratcliff
    def ratcliff(s1, s2, sm):
        """Return the Ratcliff-Obershelp value between the two strings,
        using the C implementation."""
        return _ratcliff(s1.encode('latin_1', 'replace'),
                        s2.encode('latin_1', 'replace'))
except ImportError:
    import warnings
    warnings.warn('Unable to import the cutils.ratcliff function.'
                    '  Searching names and titles using the "sql" and "local"'
                    ' data access systems will be slower.')

    def ratcliff(s1, s2, sm):
        """Ratcliff-Obershelp similarity."""
        STRING_MAXLENDIFFER = 0.7
        s1len = len(s1)
        s2len = len(s2)
        if s1len < s2len:
            threshold = float(s1len) / s2len
        else:
            threshold = float(s2len) / s1len
        if threshold < STRING_MAXLENDIFFER:
            return 0.0
        sm.set_seq2(s2.lower())
        return sm.ratio()


def merge_roles(mop):
    """Merge multiple roles."""
    new_list = []
    for m in mop:
        if m in new_list:
            keep_this = new_list[new_list.index(m)]
            if not isinstance(keep_this.currentRole, list):
                keep_this.currentRole = [keep_this.currentRole]
            keep_this.currentRole.append(m.currentRole)
        else:
            new_list.append(m)
    return new_list


def scan_names(name_list, name1, name2, name3, results=0, ro_thresold=None,
                _scan_character=False):
    """Scan a list of names, searching for best matches against
    the given variations."""
    if ro_thresold is not None: RO_THRESHOLD = ro_thresold
    else: RO_THRESHOLD = 0.6
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm3 = SequenceMatcher()
    sm1.set_seq1(name1.lower())
    if name2: sm2.set_seq1(name2.lower())
    if name3: sm3.set_seq1(name3.lower())
    resd = {}
    for i, n_data in name_list:
        nil = n_data['name']
        # XXX: on Symbian, here we get a str; not sure this is the
        #      right place to fix it.
        if isinstance(nil, str):
            nil = unicode(nil, 'latin1', 'ignore')
        # Distance with the canonical name.
        ratios = [ratcliff(name1, nil, sm1) + 0.05]
        namesurname = u''
        if not _scan_character:
            nils = nil.split(', ', 1)
            surname = nils[0]
            if len(nils) == 2: namesurname = '%s %s' % (nils[1], surname)
        else:
            nils = nil.split(' ', 1)
            surname = nils[-1]
            namesurname = nil
        if surname != nil:
            # Distance with the "Surname" in the database.
            ratios.append(ratcliff(name1, surname, sm1))
            if not _scan_character:
                ratios.append(ratcliff(name1, namesurname, sm1))
            if name2:
                ratios.append(ratcliff(name2, surname, sm2))
                # Distance with the "Name Surname" in the database.
                if namesurname:
                    ratios.append(ratcliff(name2, namesurname, sm2))
        if name3:
            # Distance with the long imdb canonical name.
            ratios.append(ratcliff(name3,
                        build_name(n_data, canonical=1), sm3) + 0.1)
        ratio = max(ratios)
        if ratio >= RO_THRESHOLD:
            if resd.has_key(i):
                if ratio > resd[i][0]: resd[i] = (ratio, (i, n_data))
            else: resd[i] = (ratio, (i, n_data))
    res = resd.values()
    res.sort()
    res.reverse()
    if results > 0: res[:] = res[:results]
    return res


def scan_titles(titles_list, title1, title2, title3, results=0,
                searchingEpisode=0, ro_thresold=None):
    """Scan a list of titles, searching for best matches against
    the given variations."""
    if ro_thresold is not None: RO_THRESHOLD = ro_thresold
    else: RO_THRESHOLD = 0.6
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm3 = SequenceMatcher()
    sm1.set_seq1(title1.lower())
    sm2.set_seq2(title2.lower())
    #searchingEpisode = 0
    if title3:
        sm3.set_seq1(title3.lower())
        if title3[-1] == '}': searchingEpisode = 1
    hasArt = 0
    if title2 != title1: hasArt = 1
    resd = {}
    for i, t_data in titles_list:
        if searchingEpisode:
            if t_data.get('kind') != 'episode': continue
        elif t_data.get('kind') == 'episode': continue
        til = t_data['title']
        # XXX: on Symbian, here we get a str; not sure this is the
        #      right place to fix it.
        if isinstance(til, str):
            til = unicode(til, 'latin1', 'ignore')
        # Distance with the canonical title (with or without article).
        #   titleS      -> titleR
        #   titleS, the -> titleR, the
        if not searchingEpisode:
            ratios = [ratcliff(title1, til, sm1) + 0.05]
            # til2 is til without the article, if present.
            til2 = til
            tils = til2.split(', ')
            matchHasArt = 0
            if tils[-1].lower() in _articles:
                til2 = ', '.join(tils[:-1])
                matchHasArt = 1
            if hasArt and not matchHasArt:
                #   titleS[, the]  -> titleR
                ratios.append(ratcliff(title2, til, sm2))
            elif matchHasArt and not hasArt:
                #   titleS  -> titleR[, the]
                ratios.append(ratcliff(title1, til2, sm1))
        else:
            ratios = [0.0]
        if title3:
            # Distance with the long imdb canonical title.
            ratios.append(ratcliff(title3,
                        build_title(t_data, canonical=1, ptdf=1), sm3) + 0.1)
        ratio = max(ratios)
        if ratio >= RO_THRESHOLD:
            if resd.has_key(i):
                if ratio > resd[i][0]:
                    resd[i] = (ratio, (i, t_data))
            else: resd[i] = (ratio, (i, t_data))
    res = resd.values()
    res.sort()
    res.reverse()
    if results > 0: res[:] = res[:results]
    return res


def scan_company_names(name_list, name1, results=0, ro_thresold=None):
    """Scan a list of company names, searching for best matches against
    the given name.  Notice that this function takes a list of
    strings, and not a list of dictionaries."""
    if ro_thresold is not None: RO_THRESHOLD = ro_thresold
    else: RO_THRESHOLD = 0.6
    sm1 = SequenceMatcher()
    sm1.set_seq1(name1.lower())
    resd = {}
    withoutCountry = not name1.endswith(']')
    for i, n in name_list:
        # XXX: on Symbian, here we get a str; not sure this is the
        #      right place to fix it.
        if isinstance(n, str):
            n = unicode(n, 'latin1', 'ignore')
        o_name = n
        var = 0.0
        if withoutCountry and n.endswith(']'):
            cidx = n.rfind('[')
            if cidx != -1:
                n = n[:cidx].rstrip()
                var = -0.05
        # Distance with the company name.
        ratio = ratcliff(name1, n, sm1) + var
        if ratio >= RO_THRESHOLD:
            if resd.has_key(i):
                if ratio > resd[i][0]: resd[i] = (ratio,
                                            (i, analyze_company_name(o_name)))
            else:
                resd[i] = (ratio, (i, analyze_company_name(o_name)))
    res = resd.values()
    res.sort()
    res.reverse()
    if results > 0: res[:] = res[:results]
    return res


