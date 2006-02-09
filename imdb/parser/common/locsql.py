"""
locsql module (imdb.parser.common package).

This module provides some functions and classes shared amongst
"local" and "sql" parsers.

Copyright 2005-2006 Davide Alberani <da@erlug.linux.it> 

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
import re, urllib
from difflib import SequenceMatcher
from codecs import lookup

from imdb import IMDbBase
from imdb.Person import Person
from imdb.Movie import Movie
from imdb._exceptions import IMDbDataAccessError
from imdb.utils import analyze_title, build_title, analyze_name, \
                        build_name, canonicalTitle, canonicalName, \
                        normalizeName, re_titleRef, re_nameRef, \
                        re_year_index, _articles

_ltype = type([])
_dtype = type({})
_stypes = (type(u''), type(''))

re_nameIndex = re.compile(r'\(([IVXLCDM]+)\)')


class IMDbLocalAndSqlAccessSystem(IMDbBase):
    """Base class for methods shared by the 'local' and the 'sql'
    data access systems."""

    def _searchIMDbMoP(self, params):
        """Fetch the given web page from the IMDb akas server."""
        from imdb.parser.http import IMDbURLopener
        ##params = urllib.urlencode(params)
        url = 'http://akas.imdb.com/find?%s' % params
        content = ''
        try:
            urlOpener = IMDbURLopener()
            uopener = urlOpener.open(url)
            content = uopener.read()
            uopener.close()
            urlOpener.close()
        except (IOError, IMDbDataAccessError):
            pass
        # XXX: convert to unicode? I don't think it's needed.
        return content

    def _getTitleID(self, title):
        raise NotImplementedError, 'override this method'

    def _getNameID(self, name):
        raise NotImplementedError, 'override this method'

    def _httpMovieID(self, titline):
        """Translate a movieID in an imdbID.
        Try an Exact Primary Title search on IMDb;
        return None if it's unable to get the imdbID.
        """
        if not titline: return None
        ##params = {'q': titline, 's': 'pt'}
        params = 'q=%s&s=pt' % str(urllib.quote_plus(titline))
        content = self._searchIMDbMoP(params)
        if not content: return None
        from imdb.parser.http.searchMovieParser import BasicMovieParser
        mparser = BasicMovieParser()
        result = mparser.parse(content)
        if not (result and result.get('data')): return None
        return result['data'][0][0]

    def _httpPersonID(self, name):
        """Translate a personID in an imdbID.
        Try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        if not name: return None
        ##params = {'q': name, 's': 'pn'}
        params = 'q=%s&s=pn' % str(urllib.quote_plus(name))
        content = self._searchIMDbMoP(params)
        if not content: return None
        from imdb.parser.http.searchPersonParser import BasicPersonParser
        pparser = BasicPersonParser()
        result = pparser.parse(content)
        if not (result and result.get('data')): return None
        return result['data'][0][0]

    def _findRefs(self, o, trefs, nrefs):
        """Find titles or names references in strings."""
        to = type(o)
        if to in _stypes:
            for title in re_titleRef.findall(o):
                a_title = analyze_title(title, canonical=1)
                rtitle = build_title(a_title, canonical=1)
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
        elif to is _ltype:
            for item in o:
                self._findRefs(item, trefs, nrefs)
        elif to is _dtype:
            for value in o.values():
                self._findRefs(value, trefs, nrefs)
        return (trefs, nrefs)

    def _extractRefs(self, o):
        """Scan for titles or names references in strings."""
        trefs = {}
        nrefs = {}
        return self._findRefs(o, trefs, nrefs)

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
                    codec = lookup(e)
                    lat1 = akatitle.encode('latin_1', 'replace')
                    return unicode(lat1, e, 'replace')
                except (LookupError, ValueError, TypeError):
                    continue
        return None


def titleVariations(title):
    """Build title variations useful for searches."""
    title1 = title
    title2 = title3 = u''
    if re_year_index.search(title):
        # If it appears to have a (year[/imdbIndex]) indication,
        # assume that a long imdb canonical name was provided.
        titldict = analyze_title(title, canonical=1)
        # title1: the canonical name.
        title1 = titldict['title']
        # title3: the long imdb canonical name.
        title3 = build_title(titldict, canonical=1)
    else:
        # Just a title.
        # title1: the canonical title.
        title1 = canonicalTitle(title)
        title3 = u''
    # title2 is title1 without the article, or title1 unchanged.
    title2 = title1
    t2s = title2.split(u', ')
    if t2s[-1] in _articles:
        title2 = u', '.join(t2s[:-1])
    return title1, title2, title3


