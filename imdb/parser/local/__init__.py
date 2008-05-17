"""
parser.local package (imdb package).

This package provides the IMDbLocalAccessSystem class used to access
IMDb's data through a local installation.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "local" or "files".

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

import os
from stat import ST_SIZE

from imdb._exceptions import IMDbDataAccessError, IMDbError
from imdb.utils import analyze_title, analyze_name, re_episodes, \
                        normalizeName, analyze_company_name, \
                        split_company_name_notes

from imdb.Movie import Movie
from imdb.Company import Company
from personParser import getFilmography, getBio, getAkaNames
from movieParser import getLabel, getMovieCast, getAkaTitles, parseMinusList, \
                        getPlot, getRatingData, getMovieMisc, getTaglines, \
                        getQuotes, getMovieLinks, getBusiness, getLiterature, \
                        getLaserdisc, getMPAA
from characterParser import getCharacterName, getCharacterFilmography
from companyParser import getCompanyName, getCompanyFilmography, getCompanyID
from utils import getFullIndex, KeyFScan, latin2utf
from imdb.parser.common.locsql import IMDbLocalAndSqlAccessSystem, \
                                merge_roles, titleVariations, nameVariations

try:
    from imdb.parser.common.cutils import get_episodes
except ImportError:
    import warnings
    warnings.warn('Unable to import the cutils.get_episodes function.'
                    '  Retrieving episodes list of tv series will be'
                    ' a bit slower.')

    def get_episodes(movieID, indexFile, keyFile):
        if movieID < 0:
            raise IMDbDataAccessError, "movieID must be positive."
        try:
            ifile = open(indexFile, 'rb')
        except IOError, e:
            raise IMDbDataAccessError, str(e)
        ifile.seek(4L*movieID, 0)
        indexStr = ifile.read(4)
        ifile.close()
        if len(indexStr) != 4:
            raise IMDbDataAccessError, \
                    "unable to read indexFile; movieID too high?"
        kfIndex = 0L
        for i in (0, 1, 2, 3):
            kfIndex |= ord(indexStr[i]) << i*8L;
        try:
            kfile = open(keyFile, 'rt')
        except IOError, e:
            raise IMDbDataAccessError, str(e)
        kfile.seek(kfIndex, 0)
        seriesTitle = kfile.readline().split('|')[0].strip()
        if seriesTitle[0:1] != '"' or seriesTitle[-1:] != ')':
            return []
        stLen = len(seriesTitle)
        results = []
        for line in kfile:
            if not line.strip(): break
            epsTitle, epsID = line.split('|')
            if epsTitle[:stLen] != seriesTitle: break
            if epsTitle[stLen+1] != '{' or epsTitle[-1] != '}':
                break
            results.append((int(epsID.strip(), 16), epsTitle))
        kfile.close()
        return results

try:
    from imdb.parser.common.cutils import search_name

    def _scan_names(keyFile, name1, name2, name3, results=0, _scan_character=0):
        """Scan the given file, using the cutils.search_name
        C function, for name variations."""
        # the search_name function in the cutils C module manages
        # latin_1 encoded strings.
        name1, name2, name3 = [x.encode('latin_1', 'replace')
                                for x in name1, name2, name3]
        try:
            sn = search_name(keyFile, name1, name2, name3, results,
                    _scan_character)
        except IOError, e:
            if _scan_character:
                import warnings
                warnings.warn('Unable to access characters information: %s' % e)
                return []
            else:
                raise
        res = []
        for x in sn:
            tmpd = analyze_name(latin2utf(x[2]))
            res.append((x[0], (x[1], tmpd)))
        return res
except ImportError:
    import warnings
    warnings.warn('Unable to import the cutils.search_name function.'
                    '  Searching names using the "local" data access system'
                    ' will be REALLY slow.')

    from imdb.parser.common.locsql import scan_names

    def _readNamesKeyFile(keyFile):
        """Iterate over the given file, returning tuples suited for
        the common.locsql.scan_names function."""
        try: kf = open(keyFile, 'r')
        except IOError, e: raise IMDbDataAccessError, str(e)
        for line in kf:
            ls = line.split('|')
            if not ls[0]: continue
            named = analyze_name(latin2utf(ls[0]))
            yield (long(ls[1], 16), named)
        kf.close()

    def _scan_names(keyFile, name1, name2, name3, results=0, _scan_character=0):
        """Scan the given file, using the common.locsql.scan_names
        pure-Python function, for name variations."""
        return scan_names(_readNamesKeyFile(keyFile),
                            name1, name2, name3, results, _scan_character)

try:
    from imdb.parser.common.cutils import search_title

    def _scan_titles(keyFile, title1, title2, title3, results=0):
        """Scan the given file, using the cutils.search_title
        C function, for title variations."""
        title1, title2, title3 = [x.encode('latin_1', 'replace')
                                    for x in title1, title2, title3]
        st = search_title(keyFile, title1, title2, title3, results)
        res = []
        for x in st:
            tmpd = analyze_title(latin2utf(x[2]))
            res.append((x[0], (x[1], tmpd)))
        return res
except ImportError:
    import warnings
    warnings.warn('Unable to import the cutils.search_title function.'
                    '  Searching titles using the "local" data access system'
                    ' will be REALLY slow.')

    from imdb.parser.common.locsql import scan_titles

    def _readTitlesKeyFile(keyFile, searchingEpisode=0):
        """Iterate over the given file, returning tuples suited for
        the common.locsql.scan_titles function."""
        try: kf = open(keyFile, 'r')
        except IOError, e: raise IMDbDataAccessError, str(e)
        for line in kf:
            ls = line.split('|')
            t = ls[0]
            if not t: continue
            if searchingEpisode:
                if t[-1] != '}': continue
            elif t[-1] == '}': continue
            titled = analyze_title(latin2utf(t))
            yield (long(ls[1], 16), titled)
        kf.close()

    def _scan_titles(keyFile, title1, title2, title3, results=0):
        """Scan the given file, using the common.locsql.scan_titles
        pure-Python function, for title variations."""
        se = 0
        if title3 and title3[-1] == '}': se = 1
        return scan_titles(_readTitlesKeyFile(keyFile, searchingEpisode=se),
                            title1, title2, title3, results)

try:
    from imdb.parser.common.cutils import search_company_name

    def _scan_company_names(keyFile, name1, results=0):
        """Scan the given file, using the cutils.search_company_name
        C function, for a given name."""
        name1 = name1.encode('latin_1', 'replace')
        try:
            st = search_company_name(keyFile, name1, results)
        except IOError, e:
            import warnings
            warnings.warn('unable to access companies information; '
                    'please run the companies4local.py script: %s.' % e)
            return []
        res = []
        for x in st:
            tmpd = analyze_company_name(latin2utf(x[2]))
            res.append((x[0], (x[1], tmpd)))
        return res
except ImportError:
    import warnings
    warnings.warn('Unable to import the cutils.search_company_name function.'
                    '  Searching company names using the "local" data access'
                    ' system will be a bit slower.')

    from imdb.parser.common.locsql import scan_company_names

    def _readCompanyNamsKeyFile(keyFile):
        """Iterate over the given file, returning tuples suited for
        the common.locsql.scan_company_names function."""
        try: kf = open(keyFile, 'r')
        except IOError, e: raise IMDbDataAccessError, str(e)
        for line in kf:
            ls = line.split('|')
            n = ls[0]
            if not n: continue
            yield (long(ls[1], 16), latin2utf(n))
        kf.close()

    def _scan_company_names(keyFile, name, results=0):
        """Scan the given file, using the common.locsql.scan_company_names
        pure-Python function, for the given company name."""
        return scan_company_names(_readCompanyNamsKeyFile(keyFile),
                                name, results)


class IMDbLocalAccessSystem(IMDbLocalAndSqlAccessSystem):
    """The class used to access IMDb's data through a local installation."""

    accessSystem = 'local'

    def __init__(self, dbDirectory, adultSearch=1, *arguments, **keywords):
        """Initialize the access system.
        The directory with the files must be supplied.
        """
        IMDbLocalAndSqlAccessSystem.__init__(self, *arguments, **keywords)
        self.__db = os.path.expandvars(dbDirectory)
        self.__db = os.path.expanduser(self.__db)
        if hasattr(os.path, 'realpath'):
            self.__db = os.path.realpath(self.__db)
        self.__db = os.path.normpath(self.__db)
        self.__db = self.__db + getattr(os.path, 'sep', '/')
        self.__db = os.path.normcase(self.__db)
        if not os.path.isdir(self.__db):
            raise IMDbDataAccessError, '"%s" is not a directory' % self.__db
        # These indices are used to quickly get the mopID
        # for a given title/name.
        self.__namesScan = KeyFScan('%snames.key' % self.__db)
        self.__titlesScan = KeyFScan('%stitles.key' % self.__db)
        self.do_adult_search(adultSearch)

    def _getTitleID(self, title):
        return self.__titlesScan.getID(title)

    def _getNameID(self, name):
        return self.__namesScan.getID(name)

    def _get_lastID(self, indexF):
        fsize = os.stat(indexF)[ST_SIZE]
        return (fsize / 4) - 1

    def get_lastMovieID(self):
        """Return the last movieID"""
        return self._get_lastID('%stitles.index' % self.__db)

    def get_lastPersonID(self):
        """Return the last personID"""
        return self._get_lastID('%snames.index' % self.__db)

    def _normalize_movieID(self, movieID):
        """Normalize the given movieID."""
        try:
            return int(movieID)
        except (ValueError, OverflowError):
            raise IMDbError, 'movieID "%s" can\'t be converted to integer' % \
                            movieID

    def _normalize_personID(self, personID):
        """Normalize the given personID."""
        try:
            return int(personID)
        except (ValueError, OverflowError):
            raise IMDbError, 'personID "%s" can\'t be converted to integer' % \
                            personID

    def _normalize_characterID(self, characterID):
        """Normalize the given characterID."""
        try:
            return int(characterID)
        except (ValueError, OverflowError):
            raise IMDbError, 'characterID "%s" can\'t be converted to integer' \
                            % characterID

    def _normalize_companyID(self, companyID):
        """Normalize the given companyID."""
        try:
            return int(companyID)
        except (ValueError, OverflowError):
            raise IMDbError, 'companyID "%s" can\'t be converted to integer' \
                            % companyID

    def _get_real_movieID(self, movieID):
        """Handle title aliases."""
        rid = getFullIndex('%saka-titles.index' % self.__db, movieID,
                            kind='akatidx')
        if rid is not None: return rid
        return movieID

    def _get_real_personID(self, personID):
        """Handle name aliases."""
        rid = getFullIndex('%saka-names.index' % self.__db, personID,
                            kind='akanidx')
        if rid is not None: return rid
        return personID

    def get_imdbMovieID(self, movieID):
        """Translate a movieID in an imdbID.
        Try an Exact Primary Title search on IMDb;
        return None if it's unable to get the imdbID.
        """
        titline = getLabel(movieID, '%stitles.index' % self.__db,
                            '%stitles.key' % self.__db)
        if titline is None: return None
        return self.title2imdbID(titline)

    def get_imdbPersonID(self, personID):
        """Translate a personID in an imdbID.
        Try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        name = getLabel(personID, '%snames.index' % self.__db,
                        '%snames.key' % self.__db)
        if name is None: return None
        return self.name2imdbID(name)

    def get_imdbCharacterID(self, characterID):
        """Translate a characterID in an imdbID.
        Try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        name = getCharacterName(characterID,
                                '%scharacters.index' % self.__db,
                                '%scharacters.data' % self.__db)
        if not name:
            return None
        return self.character2imdbID(name)

    def get_imdbCompanyID(self, companyID):
        """Translate a companyID in an imdbID.
        Try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        name = getCompanyName(companyID,
                                '%scompanies.index' % self.__db,
                                '%scompanies.data' % self.__db)
        if not name:
            return None
        return self.company2imdbID(name)

    def do_adult_search(self, doAdult):
        """If set to 0 or False, movies in the Adult category are not
        shown in the results of a search."""
        self.doAdult = doAdult

    def _search_movie(self, title, results):
        title = title.strip()
        if not title: return []
        # Search for these title variations.
        title1, title2, title3 = titleVariations(title)
        resultsST = results
        if not self.doAdult: resultsST = 0
        res = _scan_titles('%stitles.key' % self.__db,
                            title1, title2, title3, resultsST)
        if self.doAdult and results > 0: res[:] = res[:results]
        res[:] = [x[1] for x in res]
        # Check for adult movies.
        if not self.doAdult:
            newlist = []
            for entry in res:
                genres = getMovieMisc(movieID=entry[0],
                                dataF='%s%s.data' % (self.__db, 'genres'),
                                indexF='%s%s.index' % (self.__db, 'genres'),
                                attrIF='%sattributes.index' % self.__db,
                                attrKF='%sattributes.key' % self.__db)
                if 'Adult' not in genres: newlist.append(entry)
            res[:] = newlist
            if results > 0: res[:] = res[:results]
        return res

    def get_movie_main(self, movieID):
        # Information sets provided by this method.
        infosets = ('main', 'vote details')
        tl = getLabel(movieID, '%stitles.index' % self.__db,
                        '%stitles.key' % self.__db)
        # No title, no party.
        if tl is None:
            raise IMDbDataAccessError, 'unable to get movieID "%s"' % movieID
        res = analyze_title(tl)
        # Build the cast list.
        actl = []
        for castG in ('actors', 'actresses'):
            midx = getFullIndex('%s%s.titles' % (self.__db, castG),
                            movieID, multi=1)
            if midx is not None:
                params = {'movieID': movieID,
                            'dataF': '%s%s.data' % (self.__db, castG),
                            'indexF': '%snames.index' % self.__db,
                            'keyF': '%snames.key' % self.__db,
                            'attrIF': '%sattributes.index' % self.__db,
                            'attrKF': '%sattributes.key' % self.__db,
                            'charNF': '%scharacter2id.index' % self.__db,
                            'offsList': midx, 'doCast': 1}
                actl += getMovieCast(**params)
        if actl:
            actl.sort()
            res['cast'] = actl
        # List of other workers.
        works = ('writer', 'cinematographer', 'composer',
                'costume-designer', 'director', 'editor', 'miscellaneou',
                'producer', 'production-designer', 'cinematographer')
        for i in works:
            index = getFullIndex('%s%ss.titles' % (self.__db, i),
                                    movieID, multi=1)
            if index is not None:
                params = {'movieID': movieID,
                            'dataF': '%s%s.data' % (self.__db, i),
                            'indexF': '%snames.index' % self.__db,
                            'keyF': '%snames.key' % self.__db,
                            'attrIF': '%sattributes.index' % self.__db,
                            'attrKF': '%sattributes.key' % self.__db,
                            'offsList': index}
                name = key = i
                if '-' in name:
                    name = name.replace('-', ' ')
                elif name == 'miscellaneou':
                    name = 'miscellaneous crew'
                    key = 'miscellaneou'
                elif name == 'writer':
                    params['doWriters'] = 1
                params['dataF'] = '%s%ss.data' % (self.__db, key)
                data = getMovieCast(**params)
                if name == 'writer': data.sort()
                res[name] = data
        # Rating.
        rt = self.get_movie_vote_details(movieID)['data']
        if rt: res.update(rt)
        # Various information.
        miscInfo = (('runtimes', 'running-times'), ('color info', 'color-info'),
                    ('genres', 'genres'), ('distributors', 'distributors'),
                    ('languages', 'language'), ('certificates', 'certificates'),
                    ('special effects companies', 'special-effects-companies'),
                    ('sound mix', 'sound-mix'), ('tech info', 'technical'),
                    ('production companies', 'production-companies'),
                    ('countries', 'countries'))
        for name, fname in miscInfo:
            params = {'movieID': movieID,
                'dataF': '%s%s.data' % (self.__db, fname),
                'indexF': '%s%s.index' % (self.__db, fname),
                'attrIF': '%sattributes.index' % self.__db,
                'attrKF': '%sattributes.key' % self.__db}
            data = getMovieMisc(**params)
            if name in ('distributors', 'special effects companies',
                        'production companies'):
                for nitem in xrange(len(data)):
                    n, notes = split_company_name_notes(data[nitem])
                    company = Company(name=n, companyID=getCompanyID(n,
                                        '%scompany2id.index' % self.__db),
                                        notes=notes,
                                        accessSystem=self.accessSystem)
                    data[nitem] = company
            if data: res[name] = data
        if res.has_key('runtimes') and len(res['runtimes']) > 0:
            rt = res['runtimes'][0]
            episodes = re_episodes.findall(rt)
            if episodes:
                res['runtimes'][0] = re_episodes.sub('', rt)
                res['number of episodes'] = episodes[0]
        # AKA titles.
        akas = getAkaTitles(movieID,
                    '%saka-titles.data' % self.__db,
                    '%stitles.index' % self.__db,
                    '%stitles.key' % self.__db,
                    '%sattributes.index' % self.__db,
                    '%sattributes.key' % self.__db)
        if akas:
            # normalize encoding.
            for i in xrange(len(akas)):
                ts = akas[i].split('::')
                if len(ts) != 2: continue
                t = ts[0]
                n = ts[1]
                nt = self._changeAKAencoding(n, t)
                if nt is not None: akas[i] = '%s::%s' % (nt, n)
            res['akas'] = akas
        if res.get('kind') == 'episode':
            # Things to do if this is a tv series episode.
            episodeOf = res.get('episode of')
            if episodeOf is not None:
                parentSeries = Movie(data=res['episode of'],
                                            accessSystem='local')
                seriesID = self._getTitleID(parentSeries.get(
                                            'long imdb canonical title'))
                parentSeries.movieID = seriesID
                res['episode of'] = parentSeries
            if not res.get('year'):
                year = getFullIndex('%smovies.data' % self.__db,
                                    movieID, kind='moviedata', rindex=1)
                if year: res['year'] = year
        # MPAA info.
        mpaa = getMPAA(movieID, '%smpaa-ratings-reasons.index' % self.__db,
                        '%smpaa-ratings-reasons.data' % self.__db)
        if mpaa: res.update(mpaa)
        return {'data': res, 'info sets': infosets}

    def get_movie_plot(self, movieID):
        pl = getPlot(movieID, '%splot.index' % self.__db,
                                '%splot.data' % self.__db)
        trefs, nrefs = self._extractRefs(pl)
        if pl: return {'data': {'plot': pl},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_taglines(self, movieID):
        tg = getTaglines(movieID, '%staglines.index' % self.__db,
                        '%staglines.data' % self.__db)
        if tg: return {'data': {'taglines': tg}}
        return {'data': {}}

    def get_movie_keywords(self, movieID):
        params = {'movieID': movieID,
            'dataF': '%skeywords.data' % self.__db,
            'indexF': '%skeywords.index' % self.__db,
            'attrIF': '%sattributes.index' % self.__db,
            'attrKF': '%sattributes.key' % self.__db}
        kwds = getMovieMisc(**params)
        if kwds: return {'data': {'keywords': kwds}}
        return {'data': {}}

    def get_movie_alternate_versions(self, movieID):
        av = parseMinusList(movieID, '%salternate-versions.data' % self.__db,
                        '%salternate-versions.index' % self.__db)
        trefs, nrefs = self._extractRefs(av)
        if av: return {'data': {'alternate versions': av},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_crazy_credits(self, movieID):
        cc = parseMinusList(movieID, '%scrazy-credits.data' % self.__db,
                            '%scrazy-credits.index' % self.__db)
        trefs, nrefs = self._extractRefs(cc)
        if cc: return {'data': {'crazy credits': cc},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_goofs(self, movieID):
        goo = parseMinusList(movieID, '%sgoofs.data' % self.__db,
                            '%sgoofs.index' % self.__db)
        trefs, nrefs = self._extractRefs(goo)
        if goo: return {'data': {'goofs': goo},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_soundtrack(self, movieID):
        goo = parseMinusList(movieID, '%ssoundtracks.data' % self.__db,
                            '%ssoundtracks.index' % self.__db)
        trefs, nrefs = self._extractRefs(goo)
        if goo: return {'data': {'soundtrack': goo},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_quotes(self, movieID):
        mq = getQuotes(movieID, '%squotes.data' % self.__db,
                            '%squotes.index' % self.__db)
        trefs, nrefs = self._extractRefs(mq)
        if mq: return {'data': {'quotes': mq},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_release_dates(self, movieID):
        params = {'movieID': movieID,
            'dataF': '%srelease-dates.data' % self.__db,
            'indexF': '%srelease-dates.index' % self.__db,
            'attrIF': '%sattributes.index' % self.__db,
            'attrKF': '%sattributes.key' % self.__db}
        data = getMovieMisc(**params)
        if data: return {'data': {'release dates': data}}
        return {'data': {}}

    def get_movie_miscellaneous_companies(self, movieID):
        params = {'movieID': movieID,
            'dataF': '%smiscellaneous-companies.data' % self.__db,
            'indexF': '%smiscellaneous-companies.index' % self.__db,
            'attrIF': '%sattributes.index' % self.__db,
            'attrKF': '%sattributes.key' % self.__db}
        try:
            data = getMovieMisc(**params)
        except IMDbDataAccessError:
            import warnings
            warnings.warn('miscellaneous-companies files not found; '
                            'run the misc-companies4local.py script.')
            return {'data': {}}
        for nitem in xrange(len(data)):
            n, notes = split_company_name_notes(data[nitem])
            company = Company(name=n, companyID=getCompanyID(n,
                                '%scompany2id.index' % self.__db),
                                notes=notes,
                                accessSystem=self.accessSystem)
            data[nitem] = company
        if data: return {'data': {'miscellaneous companies': data}}
        return {'data': {}}

    def get_movie_vote_details(self, movieID):
        data = getRatingData(movieID, '%sratings.data' % self.__db)
        return {'data': data}

    def get_movie_trivia(self, movieID):
        triv = parseMinusList(movieID, '%strivia.data' % self.__db,
                            '%strivia.index' % self.__db)
        trefs, nrefs = self._extractRefs(triv)
        if triv: return {'data': {'trivia': triv},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_locations(self, movieID):
        params = {'movieID': movieID,
            'dataF': '%slocations.data' % self.__db,
            'indexF': '%slocations.index' % self.__db,
            'attrIF': '%sattributes.index' % self.__db,
            'attrKF': '%sattributes.key' % self.__db}
        data = getMovieMisc(**params)
        if data: return {'data': {'locations': data}}
        return {'data': {}}

    def get_movie_connections(self, movieID):
        mc = getMovieLinks(movieID, '%smovie-links.data' % self.__db,
                            '%stitles.index' % self.__db,
                            '%stitles.key' % self.__db)
        if mc: return {'data': {'connections': mc}}
        return {'data': {}}

    def get_movie_business(self, movieID):
        mb = getBusiness(movieID, '%sbusiness.index' % self.__db,
                            '%sbusiness.data' % self.__db)
        trefs, nrefs = self._extractRefs(mb)
        if mb: return {'data': {'business': mb},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def get_movie_literature(self, movieID):
        ml = getLiterature(movieID, '%sliterature.index' % self.__db,
                            '%sliterature.data' % self.__db)
        if ml: return {'data': {'literature': ml}}
        return {'data': {}}

    def get_movie_laserdisc(self, movieID):
        ml = getLaserdisc(movieID, '%slaserdisc.index' % self.__db,
                            '%slaserdisc.data' % self.__db)
        trefs, nrefs = self._extractRefs(ml)
        if ml: return {'data': {'laserdisc': ml},
                        'titlesRefs': trefs, 'namesRefs': nrefs}
        return {'data': {}}

    def _buildEpisodes(self, eps_list, parentID):
        episodes = {}
        parentTitle = getLabel(parentID, '%stitles.index' % self.__db,
                            '%stitles.key' % self.__db)
        parentSeries = Movie(title=parentTitle,
                            movieID=parentID, accessSystem='local')
        for episodeID, episodeTitle in eps_list:
            episodeTitle = unicode(episodeTitle, 'latin_1', 'replace')
            data = analyze_title(episodeTitle, canonical=1)
            m = Movie(data=data, movieID=episodeID, accessSystem='local')
            m['episode of'] = parentSeries
            if data.get('year') is None:
                year = getFullIndex('%smovies.data' % self.__db,
                                    key=episodeID, kind='moviedata', rindex=1)
                if year: m['year'] = year
            season = data.get('season', 'UNKNOWN')
            if not episodes.has_key(season): episodes[season] = {}
            ep_number = data.get('episode')
            if ep_number is None:
                ep_number = max((episodes[season].keys() or [0])) + 1
            episodes[season][ep_number] = m
        return episodes

    def get_movie_episodes(self, movieID):
        try:
            me = get_episodes(movieID, '%stitles.index' % self.__db,
                                        '%stitles.key' % self.__db)
        except IOError, e:
            raise IMDbDataAccessError, str(e)
        if me:
            episodes = self._buildEpisodes(me, movieID)
            data = {'episodes': episodes}
            data['number of episodes'] = sum([len(x) for x
                                                in episodes.values()])
            data['number of seasons'] = len(episodes.keys())
            return {'data': data}
        return {'data': {}}

    def _search_person(self, name, results):
        name = name.strip()
        if not name: return []
        name1, name2, name3 = nameVariations(name)
        res =  _scan_names('%snames.key' % self.__db,
                            name1, name2, name3, results)
        ##if results > 0: res[:] = res[:results]
        res[:] = [x[1] for x in res]
        return res

    def get_person_main(self, personID):
        infosets = ('main', 'biography', 'other works')
        nl = getLabel(personID, '%snames.index' % self.__db,
                        '%snames.key' % self.__db)
        # No name, no party.
        if nl is None:
            raise IMDbDataAccessError, 'unable to get personID "%s"' % personID
        res = analyze_name(nl)
        res.update(getBio(personID, '%sbiographies.index' % self.__db,
                    '%sbiographies.data' % self.__db))
        akas = getAkaNames(personID,
                    '%saka-names.data' % self.__db,
                    '%snames.index' % self.__db,
                    '%snames.key' % self.__db)
        if akas: res['akas'] = akas
        # XXX: horrible hack!  The getBio() function is not able to
        #      retrieve the movieID!
        #      A cleaner solution, would be to NOT return Movies object
        #      at first, from the getBio() function.
        # XXX: anyway, this is no more needed, since "guest appearances"
        #      are gone with the new tv series episodes support.
        if res.has_key('notable tv guest appearances'):
            nl = []
            for m in res['notable tv guest appearances']:
                movieID = self._getTitleID(m.get('long imdb canonical title'))
                if movieID is None: continue
                m.movieID = movieID
                nl.append(m)
            if nl:
                nl.sort()
                res['notable tv guest appearances'][:] = nl
            else: del res['notable tv guest appearances']
        trefs, nrefs = self._extractRefs(res)
        return {'data': res, 'info sets': infosets,
                'titlesRefs': trefs, 'namesRefs': nrefs}

    def get_person_filmography(self, personID):
        infosets = ('filmography', 'episodes')
        res = {}
        episodes = {}
        works = ('actor', 'actresse', 'producer', 'writer',
                'cinematographer', 'composer', 'costume-designer',
                'director', 'editor', 'miscellaneou', 'production-designer')
        for i in works:
            index = getFullIndex('%s%ss.names' % (self.__db, i), personID)
            if index is not None:
                params = {'offset': index,
                            'indexF': '%stitles.index' % self.__db,
                            'keyF': '%stitles.key' % self.__db,
                            'attrIF': '%sattributes.index' % self.__db,
                            'attrKF': '%sattributes.key' % self.__db,
                            'charNF': '%scharacter2id.index' % self.__db}
                name = key = i
                if '-' in name:
                    name = name.replace('-', ' ')
                elif name == 'actresse':
                    name = 'actress'
                    params['doCast'] = 1
                elif name == 'miscellaneou':
                    name = 'miscellaneous crew'
                    key = 'miscellaneou'
                elif name == 'actor':
                    params['doCast'] = 1
                elif name == 'writer':
                    params['doWriters'] = 1
                params['dataF'] = '%s%ss.data' % (self.__db, key)
                data = getFilmography(**params)
                movies = []
                eps = []
                # Split normal titles from episodes.
                for d in data:
                    if d.get('kind') != 'episode':
                        movies.append(d)
                    else:
                        eps.append(d)
                movies.sort()
                if movies:
                    res[name] = movies
                for e in eps:
                    series = Movie(data=e['episode of'], accessSystem='local')
                    seriesID = self._getTitleID(series.get(
                                                'long imdb canonical title'))
                    series.movieID = seriesID
                    if not e.get('year'):
                        year = getFullIndex('%smovies.data' % self.__db,
                                            e.movieID, kind='moviedata',
                                            rindex=1)
                        if year: e['year'] = year
                    if not e.currentRole and name not in ('actor', 'actress'):
                        if e.notes: e.notes = ' %s' % e.notes
                        e.notes = '[%s]%s' % (name, e.notes)
                    episodes.setdefault(series, []).append(e)
        if episodes:
            for k in episodes:
                episodes[k].sort()
                episodes[k].reverse()
            res['episodes'] = episodes
        return {'data': res, 'info sets': tuple(infosets)}

    get_person_biography = get_person_main
    get_person_other_works = get_person_main
    get_person_episodes = get_person_filmography

    def _search_character(self, name, results):
        name = name.strip()
        if not name: return []
        s_name = normalizeName(analyze_name(name)['name'])
        nsplit = s_name.split()
        name2 = u''
        if len(nsplit) > 1:
            name2 = '%s %s' % (nsplit[-1], ' '.join(nsplit[:-1]))
            if s_name == name2:
                name2 = u''
        res =  _scan_names('%scharacters.key' % self.__db,
                            s_name, name2, u'', results, _scan_character=1)
        res[:] = [x[1] for x in res]
        return res

    def get_character_main(self, characterID, results=1000):
        infosets = self.get_character_infoset()
        name = getCharacterName(characterID,
                                '%scharacters.index' % self.__db,
                                '%scharacters.data' % self.__db)
        if not name:
            raise IMDbDataAccessError, \
                            'unable to get characterID "%s"' % characterID
        res = analyze_name(name, canonical=1)
        filmography = getCharacterFilmography(characterID,
                                            '%scharacters.index' % self.__db,
                                            '%scharacters.data' % self.__db,
                                            '%stitles.index' % self.__db,
                                            '%stitles.key' % self.__db,
                                            '%snames.index' % self.__db,
                                            '%snames.key' % self.__db,
                                            limit=results)
        if filmography:
            filmography = merge_roles(filmography)
            filmography.sort()
            res['filmography'] = filmography
        return {'data': res, 'info sets': infosets}

    get_character_filmography = get_character_main
    get_character_biography = get_character_main

    def _search_company(self, name, results):
        name = name.strip()
        if not name: return []
        res =  _scan_company_names('%scompanies.key' % self.__db,
                                    name, results)
        res[:] = [x[1] for x in res]
        return res

    def get_company_main(self, companyID):
        name = getCompanyName(companyID,
                                '%scompanies.index' % self.__db,
                                '%scompanies.data' % self.__db)
        if not name:
            raise IMDbDataAccessError, \
                            'unable to get companyID "%s"' % companyID
        res = analyze_company_name(name)
        filmography = getCompanyFilmography(companyID,
                                            '%scompanies.index' % self.__db,
                                            '%scompanies.data' % self.__db,
                                            '%stitles.index' % self.__db,
                                            '%stitles.key' % self.__db)
        if filmography:
            res.update(filmography)
        return {'data': res}

