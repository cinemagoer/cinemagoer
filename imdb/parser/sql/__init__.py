"""
parser.sql package (imdb package).

This package provides the IMDbSqlAccessSystem class used to access
IMDb's data through a SQL database.  Every database supported by
the SQLObject Object Relational Manager is available.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "sql", "database" or "db".

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

# FIXME: this whole module was written in a veeery short amount of time.
#        The code should be commented, rewritten and cleaned. :-)

from types import UnicodeType

from sqlobject.sqlbuilder import *

from dbschema import *

from imdb.parser.common.locsql import IMDbLocalAndSqlAccessSystem, \
                    scan_names, scan_titles, titleVariations, \
                    nameVariations, merge_roles, scan_company_names
from imdb.utils import normalizeTitle, normalizeName, build_title, \
                        build_name, analyze_name, analyze_title, \
                        build_company_name, re_episodes, _articles
from imdb.Person import Person
from imdb.Movie import Movie
from imdb.Company import Company
from imdb._exceptions import IMDbDataAccessError, IMDbError

try:
    from imdb.parser.common.cutils import soundex
except ImportError:
    import warnings
    warnings.warn('Unable to import the cutils.soundex function.'
                    '  Searches of movie titles and person names will be'
                    ' a bit slower.')
    import string

    _all_chars = string.maketrans('', '')
    _keep_chars = 'bcdfgjklmnpqrstvxzBCDFGJKLMNPQRSTVXZ'
    _del_nonascii = _all_chars.translate(_all_chars, _keep_chars)
    _soundTable = string.maketrans(_keep_chars, 2*'123122245512623122')

    def soundex(s):
        """Return the soundex code for the given string."""
        # Maximum length of the soundex code.
        SOUNDEX_LEN = 5
        # Remove everything but the meaningful ascii chars.
        s = s.translate(_all_chars, _del_nonascii)
        if not s: return None
        s = s.upper()
        first_char = s[0]
        # Use the _soundTable to translate the string in the soundexCode.
        s = s.translate(_soundTable)
        # Remove duplicated consecutive digits.
        sl = [s[0]]
        sl_append = sl.append
        for i in xrange(1, len(s)):
            if s[i] != s[i-1]:
                sl_append(s[i])
        s = ''.join(sl)
        return first_char + s[1:SOUNDEX_LEN]


_litlist = ['screenplay/teleplay', 'novel', 'adaption', 'book',
            'production process protocol', 'interviews',
            'printed media reviews', 'essays', 'other literature']
_litd = dict([(x, ('literature', x)) for x in _litlist])

_buslist = ['budget', 'weekend gross', 'gross', 'opening weekend', 'rentals',
            'admissions', 'filming dates', 'production dates', 'studios',
            'copyright holder']
_busd = dict([(x, ('business', x)) for x in _buslist])


def _reGroupDict(d, newgr):
    """Regroup keys in the d dictionary in subdictionaries, based on
    the scheme in the newgr dictionary.
    E.g.: in the newgr, an entry 'LD label': ('laserdisc', 'label')
    tells the _reGroupDict() function to take the entry with
    label 'LD label' (as received from the sql database)
    and put it in the subsection (another dictionary) named
    'laserdisc', using the key 'label'."""
    r = {}
    newgrks = newgr.keys()
    for k, v in d.items():
        if k in newgrks:
            r.setdefault(newgr[k][0], {})[newgr[k][1]] = v
            # A not-so-clearer version:
            ##r.setdefault(newgr[k][0], {})
            ##r[newgr[k][0]][newgr[k][1]] = v
        else: r[k] = v
    return r


def _groupListBy(l, index):
    """Regroup items in a list in a list of lists, grouped by
    the value at the given index."""
    tmpd = {}
    for item in l:
        tmpd.setdefault(item[index], []).append(item)
    res = tmpd.values()
    return res


def sub_dict(d, keys):
    """Return the subdictionary of 'd', with just the keys listed in 'keys'."""
    return dict([(k, d[k]) for k in keys if k in d])


def get_movie_data(movieID, kindDict, fromAka=0):
    """Return a dictionary containing data about the given movieID;
    if fromAka is true, the AkaTitle table is searched."""
    if not fromAka: Table = Title
    else: Table = AkaTitle
    m = Table.get(movieID)
    mdict = {'title': m.title, 'kind': kindDict[m.kindID],
            'year': m.productionYear, 'imdbIndex': m.imdbIndex,
            'season': m.seasonNr, 'episode': m.episodeNr}
    if not fromAka:
        if m.seriesYears is not None:
            mdict['series years'] = unicode(m.seriesYears)
    if mdict['imdbIndex'] is None: del mdict['imdbIndex']
    if mdict['year'] is None: del mdict['year']
    if mdict['season'] is None: del mdict['season']
    else:
        try: mdict['season'] = int(mdict['season'])
        except: pass
    if mdict['episode'] is None: del mdict['episode']
    else:
        try: mdict['episode'] = int(mdict['episode'])
        except: pass
    episodeOfID = m.episodeOfID
    if episodeOfID is not None:
        ser_dict = get_movie_data(episodeOfID, kindDict, fromAka)
        mdict['episode of'] = Movie(data=ser_dict, movieID=episodeOfID,
                                    accessSystem='sql')
        if fromAka:
            ser_note = AkaTitle.get(episodeOfID).note
            if ser_note:
                mdict['episode of'].notes = ser_note
    return mdict


class IMDbSqlAccessSystem(IMDbLocalAndSqlAccessSystem):
    """The class used to access IMDb's data through a SQL database."""

    accessSystem = 'sql'

    def __init__(self, uri, adultSearch=1, *arguments, **keywords):
        """Initialize the access system."""
        IMDbLocalAndSqlAccessSystem.__init__(self, *arguments, **keywords)
        # Set the connection to the database.
        try:
            self._connection = setConnection(uri)
        except AssertionError, e:
            raise IMDbDataAccessError, \
                    'unable to connect to the database server; ' + \
                    'complete message: "%s"' % str(e)
        self.Error = self._connection.module.Error
        # Maps some IDs to the corresponding strings.
        self._kind = {}
        self._kindRev = {}
        try:
            for kt in KindType.select():
                self._kind[kt.id] = kt.kind
                self._kindRev[str(kt.kind)] = kt.id
        except self.Error:
            # NOTE: you can also get the error, but - at least with
            #       MySQL - it also contains the password, and I don't
            #       like the idea to print it out.
            raise IMDbDataAccessError, \
                    'unable to connect to the database server'
        self._role = {}
        for rl in RoleType.select():
            self._role[rl.id] = str(rl.role)
        self._info = {}
        self._infoRev = {}
        for inf in InfoType.select():
            self._info[inf.id] = str(inf.info)
            self._infoRev[str(inf.info)] = inf.id
        self._compType = {}
        for cType in CompanyType.select():
            self._compType[cType.id] = cType.kind
        info = [(it.id, it.info) for it in InfoType.select()]
        self._compcast = {}
        for cc in CompCastType.select():
            self._compcast[cc.id] = str(cc.kind)
        self._link = {}
        for lt in LinkType.select():
            self._link[lt.id] = str(lt.link)
        self._moviesubs = {}
        # Build self._moviesubs, a dictionary used to rearrange
        # the data structure for a movie object.
        for vid, vinfo in info:
            if not vinfo.startswith('LD '): continue
            self._moviesubs[vinfo] = ('laserdisc', vinfo[3:])
        self._moviesubs.update(_litd)
        self._moviesubs.update(_busd)
        self.do_adult_search(adultSearch)

    def _buildNULLCondition(self, col, val):
        """Build a comparison for columns where values can be NULL."""
        if val is None:
            return ISNULL(col)
        else:
            return col == val.encode('utf_8')

    def _getTitleID(self, title):
        """Given a long imdb canonical title, returns a movieID or
        None if not found."""
        td = analyze_title(title)
        condition = None
        if td['kind'] == 'episode':
            epof = td['episode of']
            seriesID = [s.id for s in Title.select(
                        AND(Title.q.title == epof['title'].encode('utf_8'),
                            self._buildNULLCondition(Title.q.imdbIndex,
                                                    epof.get('imdbIndex')),
                           Title.q.kindID == self._kindRev[epof['kind']],
                           self._buildNULLCondition(Title.q.productionYear,
                                                    epof.get('year'))))]
            if seriesID:
                condition = AND(IN(Title.q.episodeOfID, seriesID),
                                Title.q.title == td['title'].encode('utf_8'),
                                self._buildNULLCondition(Title.q.imdbIndex,
                                                        td.get('imdbIndex')),
                                Title.q.kindID == self._kindRev[td['kind']],
                                self._buildNULLCondition(Title.q.productionYear,
                                                        td.get('year')))
        if condition is None:
            condition = AND(Title.q.title == td['title'].encode('utf_8'),
                            self._buildNULLCondition(Title.q.imdbIndex,
                                                    td.get('imdbIndex')),
                            Title.q.kindID == self._kindRev[td['kind']],
                            self._buildNULLCondition(Title.q.productionYear,
                                                    td.get('year')))
        res = Title.select(condition)
        try:
            if res.count() != 1:
                return None
        except (UnicodeDecodeError, TypeError):
            return None
        return res[0].id

    def _getNameID(self, name):
        """Given a long imdb canonical name, returns a personID or
        None if not found."""
        nd = analyze_name(name)
        res = Name.select(AND(Name.q.name == nd['name'].encode('utf_8'),
                                self._buildNULLCondition(Name.q.imdbIndex,
                                                        nd.get('imdbIndex'))))
        try:
            c = res.count()
            if res.count() != 1:
                return None
        except (UnicodeDecodeError, TypeError):
            return None
        return res[0].id

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

    def get_imdbMovieID(self, movieID):
        """Translate a movieID in an imdbID.
        If not in the database, try an Exact Primary Title search on IMDb;
        return None if it's unable to get the imdbID.
        """
        try: movie = Title.get(movieID)
        except SQLObjectNotFound: return None
        imdbID = movie.imdbID
        if imdbID is not None: return '%07d' % imdbID
        m_dict = get_movie_data(movie.id, self._kind)
        titline = build_title(m_dict, canonical=1, ptdf=1)
        imdbID = self.title2imdbID(titline)
        # If the imdbID was retrieved from the web and was not in the
        # database, update the database (ignoring errors, because it's
        # possibile that the current user has not update privileges).
        # There're times when I think I'm a genius; this one of
        # those times... <g>
        if imdbID is not None:
            try: movie.imdbID = int(imdbID)
            except: pass
        return imdbID

    def get_imdbPersonID(self, personID):
        """Translate a personID in an imdbID.
        If not in the database, try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        try: person = Name.get(personID)
        except SQLObjectNotFound: return None
        imdbID = person.imdbID
        if imdbID is not None: return '%07d' % imdbID
        n_dict = {'name': person.name, 'imdbIndex': person.imdbIndex}
        namline = build_name(n_dict, canonical=1)
        imdbID = self.name2imdbID(namline)
        if imdbID is not None:
            try: person.imdbID = int(imdbID)
            except: pass
        return imdbID

    def get_imdbCharacterID(self, characterID):
        """Translate a characterID in an imdbID.
        If not in the database, try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        try: character = CharName.get(characterID)
        except SQLObjectNotFound: return None
        imdbID = character.imdbID
        if imdbID is not None: return '%07d' % imdbID
        n_dict = {'name': character.name, 'imdbIndex': character.imdbIndex}
        namline = build_name(n_dict, canonical=1)
        imdbID = self.character2imdbID(namline)
        if imdbID is not None:
            try: character.imdbID = int(imdbID)
            except: pass
        return imdbID

    def get_imdbCompanyID(self, companyID):
        """Translate a companyID in an imdbID.
        If not in the database, try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        try: company = CompanyName.get(companyID)
        except SQLObjectNotFound: return None
        imdbID = company.imdbID
        if imdbID is not None: return '%07d' % imdbID
        n_dict = {'name': company.name, 'country': company.countryCode}
        namline = build_company_name(n_dict)
        imdbID = self.company2imdbID(namline)
        if imdbID is not None:
            try: company.imdbID = int(imdbID)
            except: pass
        return imdbID

    def do_adult_search(self, doAdult):
        """If set to 0 or False, movies in the Adult category are not
        episodeOf = title_dict.get('episode of')
        shown in the results of a search."""
        self.doAdult = doAdult

    def _search_movie(self, title, results):
        title = title.strip()
        if not title: return []
        title_dict = analyze_title(title, canonical=1)
        s_title = title_dict['title']
        if not s_title: return []
        episodeOf = title_dict.get('episode of')

        if not episodeOf:
            s_title_split = s_title.split(', ')
            if len(s_title_split) >1 and s_title_split[-1].lower() in _articles:
                s_title_rebuilt = ', '.join(s_title_split[:-1])
                if s_title_rebuilt: s_title = s_title_rebuilt
        else:
            s_title = normalizeTitle(s_title)
        if isinstance(s_title, UnicodeType):
            s_title = s_title.encode('ascii', 'ignore')

        soundexCode = soundex(s_title)

        # XXX: improve the search restricting the kindID if the
        #      "kind" of the input differs from "movie"?
        condition = conditionAka = None
        if title_dict['kind'] == 'episode' and episodeOf is not None:
            series_title = build_title(episodeOf, canonical=1)
            # XXX: is it safe to get "results" results?
            #      Too many?  Too few?
            serRes = results
            if serRes < 3 or serRes > 10:
                serRes = 10
            searchSeries = self._search_movie(series_title, serRes)
            seriesIDs = [result[0] for result in searchSeries]
            if seriesIDs:
                condition = AND(Title.q.phoneticCode == soundexCode,
                                IN(Title.q.episodeOfID, seriesIDs),
                                Title.q.kindID == self._kindRev['episode'])
                conditionAka = AND(AkaTitle.q.phoneticCode == soundexCode,
                                IN(AkaTitle.q.episodeOfID, seriesIDs),
                                AkaTitle.q.kindID == self._kindRev['episode'])
            else:
                # XXX: bad situation: we have found no matching series;
                #      try searching everything (both episodes and
                #      non-episodes) for the title.
                condition = AND(Title.q.phoneticCode == soundexCode,
                                IN(Title.q.episodeOfID, seriesIDs))
                conditionAka = AND(AkaTitle.q.phoneticCode == soundexCode,
                                IN(AkaTitle.q.episodeOfID, seriesIDs))
        if condition is None:
            # XXX: excludes episodes?
            condition = AND(Title.q.kindID != self._kindRev['episode'],
                            Title.q.phoneticCode == soundexCode)
            conditionAka = AND(AkaTitle.q.kindID != self._kindRev['episode'],
                            AkaTitle.q.phoneticCode == soundexCode)

        # Up to 3 variations of the title are searched, plus the
        # long imdb canonical title, if provided.
        title1, title2, title3 = titleVariations(title)

        try:
            qr = [(q.id, get_movie_data(q.id, self._kind))
                    for q in Title.select(condition)]
            q2 = [(q.movieID, get_movie_data(q.id, self._kind, fromAka=1))
                    for q in AkaTitle.select(conditionAka)]
            qr += q2
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to search the database: "%s"' % str(e)

        resultsST = results
        if not self.doAdult: resultsST = 0
        res = scan_titles(qr, title1, title2, title3, resultsST,
                            searchingEpisode=episodeOf is not None,
                            ro_thresold=0.0)
        if self.doAdult and results > 0: res[:] = res[:results]
        res[:] = [x[1] for x in res]

        if res and not self.doAdult:
            mids = [x[0] for x in res]
            genreID = self._infoRev['genres']
            adultlist = [al.movieID for al
                        in MovieInfo.select(
                            AND(MovieInfo.q.infoTypeID == genreID,
                                MovieInfo.q.info == 'Adult',
                                IN(MovieInfo.q.movieID, mids)))]
            res[:] = [x for x in res if x[0] not in adultlist]
            if results > 0: res[:] = res[:results]
        return res

    def get_movie_main(self, movieID):
        # Every movie information is retrieved from here.
        infosets = self.get_movie_infoset()
        try:
            res = get_movie_data(movieID, self._kind)
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to get movieID "%s": "%s"' % (movieID, str(e))
        if not res:
            raise IMDbDataAccessError, 'unable to get movieID "%s"' % movieID
        # Collect cast information.
        castdata = [[cd.personID, cd.personRoleID, cd.note, cd.nrOrder,
                    self._role[cd.roleID]]
                    for cd in CastInfo.select(CastInfo.q.movieID == movieID)]
        for p in castdata:
            person = Name.get(p[0])
            p += [person.name, person.imdbIndex]
            if p[4] in ('actor', 'actress'):
                p[4] = 'cast'
        # Regroup by role/duty (cast, writer, director, ...)
        castdata[:] =  _groupListBy(castdata, 4)
        for group in castdata:
            duty = group[0][4]
            for pdata in group:
                curRole = pdata[1]
                curRoleID = None
                if curRole is not None:
                    robj = CharName.get(curRole)
                    curRole = robj.name
                    curRoleID = robj.id
                p = Person(personID=pdata[0], name=pdata[5],
                            currentRole=curRole or u'',
                            roleID=curRoleID,
                            notes=pdata[2] or u'',
                            accessSystem='sql')
                if pdata[6]: p['imdbIndex'] = pdata[6]
                p.billingPos = pdata[3]
                res.setdefault(duty, []).append(p)
            if duty == 'cast':
                res[duty] = merge_roles(res[duty])
            res[duty].sort()
        # Info about the movie.
        minfo = [(self._info[m.infoTypeID], m.info, m.note)
                for m in MovieInfo.select(MovieInfo.q.movieID == movieID)]
        minfo = _groupListBy(minfo, 0)
        for group in minfo:
            sect = group[0][0]
            for mdata in group:
                data = mdata[1]
                if mdata[2]: data += '::%s' % mdata[2]
                res.setdefault(sect, []).append(data)
        # Companies info about a movie.
        cinfo = [(self._compType[m.companyTypeID], m.companyID, m.note) for m
                in MovieCompanies.select(MovieCompanies.q.movieID == movieID)]
        cinfo = _groupListBy(cinfo, 0)
        for group in cinfo:
            sect = group[0][0]
            for mdata in group:
                cDb = CompanyName.get(mdata[1])
                cDbTxt = cDb.name
                if cDb.countryCode:
                    cDbTxt += ' %s' % cDb.countryCode
                company = Company(name=cDbTxt,
                                companyID=mdata[1],
                                notes=mdata[2] or u'',
                                accessSystem=self.accessSystem)
                res.setdefault(sect, []).append(company)
        # AKA titles.
        akat = [(get_movie_data(at.id, self._kind, fromAka=1), at.note)
                for at in AkaTitle.select(AkaTitle.q.movieID == movieID)]
        if akat:
            res['akas'] = []
            for td, note in akat:
                nt = build_title(td, canonical=1, ptdf=1)
                if note:
                    net = self._changeAKAencoding(note, nt)
                    if net is not None: nt = net
                    nt += '::%s' % note
                if nt not in res['akas']: res['akas'].append(nt)
        # Complete cast/crew.
        compcast = [(self._compcast[cc.subjectID], self._compcast[cc.statusID])
            for cc in CompleteCast.select(CompleteCast.q.movieID == movieID)]
        if compcast:
            for entry in compcast:
                val = unicode(entry[1])
                res[u'complete %s' % entry[0]] = val
        # Movie connections.
        mlinks = [[ml.linkedMovieID, self._link[ml.linkTypeID]]
                    for ml in MovieLink.select(MovieLink.q.movieID == movieID)]
        if mlinks:
            for ml in mlinks:
                lmovieData = get_movie_data(ml[0], self._kind)
                m = Movie(movieID=ml[0], data=lmovieData, accessSystem='sql')
                ml[0] = m
            res['connections'] = {}
            mlinks[:] = _groupListBy(mlinks, 1)
            for group in mlinks:
                lt = group[0][1]
                res['connections'][lt] = [i[0] for i in group]
        # Episodes.
        episodes = {}
        eps_list = list(Title.select(Title.q.episodeOfID == movieID))
        eps_list.sort()
        if eps_list:
            ps_data = {'title': res['title'], 'kind': res['kind'],
                        'year': res.get('year'),
                        'imdbIndex': res.get('imdbIndex')}
            parentSeries = Movie(movieID=movieID, data=ps_data,
                                accessSystem='sql')
            for episode in eps_list:
                episodeID = episode.id
                episode_data = get_movie_data(episodeID, self._kind)
                m = Movie(movieID=episodeID, data=episode_data,
                            accessSystem='sql')
                m['episode of'] = parentSeries
                season = episode_data.get('season', 'UNKNOWN')
                if not episodes.has_key(season): episodes[season] = {}
                ep_number = episode_data.get('episode')
                if ep_number is None:
                    ep_number = max((episodes[season].keys() or [0])) + 1
                episodes[season][ep_number] = m
            res['episodes'] = episodes
            res['number of episodes'] = sum([len(x) for x in episodes.values()])
            res['number of seasons'] = len(episodes.keys())
        # Regroup laserdisc information.
        res = _reGroupDict(res, self._moviesubs)
        # Do some transformation to preserve consistency with other
        # data access systems.
        if res.has_key('plot'):
            nl = []
            for i in res['plot']:
                if i[-1] == ')':
                    sauth = i.rfind('::(author: ')
                    if sauth != -1:
                        nl.append(i[sauth+11:-1] + '::' + i[:sauth])
                    else: nl.append(i)
                else: nl.append(i)
            res['plot'][:] = nl
        # Other transformations.
        if res.has_key('runtimes') and len(res['runtimes']) > 0:
            rt = res['runtimes'][0]
            episodes = re_episodes.findall(rt)
            if episodes:
                res['runtimes'][0] = re_episodes.sub('', rt)
                if res['runtimes'][0][-2:] == '::':
                    res['runtimes'][0] = res['runtimes'][0][:-2]
        if res.has_key('year'):
            res['year'] = res['year']
        if res.has_key('votes'):
            res['votes'] = int(res['votes'][0])
        if res.has_key('rating'):
            res['rating'] = float(res['rating'][0])
        if res.has_key('votes distribution'):
            res['votes distribution'] = res['votes distribution'][0]
        if res.has_key('mpaa'):
            res['mpaa'] = res['mpaa'][0]
        if res.has_key('guest'):
            res['guests'] = res['guest']
            del res['guest']
        trefs,nrefs = {}, {}
        trefs,nrefs = self._extractRefs(sub_dict(res,Movie.keys_tomodify_list))
        return {'data': res, 'titlesRefs': trefs, 'namesRefs': nrefs,
                'info sets': infosets}

    # Just to know what kind of information are available.
    get_movie_alternate_versions = get_movie_main
    get_movie_business = get_movie_main
    get_movie_connections = get_movie_main
    get_movie_crazy_credits = get_movie_main
    get_movie_goofs = get_movie_main
    get_movie_keywords = get_movie_main
    get_movie_literature = get_movie_main
    get_movie_locations = get_movie_main
    get_movie_plot = get_movie_main
    get_movie_quotes = get_movie_main
    get_movie_release_dates = get_movie_main
    get_movie_soundtrack = get_movie_main
    get_movie_taglines = get_movie_main
    get_movie_technical = get_movie_main
    get_movie_trivia = get_movie_main
    get_movie_vote_details = get_movie_main
    # XXX: is 'guest' still needed?  I think every GA reference in
    #      the biographies.list file was removed.
    #get_movie_guests = get_movie_main
    get_movie_episodes = get_movie_main

    def _search_person(self, name, results):
        name = name.strip()
        if not name: return []
        s_name = analyze_name(name)['name']
        if not s_name: return []
        if isinstance(s_name, UnicodeType):
            s_name = s_name.encode('ascii', 'ignore')
        soundexCode = soundex(s_name)
        name1, name2, name3 = nameVariations(name)

        # If the soundex is None, compare only with the first
        # phoneticCode column.
        if soundexCode is not None:
            condition = IN(soundexCode, [Name.q.namePcodeCf,
                                        Name.q.namePcodeNf,
                                        Name.q.surnamePcode])
            conditionAka = IN(soundexCode, [AkaName.q.namePcodeCf,
                                            AkaName.q.namePcodeNf,
                                            AkaName.q.surnamePcode])
        else:
            condition = ISNULL(Name.q.namePcodeCf)
            conditionAka = ISNULL(AkaName.q.namePcodeCf)

        try:
            qr = [(q.id, {'name': q.name, 'imdbIndex': q.imdbIndex})
                    for q in Name.select(condition)]
            qr += [(q.personID, {'name': q.name, 'imdbIndex': q.imdbIndex})
                    for q in AkaName.select(conditionAka)]
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to search the database: "%s"' % str(e)

        res = scan_names(qr, name1, name2, name3, results)
        res[:] = [x[1] for x in res]
        # Purge empty imdbIndex.
        returnl = []
        for x in res:
            tmpd = x[1]
            if tmpd['imdbIndex'] is None:
                del tmpd['imdbIndex']
            returnl.append((x[0], tmpd))
        return returnl

    def get_person_main(self, personID):
        # Every person information is retrieved from here.
        infosets = self.get_person_infoset()
        try:
            p = Name.get(personID)
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to get personID "%s": "%s"' % (personID, str(e))
        res = {'name': p.name, 'imdbIndex': p.imdbIndex}
        if res['imdbIndex'] is None: del res['imdbIndex']
        if not res:
            raise IMDbDataAccessError, 'unable to get personID "%s"' % personID
        # Collect cast information.
        castdata = [(cd.movieID, cd.personRoleID, cd.note,
                    self._role[cd.roleID],
                    get_movie_data(cd.movieID, self._kind))
                for cd in CastInfo.select(CastInfo.q.personID == personID)]
        # Regroup by role/duty (cast, writer, director, ...)
        castdata[:] =  _groupListBy(castdata, 3)
        episodes = {}
        seenDuties = []
        for group in castdata:
            for mdata in group:
                duty = orig_duty = group[0][3]
                if duty not in seenDuties: seenDuties.append(orig_duty)
                note = mdata[2] or u''
                if mdata[4].has_key('episode of'):
                    duty = 'episodes'
                    if orig_duty not in ('actor', 'actress'):
                        if note: note = ' %s' % note
                        note = '[%s]%s' % (orig_duty, note)
                curRole = mdata[1]
                curRoleID = None
                if curRole is not None:
                    robj = CharName.get(curRole)
                    curRole = robj.name
                    curRoleID = robj.id
                m = Movie(movieID=mdata[0], data=mdata[4],
                            currentRole=curRole or u'',
                            roleID=curRoleID,
                            notes=note, accessSystem='sql')
                if duty != 'episodes':
                    res.setdefault(duty, []).append(m)
                else:
                    episodes.setdefault(m['episode of'], []).append(m)
        if episodes:
            for k in episodes:
                episodes[k].sort()
                episodes[k].reverse()
            res['episodes'] = episodes
        for duty in seenDuties:
            if res.has_key(duty):
                if duty in ('actor', 'actress', 'himself', 'herself',
                            'themselves'):
                    res[duty] = merge_roles(res[duty])
                res[duty].sort()
        # XXX: is 'guest' still needed?  I think every GA reference in
        #      the biographies.list file was removed.
        if res.has_key('guest'):
            res['notable tv guest appearances'] = res['guest']
            del res['guest']
        # Info about the person.
        pinfo = [(self._info[pi.infoTypeID], pi.info, pi.note)
                for pi in PersonInfo.select(PersonInfo.q.personID == personID)]
        # Regroup by duty.
        pinfo = _groupListBy(pinfo, 0)
        for group in pinfo:
            sect = group[0][0]
            for pdata in group:
                data = pdata[1]
                if pdata[2]: data += '::%s' % pdata[2]
                res.setdefault(sect, []).append(data)
        # AKA names.
        akan = [(an.name, an.imdbIndex)
                for an in AkaName.select(AkaName.q.personID == personID)]
        if akan:
            res['akas'] = []
            for n in akan:
                nd = {'name': n[0]}
                if n[1]: nd['imdbIndex'] = n[1]
                nt = build_name(nd, canonical=1)
                res['akas'].append(nt)
        # Do some transformation to preserve consistency with other
        # data access systems.
        for key in ('birth date', 'birth notes', 'death date', 'death notes',
                        'birth name', 'height'):
            if res.has_key(key):
                res[key] = res[key][0]
        if res.has_key('mini biography'):
            nl = []
            for i in res['mini biography']:
                if i[-1] == ')':
                    sauth = i.rfind('::(author: ')
                    if sauth != -1:
                        nl.append(i[sauth+11:-1] + '::' + i[:sauth])
                    else: nl.append(i)
                else: nl.append(i)
            res['mini biography'][:] = nl
        if res.has_key('guest'):
            res['notable tv guest appearances'] = res['guest']
            del res['guest']
        miscnames = res.get('nick names', [])
        if res.has_key('birth name'): miscnames.append(res['birth name'])
        if res.has_key('akas'):
            for mname in miscnames:
                if mname in res['akas']: res['akas'].remove(mname)
            if not res['akas']: del res['akas']
        trefs,nrefs = self._extractRefs(sub_dict(res,Person.keys_tomodify_list))
        return {'data': res, 'titlesRefs': trefs, 'namesRefs': nrefs,
                'info sets': infosets}

    # Just to know what kind of information are available.
    get_person_filmography = get_person_main
    get_person_biography = get_person_main
    get_person_other_works = get_person_main
    get_person_episodes = get_person_main

    def _search_character(self, name, results):
        name = name.strip()
        if not name: return []
        s_name = analyze_name(name)['name']
        if not s_name: return []
        if isinstance(s_name, UnicodeType):
            s_name = s_name.encode('ascii', 'ignore')
        s_name = normalizeName(s_name)
        soundexCode = soundex(s_name)
        surname = s_name.split(' ')[-1]
        surnameSoundex = soundex(surname)
        name2 = ''
        soundexName2 = None
        nsplit = s_name.split()
        if len(nsplit) > 1:
            name2 = '%s %s' % (nsplit[-1], ' '.join(nsplit[:-1]))
            if s_name == name2:
                name2 = ''
            else:
                soundexName2 = soundex(name2)
        # If the soundex is None, compare only with the first
        # phoneticCode column.
        if soundexCode is not None:
            if soundexName2 is not None:
                condition = OR(surnameSoundex == CharName.q.surnamePcode,
                            IN(CharName.q.namePcodeNf, [soundexCode,
                                                        soundexName2]),
                            IN(CharName.q.surnamePcode, [soundexCode,
                                                        soundexName2]))
            else:
                condition = OR(surnameSoundex == CharName.q.surnamePcode,
                            IN(soundexCode, [CharName.q.namePcodeNf,
                                            CharName.q.surnamePcode]))
        else:
            condition = ISNULL(Name.q.namePcodeNf)
        try:
            qr = [(q.id, {'name': q.name, 'imdbIndex': q.imdbIndex})
                    for q in CharName.select(condition)]
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to search the database: "%s"' % str(e)
        res = scan_names(qr, s_name, name2, '', results,
                        _scan_character=True)
        res[:] = [x[1] for x in res]
        # Purge empty imdbIndex.
        returnl = []
        for x in res:
            tmpd = x[1]
            if tmpd['imdbIndex'] is None:
                del tmpd['imdbIndex']
            returnl.append((x[0], tmpd))
        return returnl

    def get_character_main(self, characterID, results=1000):
        # Every person information is retrieved from here.
        infosets = self.get_character_infoset()
        try:
            c = CharName.get(characterID)
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to get characterID "%s": "%s"' % (characterID, e)
        res = {'name': c.name, 'imdbIndex': c.imdbIndex}
        if res['imdbIndex'] is None: del res['imdbIndex']
        if not res:
            raise IMDbDataAccessError, 'unable to get characterID "%s"' % \
                                        characterID
        # Collect filmography information.
        items = CastInfo.select(CastInfo.q.personRoleID == characterID)
        if results > 0:
            items = items[:results]
        filmodata = [(cd.movieID, cd.personID, cd.note,
                    get_movie_data(cd.movieID, self._kind)) for cd in items
                    if self._role[cd.roleID] in ('actor', 'actress')]
        fdata = []
        for f in filmodata:
            curRole = None
            curRoleID = f[1]
            note = f[2] or u''
            if curRoleID is not None:
                robj = Name.get(curRoleID)
                curRole = robj.name
            m = Movie(movieID=f[0], data=f[3],
                        currentRole=curRole or u'',
                        roleID=curRoleID, roleIsPerson=True,
                        notes=note, accessSystem='sql')
            fdata.append(m)
        fdata = merge_roles(fdata)
        fdata.sort()
        if fdata:
            res['filmography'] = fdata
        return {'data': res, 'info sets': infosets}

    get_character_filmography = get_character_main
    get_character_biography = get_character_main

    def _search_company(self, name, results):
        name = name.strip()
        if not name: return []
        if isinstance(name, UnicodeType):
            name = name.encode('ascii', 'ignore')
        soundexCode = soundex(name)
        # If the soundex is None, compare only with the first
        # phoneticCode column.
        if soundexCode is None:
            condition = ISNULL(CompanyName.q.namePcodeNf)
        else:
            if name.endswith(']'):
                condition = CompanyName.q.namePcodeSf == soundexCode
            else:
                condition = CompanyName.q.namePcodeNf == soundexCode
        try:
            qr = [(q.id, {'name': q.name, 'country': q.countryCode})
                    for q in CompanyName.select(condition)]
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to search the database: "%s"' % str(e)
        qr[:] = [(x[0], build_company_name(x[1])) for x in qr]
        res = scan_company_names(qr, name, results)
        res[:] = [x[1] for x in res]
        # Purge empty country keys.
        returnl = []
        for x in res:
            tmpd = x[1]
            country = tmpd.get('country')
            if country is None and tmpd.has_key('country'):
                del tmpd['country']
            returnl.append((x[0], tmpd))
        return returnl

    def get_company_main(self, companyID, results=0):
        # Every company information is retrieved from here.
        infosets = self.get_company_infoset()
        try:
            c = CompanyName.get(companyID)
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to get companyID "%s": "%s"' % (companyID, e)
        res = {'name': c.name, 'country': c.countryCode}
        if res['country'] is None: del res['country']
        if not res:
            raise IMDbDataAccessError, 'unable to get companyID "%s"' % \
                                        companyID
        # Collect filmography information.
        items = MovieCompanies.select(MovieCompanies.q.companyID == companyID)
        if results > 0:
            items = items[:results]
        filmodata = [(cd.movieID, cd.companyID,
                    self._compType[cd.companyTypeID], cd.note,
                    get_movie_data(cd.movieID, self._kind)) for cd in items]
        filmodata = _groupListBy(filmodata, 2)
        for group in filmodata:
            ctype = group[0][2]
            for movieID, companyID, ctype, note, movieData in group:
                movie = Movie(data=movieData, movieID=movieID,
                            notes=note or u'', accessSystem=self.accessSystem)
                res.setdefault(ctype, []).append(movie)
            res.get(ctype, []).sort()
        return {'data': res, 'info sets': infosets}

    def __del__(self):
        """Ensure that the connection is closed."""
        if not hasattr(self, '_connection'): return
        self._connection.close()

