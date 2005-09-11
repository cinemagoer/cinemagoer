"""
parser.sql package (imdb package).

This package provides the IMDbSqlAccessSystem class used to access
IMDb's data through a SQL database.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "sql", "database" or "db".

Copyright 2005 Davide Alberani <da@erlug.linux.it> 

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

from imdb.parser.common.locsql import IMDbLocalAndSqlAccessSystem, _last
from imdb.utils import canonicalTitle, canonicalName, normalizeTitle, \
                        normalizeName, build_title, build_name, \
                        analyze_name, analyze_title, re_episodes
from imdb.Person import Person
from imdb.Movie import Movie
from imdb._exceptions import IMDbDataAccessError, IMDbError

import MySQLdb
import _mysql_exceptions


_litlist = ['screenplay/teleplay', 'novel', 'adaption', 'book',
            'production process protocol', 'interviews',
            'printed media reviews', 'essays', 'other literature']
_litd = dict([(x, ('literature', x)) for x in _litlist])

_buslist = ['budget', 'weekend gross', 'gross', 'opening weekend', 'rentals',
            'admissions', 'filming dates', 'production dates', 'studios',
            'copyright holder']
_busd = dict([(x, ('business', x)) for x in _buslist])


def _(s):
    """Escape some harmful chars."""
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')


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
            if not r.has_key(newgr[k][0]):
                r[newgr[k][0]] = {}
            r[newgr[k][0]][newgr[k][1]] = v
        else: r[k] = v
    return r


def _groupListBy(l, index, sortByI=None, reverseSort=0):
    """Regroup items in a list in a list of lists, grouped by
    the value found in the given index."""
    tmpd = {}
    for item in l:
        if tmpd.has_key(item[index]): tmpd[item[index]].append(item)
        else: tmpd[item[index]] = [item]
    res = tmpd.values()
    if sortByI is not None:
        for i in xrange(len(res)):
            tmpl = [(x[sortByI] or _last, x) for x in res[i]]
            tmpl.sort()
            if reverseSort: tmpl.reverse()
            res[i][:] = [x[1] for x in tmpl]
    return res


def distance(a,b):
    "Calculates the Levenshtein distance between a and b."
    a = a.lower()
    b = b.lower()
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
    current = range(n+1)
    for i in xrange(1,m+1):
        previous, current = current, [i]+[0]*m
        for j in xrange(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
    return current[n]


class IMDbSqlAccessSystem(IMDbLocalAndSqlAccessSystem):
    """The class used to access IMDb's data through a SQL database."""

    accessSystem = 'sql'

    def __init__(self, db, user, passwd, host='localhost', miscDBargs={},
                *arguments, **keywords):
        """Initialize the access system."""
        IMDbLocalAndSqlAccessSystem.__init__(self, *arguments, **keywords)
        initdict = miscDBargs
        initdict.update({'db': db, 'user': user, 'host': host,
                        'passwd': passwd})
        try:
            self._db = MySQLdb.connect(**initdict)
            self._curs = self._db.cursor()
        except _mysql_exceptions.Error, e:
            errstr = 'Error connecting to database (PARAMS: %s)' % initdict
            errstr += '\n%s' % str(e)
            raise IMDbDataAccessError, errstr
        self._roles = dict(self.query('SELECT id, role FROM roletypes;'))
        self._roles[-1] = 'cast'
        info = list(self.query('SELECT id, info FROM infotypes;'))
        ldgroup = {}
        # Build self._moviesubs, a dictionary used to rearrange
        # the data structure for a movie object.
        for v in info:
            v = v[1]
            if not v.startswith('LD '): continue
            ldgroup[v] = ('laserdisc', v[3:])
        self._moviesubs = ldgroup
        self._moviesubs.update(_litd)
        self._moviesubs.update(_busd)
        # Dictionary used to convert between infoids and info labels.
        self._info = dict(info + [(x[1], x[0]) for x in info])
        # Collect the ids for actors and actresses from the db.
        self._actids = [x[0] for x in self._roles.items()
                        if x[1] in ('actor', 'actress')]
        lt = self.query('SELECT id, type FROM linktypes;')
        self._linktypes = dict(lt)

    def _getNameID(self, name):
        """Given a long imdb canonical name, returns a personID or
        None if not found."""
        nd = analyze_name(name)
        sql = 'SELECT personid FROM names WHERE name = %s'
        data = [nd.get('name')]
        indx = nd.get('imdbIndex')
        if indx:
            sql += ' AND imdbindex = %s'
            data.append(indx)
        sql += ' LIMIT 1;'
        try:
            self._curs.execute(sql, data)
            res = self._curs.fetchall()
        except _mysql_exceptions.Error, e:
            raise IMDbDataAccessError, 'Error in _getNameID("%s"):\n%s' % \
                                        (name, str(e))
        if not res: return None
        return res[0][0]

    def _getTitleID(self, title):
        """Given a long imdb canonical title, returns a movieID or
        None if not found."""
        td = analyze_title(title)
        sql = 'SELECT movieid FROM titles WHERE title = %s AND kind = %s'
        data = [td.get('title'), td.get('kind')]
        indx = td.get('imdbIndex')
        if indx:
            sql += ' AND imdbindex = %s'
            data.append(indx)
        year = td.get('year')
        if year and year != '????':
            sql += ' AND year = %s'
            data.append(year)
        try:
            self._curs.execute(sql, data)
            res = self._curs.fetchall()
        except _mysql_exceptions.Error, e:
            raise IMDbDataAccessError, 'Error in _getTitleID("%s"):\n%s' % \
                                        (title, str(e))
        if not res: return None
        return res[0][0]

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
    
    def get_imdbMovieID(self, movieID):
        """Translate a movieID in an imdbID.
        If not in the database, try an Exact Primary Title search on IMDb;
        return None if it's unable to get the imdbID.
        """
        imdbID = self.query('SELECT imdbid FROM titles WHERE ' +
                            'movieid = %s LIMIT 1;' % movieID)[0][0]
        if imdbID is not None: return '%07d' % imdbID
        titline = build_title(self._getDict('titles',
                            ('title', 'imdbIndex', 'kind', 'year'),
                            'movieid = %s' % movieID, unique=1), canonical=1)
        imdbID = self._httpMovieID(titline)
        # If the imdbID was retrieved from the web and was not in the
        # database, update the database (ignoring errors, because it's
        # possibile that the current use has not update privileges).
        # There're times when I think I'm a genius; this one of
        # those times... <g>
        if imdbID is not None:
            self.query('UPDATE titles SET imdbid = %s WHERE movieid = %s;' %
                        (imdbID, movieID))
        return imdbID

    def get_imdbPersonID(self, personID):
        """Translate a personID in an imdbID.
        If not in the database, try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID.
        """
        imdbID = self.query('SELECT imdbid FROM names WHERE ' +
                            'personid = %s LIMIT 1;' % personID)[0][0]
        if imdbID is not None: return '%07d' % imdbID
        namline = build_name(self._getDict('names',
                            ('name', 'imdbIndex'),
                            'personid = %s' % personID, unique=1), canonical=1)
        imdbID = self._httpPersonID(namline)
        if imdbID is not None:
            self.query('UPDATE names SET imdbid = %s WHERE personid = %s;' %
                        (imdbID, personID))
        return imdbID

    def query(self, sql, escape=1):
        """Execute a SQL query and returns the results."""
        try:
            if escape: sql = _(sql)
            self._curs.execute(sql)
            return self._curs.fetchall()
        except _mysql_exceptions.Error, e:
            raise IMDbDataAccessError, 'Error in query("%s"):\n%s' % \
                                    (sql, str(e))

    def _search_movie(self, title, results):
        res = []
        title3 = ''
        rfc = title.rfind(', ')
        # Up to 3 variations of the title are searched.
        _curres = []
        if rfc != -1:
            title2 = normalizeTitle(title)
            title3 = title[:rfc]
        else:
            title2 = canonicalTitle(title)
            rfc = title2.rfind(', ')
            if rfc != -1: title3 = title2[:rfc]
        for stitle in (title, title2, title3):
            if not stitle: continue
            qr = list(self.query("SELECT movieid, title, imdbindex, kind, " +
                                    "year FROM titles WHERE " +
                                    "SOUNDEX(title) = SOUNDEX('%s');" %
                                    _(stitle), escape=0))
            qr += list(self.query("SELECT movieid, title, imdbindex, kind, " +
                                    "year FROM akatitles WHERE " +
                                    "SOUNDEX(title) = SOUNDEX('%s');" %
                                    _(stitle), escape=0))
            # Remove duplicated entries.
            for i in qr:
                if i not in _curres:
                    _curres.append(i)
                    # Calculate the distance with the searched title.
                    res.append((distance(stitle, i[1]), i))
        del _curres
        res.sort()
        res[:] = res[:results]
        res[:] = [x[1] for x in res]
        # Purge empty imdbIndex and year.
        purged = []
        for x in res:
            tmpd = {'title': x[1], 'kind': x[3]}
            if x[2]: tmpd['imdbIndex'] = x[2]
            if x[4]: tmpd['year'] = x[4]
            purged.append((x[0], tmpd))
        return purged
        
    def _getDict(self, table, cols, clause='', unique=0):
        """Return a list of dictionaries with data from the given
        table and columns; if unique is specified, only the first
        result is returned."""
        if clause: clause = ' WHERE %s' % clause
        if unique: clause += ' LIMIT 1'
        res = self.query('SELECT %s FROM %s%s;' %
                            (', '.join(cols).lower(), table, clause))
        res = [dict(zip(cols, x)) for x in res]
        if unique and res: return res[0]
        return res

    def get_movie_main(self, movieID):
        # Every movie information is retrieved from here.
        infosets = self.get_movie_infoset()
        res = self._getDict('titles',
                            ('title', 'imdbIndex', 'kind', 'year'),
                            'movieid = %s' % movieID, unique=1)
        if res['imdbIndex'] is None: del res['imdbIndex']
        if res['year'] is None: del res['year']
        if not res:
            raise IMDbDataAccessError, 'unable to get movieID "%s"' % movieID
        # Collect cast information.
        castdata = list(self.query('SELECT names.personid, cast.currentRole, ' +
                        'cast.note, cast.nrorder, cast.roleid, ' +
                        'names.name, names.imdbIndex FROM cast ' +
                        'INNER JOIN names USING (personid) WHERE ' +
                        'cast.movieid = %s' % movieID))
        # Change id for actor and actress to -1, so that they both will
        # be included in the 'cast' list.
        tmpcast = []
        for i in castdata:
            if i[4] in self._actids:
                tmpcast.append((i[0], i[1], i[2], i[3], -1, i[5], i[6]))
            else:
                tmpcast.append(i)
        # Regroup by role/duty (cast, writer, director, ...)
        castdata[:] =  _groupListBy(tmpcast, 4, 3)
        for group in castdata:
            duty = self._roles[group[0][4]]
            if not res.has_key(duty): res[duty] = []
            for pdata in group:
                p = Person(personID=pdata[0], name=pdata[5],
                            currentRole=pdata[1], notes=pdata[2],
                            accessSystem='sql')
                if pdata[6]: p['imdbIndex'] = pdata[6]
                res[duty].append(p)
        # Info about the movie.
        minfo = self.query('SELECT infoid, info, note from moviesinfo ' +
                            'WHERE movieid = %s' % movieID)
        minfo = _groupListBy(minfo, 0)
        for group in minfo:
            sect = self._info[group[0][0]]
            if not res.has_key(sect): res[sect] = []
            for mdata in group:
                data = mdata[1]
                if mdata[2]: data += '::%s' % mdata[2]
                res[sect].append(data)
        # AKA titles.
        akat = self.query('SELECT title, imdbindex, kind, year, note ' +
                            'FROM akatitles WHERE movieid = %s;' % movieID)
        if akat:
            res['akas'] = []
            for t in akat:
                td = {'title': t[0], 'kind': t[2]}
                if t[1]: td['imdbIndex'] = t[1]
                if t[3]: td['year'] = t[3]
                nt = build_title(td, canonical=1)
                if t[4]: nt += '::%s' % t[4]
                res['akas'].append(nt)
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
        # Complete cast/crew.
        compcast = self.query('SELECT object, status, note FROM completecast ' +
                            'WHERE movieid = %s;' % movieID)
        if compcast:
            for entry in compcast:
                val = entry[1]
                if entry[2]: val += '::%s' % entry[2]
                res['complete %s' % entry[0]] = val
        # Movie connections.
        mlinks = list(self.query('SELECT movietoid, linktypeid, note ' +
                                'FROM movielinks ' +
                                'WHERE movieid = %s' % movieID))
        if mlinks:
            midto = [str(x[0]) for x in mlinks]
            midd = {}
            midl = self.query('SELECT movieid, title, imdbIndex, year, kind ' +
                                'FROM titles WHERE movieid in (%s);' %
                                ', '.join(midto))
            for j in midl:
                m = Movie(movieID=j[0], title=j[1], accessSystem='sql')
                m['kind'] = j[4]
                if j[3]: m['year'] = j[3]
                if j[2]: m['imdbIndex'] = j[2]
                midd[j[0]] = m
            res['connections'] = {}
            mlinks[:] = _groupListBy(mlinks, 1)
            for group in mlinks:
                lt = self._linktypes[group[0][1]]
                res['connections'][lt] = []
                for item in group:
                    m = midd[item[0]]
                    if item[2]: m.notes = item[2]
                    res['connections'][lt].append(m)
        res = _reGroupDict(res, self._moviesubs)
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
        trefs, nrefs = self._extractRefs(res)
        return {'data': res, 'titlesRefs': trefs, 'namesRefs': nrefs,
                'info sets': infosets}

    # Just to know what kind of information are available.
    def get_movie_alternate_versions(self, movieID): return self.get_movie_main(movieID)
    def get_movie_business(self, movieID): return self.get_movie_main(movieID)
    def get_movie_connections(self, movieID): return self.get_movie_main(movieID)
    def get_movie_crazy_credits(self, movieID): return self.get_movie_main(movieID)
    def get_movie_goofs(self, movieID): return self.get_movie_main(movieID)
    def get_movie_keywords(self, movieID): return self.get_movie_main(movieID)
    def get_movie_literature(self, movieID): return self.get_movie_main(movieID)
    def get_movie_locations(self, movieID): return self.get_movie_main(movieID)
    def get_movie_plot(self, movieID): return self.get_movie_main(movieID)
    def get_movie_quotes(self, movieID): return self.get_movie_main(movieID)
    def get_movie_release_dates(self, movieID): return self.get_movie_main(movieID)
    def get_movie_soundtrack(self, movieID): return self.get_movie_main(movieID)
    def get_movie_taglines(self, movieID): return self.get_movie_main(movieID)
    def get_movie_technical(self, movieID): return self.get_movie_main(movieID)
    def get_movie_trivia(self, movieID): return self.get_movie_main(movieID)
    def get_movie_vote_details(self, movieID): return self.get_movie_main(movieID)

    def _search_person(self, name, results):
        res = []
        rfc = name.rfind(', ')
        name2 = ''
        _curres = []
        # Up to 2 variations of the name are searched.
        if rfc != -1:
            name2 = normalizeName(name)
        else:
            name2 = canonicalName(name)
        for sname in (name, name2):
            if not sname: continue
            qr = list(self.query("SELECT personid, name, imdbindex " +
                                    "FROM names WHERE " +
                                    "SOUNDEX(name) = SOUNDEX('%s');" %
                                    _(sname), escape=0))
            qr += list(self.query("SELECT personid, name, imdbindex " +
                                    "FROM akanames WHERE " +
                                    "SOUNDEX(name) = SOUNDEX('%s');" %
                                    _(sname), escape=0))
            # Remove duplicated entries.
            for i in qr:
                if i not in _curres:
                    _curres.append(i)
                    # Calculate the distance with the searched name.
                    res.append((distance(sname, i[1]), i))
        del _curres
        res.sort()
        res[:] = res[:results]
        res[:] = [x[1] for x in res]
        # Purge empty imdbIndex and year.
        purged = []
        for x in res:
            tmpd = {'name': x[1]}
            if x[2]: tmpd['imdbIndex'] = x[2]
            purged.append((x[0], tmpd))
        return purged

    def get_person_main(self, personID):
        # Every person information is retrieved from here.
        infosets = self.get_person_infoset()
        res = self._getDict('names', ('name', 'imdbIndex'),
                            'personid = %s' % personID, unique=1)
        if res['imdbIndex'] is None: del res['imdbIndex']
        if not res:
            raise IMDbDataAccessError, 'unable to get personID "%s"' % personID
        # Collect cast information.
        castdata = list(self.query('SELECT cast.movieid, cast.currentRole, ' +
                        'cast.note, cast.roleid, ' +
                        'titles.title, titles.imdbindex, titles.kind, ' +
                        'titles.year FROM cast ' +
                        'INNER JOIN titles USING (movieid) WHERE ' +
                        'cast.personid = %s' % personID))
        # Regroup by role/duty (cast, writer, director, ...)
        castdata[:] =  _groupListBy(castdata, 3, 7, reverseSort=1)
        for group in castdata:
            duty = self._roles[group[0][3]]
            if not res.has_key(duty): res[duty] = []
            for mdata in group:
                m = Movie(movieID=mdata[0], title=mdata[4],
                            currentRole=mdata[1], notes=mdata[2],
                            accessSystem='sql')
                m['kind'] = mdata[6]
                if mdata[5]: m['imdbIndex'] = mdata[5]
                if mdata[7]: m['year'] = mdata[7]
                res[duty].append(m)
        # Info about the person.
        pinfo = self.query('SELECT infoid, info, note from personsinfo ' +
                            'WHERE personid = %s' % personID)
        pinfo = _groupListBy(pinfo, 0)
        for group in pinfo:
            sect = self._info[group[0][0]]
            if not res.has_key(sect): res[sect] = []
            for pdata in group:
                data = pdata[1]
                if pdata[2]: data += '::%s' % pdata[2]
                res[sect].append(data)
        # AKA names.
        akan = self.query('SELECT name, imdbindex ' +
                            'FROM akanames WHERE personid = %s;' % personID)
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
        if res.has_key('crewmembers'):
            res['miscellaneouscrew'] = res['crewmembers']
            del res['crewmembers']
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
        trefs, nrefs = self._extractRefs(res)
        return {'data': res, 'titlesRefs': trefs, 'namesRefs': nrefs,
                'info sets': infosets}

    # Just to know what kind of information are available.
    def get_person_filmography(self, personID): return self.get_person_main(personID)
    def get_person_biography(self, personID): return self.get_person_main(personID)
    def get_person_other_works(self, personID): return self.get_person_main(personID)


