"""
parser.sql package (imdb package).

This package provides the IMDbSqlAccessSystem class used to access
IMDb's data through a SQL database.  Every database supported by
the SQLObject Object Relational Manager is available.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "sql", "database" or "db".

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

# FIXME: this whole module was written in a veeery short amount of time.
#        The code should be commented, rewritten and cleaned. :-)

from sqlobject.sqlbuilder import *

from dbschema import *

from imdb.parser.common.locsql import IMDbLocalAndSqlAccessSystem, \
                    scan_names, scan_titles, titleVariations, nameVariations
from imdb.utils import canonicalTitle, canonicalName, normalizeTitle, \
                        normalizeName, build_title, build_name, \
                        analyze_name, analyze_title, re_episodes, \
                        sortMovies, sortPeople, _articles
from imdb.Person import Person
from imdb.Movie import Movie
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


# FIXME: move these two function in the imdbpy2sql.py script.
def title_soundex(title):
    """Return the soundex code for the given title; the (optional) ending
    article is pruned.  It assumes to receive a title without year/imdbIndex
    or kind indications, but just the title string, as the one in the
    analyze_title(title)['title'] value."""
    # Prune non-ascii chars from the string.
    title = title.encode('ascii', 'ignore')
    if not title: return None
    ts = title.split(', ')
    # Strip the ending article, if any.
    if ts[-1] in _articles:
        title = ', '.join(ts[:-1])
    return soundex(title)

def name_soundexes(name):
    """Return three soundex codes for the given name; the name is assumed
    to be in the 'surname, name' format, without the imdbIndex indication,
    as the one in the analyze_name(name)['name'] value.
    The first one is the soundex of the name in the canonical format.
    The second is the soundex of the name in the normal format, if different
    from the first one.
    The third is the soundex of the surname, if different from the
    other two values."""
    # Prune non-ascii chars from the string.
    name = name.encode('ascii', 'ignore')
    if not name: return (None, None, None)
    s1 = soundex(name)
    name_normal = normalizeName(name)
    s2 = soundex(name_normal)
    if s1 == s2: s2 = None
    namesplit = name.split(', ')
    s3 = soundex(namesplit[0])
    if s3 and s3 in (s1, s2): s3 = None
    return (s1, s2, s3)


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


class IMDbSqlAccessSystem(IMDbLocalAndSqlAccessSystem):
    """The class used to access IMDb's data through a SQL database."""

    accessSystem = 'sql'

    def __init__(self, uri, adultSearch=1, *arguments, **keywords):
        """Initialize the access system."""
        IMDbLocalAndSqlAccessSystem.__init__(self, *arguments, **keywords)
        # Set the connection to the database.
        self._connection = setConnection(uri)
        # Maps movie's kind strings to kind ids.
        self._kind = {}
        for kt in KindType.select(): self._kind[str(kt.kind)] = kt.id
        info = [(it.id, it.info) for it in InfoType.select()]
        self._moviesubs = {}
        # Build self._moviesubs, a dictionary used to rearrange
        # the data structure for a movie object.
        for vid, vinfo in info:
            if not vinfo.startswith('LD '): continue
            self._moviesubs[vinfo] = ('laserdisc', vinfo[3:])
        self._moviesubs.update(_litd)
        self._moviesubs.update(_busd)
        self.do_adult_search(adultSearch)

    def _getTitleID(self, title):
        """Given a long imdb canonical title, returns a movieID or
        None if not found."""
        td = analyze_title(title)
        condition = None
        if td['kind'] == 'episode':
            epof = build_title(td['episode of'], canonical=1)
            seriesID = [s.id for s in Title.select(
                        AND(Title.q.title == epof['title'],
                            Title.q.imdbIndex == epof.get('imdbIndex'),
                           Title.q.kindID == self._kind[epof['kind']],
                           Title.q.productionYear == epof.get('year')))]
            if seriesID:
                condition = AND(IN(Title.q.episodeOfID, seriesID),
                                Title.q.title == td['title'],
                                Title.q.imdbIndex == td.get('imdbIndex'),
                                Title.q.kindID == self._kind[td['kind']],
                                Title.q.productionYear == td.get('year'))
        if condition is None:
            condition = AND(Title.q.title == td['title'],
                            Title.q.imdbIndex == td.get('imdbIndex'),
                            Title.q.kindID == self._kind[td['kind']],
                            Title.q.productionYear == td.get('year'))
        res = Title.select(condition)
        if res.count() != 1:
            return None
        return res[0].id

    def _getNameID(self, name):
        """Given a long imdb canonical name, returns a personID or
        None if not found."""
        nd = analyze_name(name)
        res = Name.select(AND(Name.q.name == nd['name'],
                                Name.q.imdbIndex == nd.get('imdbIndex')))
        if res.count() != 1:
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

    def _get_movie_data(self, movieID, fromAka=0):
        if not fromAka: Table = Title
        else: Table = AkaTitle
        m = Table.get(movieID)
        mdict = {'title': m.title, 'kind': str(m.kind.kind),
                'year': m.productionYear, 'imdbIndex': m.imdbIndex}
        if mdict['imdbIndex'] is None: del mdict['imdbIndex']
        if mdict['year'] is None: del mdict['year']
        else: mdict['year'] = str(mdict['year'])
        episodeOfID = m.episodeOfID
        if episodeOfID is not None:
            mdict['episode of'] = self._get_movie_data(episodeOfID, fromAka)
        return mdict

    def get_imdbMovieID(self, movieID):
        """Translate a movieID in an imdbID.
        If not in the database, try an Exact Primary Title search on IMDb;
        return None if it's unable to get the imdbID.
        """
        try: movie = Title.get(movieID)
        except SQLObjectNotFound: return None
        imdbID = movie.imdbID
        if imdbID is not None: return '%07d' % imdbID
        m_dict = self._get_movie_data(movie.id)
        titline = build_title(m_dict, canonical=1, ptdf=1)
        imdbID = self._title2imdbID(titline)
        # If the imdbID was retrieved from the web and was not in the
        # database, update the database (ignoring errors, because it's
        # possibile that the current user has not update privileges).
        # There're times when I think I'm a genius; this one of
        # those times... <g>
        if imdbID is not None:
            try: movie.imdbID = imdbID
            except SQLObjectNotFound: pass
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
        imdbID = self._name2imdbID(namline)
        if imdbID is not None:
            try: person.imdbID = imdbID
            except SQLObjectNotFound: pass
        return imdbID

    def do_adult_search(self, doAdult):
        """If set to 0 or False, movies in the Adult category are not
        shown in the results of a search."""
        self.doAdult = doAdult

    def _search_movie(self, title, results):
        title = title.strip()
        if not title: return []

        s_title = analyze_title(title)['title']
        if not s_title: return []
        soundexCode = soundex(s_title)
        # Up to 3 variations of the title are searched, plus the
        # long imdb canonical title, if provided.
        title1, title2, title3 = titleVariations(title)

        try:
            qr = [(q.id, self._get_movie_data(q.id)) for q
                    in Title.select(Title.q.phoneticCode == soundexCode)]
            qr += [(q.movieID, self._get_movie_data(q.id, fromAka=1)) for q
                    in AkaTitle.select(AkaTitle.q.phoneticCode == soundexCode)]
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to search the database: "%s"' % str(e)

        resultsST = results
        if not self.doAdult: resultsST = 0
        res = scan_titles(qr, title1, title2, title3, resultsST)
        if self.doAdult and results > 0: res[:] = res[:results]
        res[:] = [x[1] for x in res]

        if res and not self.doAdult:
            mids = [x[0] for x in res]
            genreID = InfoType.select(InfoType.q.info == 'genres')[0].id
            adultlist = [al.id for al
                        in MovieInfo.select(
                            AND(MovieInfo.q.infoTypeID == genreID,
                                MovieInfo.q.info == 'Adult',
                                IN(MovieInfo.q.id, mids)))]
            res[:] = [x for x in res if x[0] not in adultlist]
            if results > 0: res[:] = res[:results]
        return res
        
    def get_movie_main(self, movieID):
        # Every movie information is retrieved from here.
        infosets = self.get_movie_infoset()
        try:
            res = self._get_movie_data(movieID)
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to get movieID "%s": "%s"' % (movieID, str(e))
        if not res:
            raise IMDbDataAccessError, 'unable to get movieID "%s"' % movieID
        # Collect cast information.
        castdata = [[cd.personID, cd.personRole, cd.note, cd.nrOrder,
                    str(cd.role.role), cd.person.name, cd.person.imdbIndex]
                    for cd in CastInfo.select(CastInfo.q.movieID == movieID)]
        for p in castdata:
            if p[4] in ('actor', 'actress'):
                p[4] = 'cast'
        # Regroup by role/duty (cast, writer, director, ...)
        castdata[:] =  _groupListBy(castdata, 4)
        for group in castdata:
            duty = group[0][4]
            for pdata in group:
                p = Person(personID=pdata[0], name=pdata[5],
                            currentRole=pdata[1] or u'', notes=pdata[2] or u'',
                            accessSystem='sql')
                if pdata[6]: p['imdbIndex'] = pdata[6]
                p.billingPos = pdata[3]
                res.setdefault(duty, []).append(p)
            res[duty].sort(sortPeople)
        # Info about the movie.
        minfo = [(m.infoType.info, m.info, m.note)
                for m in MovieInfo.select(MovieInfo.q.movieID == movieID)]
        minfo = _groupListBy(minfo, 0)
        for group in minfo:
            sect = group[0][0]
            for mdata in group:
                data = mdata[1]
                if mdata[2]: data += '::%s' % mdata[2]
                res.setdefault(sect, []).append(data)
        # AKA titles.
        akat = [(self._get_movie_data(at.id, fromAka=1), at.note)
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
        compcast = [(cc.subject.kind, cc.subject.kind, cc.note) for cc
                    in CompleteCast.select(CompleteCast.q.movieID == movieID)]
        if compcast:
            for entry in compcast:
                val = entry[1]
                if entry[2]: val += '::%s' % entry[2]
                res['complete %s' % entry[0]] = val
        # Movie connections.
        mlinks = [[ml.linkedMovieID, ml.linkType.link, ml.note]
                    for ml in MovieLink.select(MovieLink.q.movieID == movieID)]
        if mlinks:
            for ml in mlinks:
                lmovieData = self._get_movie_data(ml[0])
                m = Movie(movieID=ml[0], data=lmovieData, accessSystem='sql')
                if ml[2] is not None: m.notes = ml[2]
                ml[0] = m
            res['connections'] = {}
            mlinks[:] = _groupListBy(mlinks, 1)
            for group in mlinks:
                lt = group[0][1]
                res['connections'][lt] = [i[0] for i in group]
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
                res['episodes'] = episodes[0]
        if res.has_key('year'):
            res['year'] = str(res['year'])
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
        soundexCode = soundex(s_name)
        name1, name2, name3 = nameVariations(name)

        # If the soundex is None, compare only with the first
        # phoneticCode column.
        if soundexCode is not None:
            condition = IN(soundexCode, [Name.q.phoneticCode1,
                                        Name.q.phoneticCode2,
                                        Name.q.phoneticCode3])
            conditionAka = IN(soundexCode, [AkaName.q.phoneticCode1,
                                            AkaName.q.phoneticCode2,
                                            AkaName.q.phoneticCode3])
        else:
            condition = ISNULL(Name.q.phoneticCode1)
            conditionAka = ISNULL(AkaName.q.phoneticCode1)

        try:
            qr = [(q.id, {'name': q.name, 'imdbIndex': q.imdbIndex})
                    for q in Name.select(condition)]
            qr += [(q.movieID, {'name': q.name, 'imdbIndex': q.imdbIndex})
                    for q in AkaName.select(conditionAka)]
        except SQLObjectNotFound, e:
            raise IMDbDataAccessError, \
                    'unable to search the database: "%s"' % str(e)

        resultsST = results
        if not self.doAdult: resultsST = 0
        res = scan_names(qr, name1, name2, name3, resultsST)
        if results > 0: res[:] = res[:results]
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
        castdata = [(cd.movieID, cd.personRole, cd.note, cd.role.role,
                    self._get_movie_data(cd.movieID))
                for cd in CastInfo.select(CastInfo.q.personID == personID)]
        # Regroup by role/duty (cast, writer, director, ...)
        castdata[:] =  _groupListBy(castdata, 3)
        for group in castdata:
            duty = group[0][3]
            for mdata in group:
                m = Movie(movieID=mdata[0], data=mdata[4],
                            currentRole=mdata[1] or u'',
                            notes=mdata[2] or u'',
                            accessSystem='sql')
                res.setdefault(duty, []).append(m)
            res[duty].sort(sortMovies)
        # XXX: is 'guest' still needed?  I think every GA reference in
        #      the biographies.list file was removed.
        if res.has_key('guest'):
            res['notable tv guest appearances'] = res['guest']
            del res['guest']
        # Info about the person.
        pinfo = [(pi.infoType.info, pi.info, pi.note)
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

    def __del__(self):
        """Ensure that the connection is closed."""
        self._connection.close()