def nameVariations(name):
    """Build name variations useful for searches."""
    name1 = name
    name2 = name3 = u''
    if re_nameIndex.search(name):
        # We've a name with an (imdbIndex)
        namedict = analyze_name(name, canonical=1)
        # name1 is the name in the canonical format.
        name1 = namedict['name']
        # name3 is the canonical name with the imdbIndex.
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
    from ratober import ratcliff as _ratcliff
    def ratcliff(s1, s2, sm):
        return _ratcliff(s1.encode('latin_1', 'replace'),
                        s2.encode('latin_1', 'replace'))
except ImportError:
    import warnings
    warnings.warn('Unable to import the ratober.ratcliff function.'
                    '  Searching names and titles using the "sql" and "local"'
                    ' data access systems will be slower.')

    def ratcliff(s1, s2, sm):
        """Ratcliff-Obershelp similarity."""
        sm.set_seq2(s2.lower())
        return sm.ratio()


def scan_names(name_list, name1, name2, name3, results=0):
    """Scan a list of names, searching for best matches against
    the given variations."""
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm3 = SequenceMatcher()
    sm1.set_seq1(name1.lower())
    if name2: sm2.set_seq1(name2.lower())
    if name3: sm3.set_seq1(name3.lower())
    resd = {}
    for i in name_list:
        nil = i[1]
        # Distance with the canonical name.
        ratios = [ratcliff(name1, nil, sm1) + 0.05]
        nils = nil.split(', ', 1)
        surname = nils[0]
        namesurname = ''
        if len(nils) == 2: namesurname = '%s %s' % (nils[1], surname)
        if surname != nil:
            # Distance with the "Surname" in the database.
            ratios.append(ratcliff(name1, surname, sm1))
            ratios.append(ratcliff(name1, namesurname, sm1))
            if name2:
                ratios.append(ratcliff(name2, surname, sm2))
                # Distance with the "Name Surname" in the database.
                ratios.append(ratcliff(name2, namesurname, sm2))
        if name3:
            # Distance with the long imdb canonical name.
            tmpp = {'name': i[1], 'imdbIndex': i[2]}
            ratios.append(ratcliff(name3,
                        build_name(tmpp, canonical=1), sm3) + 0.1)
        ratio = max(ratios)
        if resd.has_key(i):
            if ratio > resd[i]: resd[i] = ratio
        else: resd[i] = ratio
    
    res = [(x[1], x[0]) for x in resd.items()]
    res.sort()
    res.reverse()
    if results > 0: res[:] = res[:results]
    return res

def scan_titles(titles_list, title1, title2, title3, results=0):
    """Scan a list of titles, searching for best matches against
    the given variations."""
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm3 = SequenceMatcher()
    sm1.set_seq1(title1.lower())
    sm2.set_seq2(title2.lower())
    if title3: sm3.set_seq1(title3.lower())
    hasArt = 0
    if title2 != title1: hasArt = 1
    resd = {}
    for i in titles_list:
        til = i[1]
        # Distance with the canonical title (with or without article).
        #   titleS      -> titleR
        #   titleS, the -> titleR, the
        ratios = [ratcliff(title1, til, sm1) + 0.05]
        # til2 is til without the article, if present.
        til2 = til
        tils = til2.split(', ')
        matchHasArt = 0
        if tils[-1] in _articles:
            til2 = ', '.join(tils[:-1])
            matchHasArt = 1
        if hasArt and not matchHasArt:
            #   titleS[, the]  -> titleR
            ratios.append(ratcliff(title2, til, sm2))
        elif matchHasArt and not hasArt:
            #   titleS  -> titleR[, the]
            ratios.append(ratcliff(title1, til2, sm1))
        if title3:
            # Distance with the long imdb canonical title.
            tmpm = {'title': i[1], 'imdbIndex': i[2],
                    'kind': i[3], 'year': i[4]}
            ratios.append(ratcliff(title3,
                        build_title(tmpm, canonical=1), sm3) + 0.1)
        ratio = max(ratios)
        if resd.has_key(i):
            if ratio > resd[i]: resd[i] = ratio
        else: resd[i] = ratio
    res = [(x[1], x[0]) for x in resd.items()]
    res.sort()
    res.reverse()
    if results > 0: res[:] = res[:results]
    return res


