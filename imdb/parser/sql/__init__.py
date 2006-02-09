# -*- coding: utf-8 -*-
"""
parser.sql package (imdb package).

This package provides the IMDbSqlAccessSystem class used to access
IMDb's data through a SQL database.
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

import MySQLdb
import _mysql_exceptions

from imdb.parser.common.locsql import IMDbLocalAndSqlAccessSystem, \
                    scan_names, scan_titles, titleVariations, nameVariations
from imdb.utils import canonicalTitle, canonicalName, normalizeTitle, \
                        normalizeName, build_title, build_name, \
                        analyze_name, analyze_title, re_episodes, \
                        sortMovies, sortPeople
from imdb.Person import Person
from imdb.Movie import Movie
from imdb._exceptions import IMDbDataAccessError, IMDbError

_uctype = type(u'')

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

    def __init__(self, db, user, passwd, host='localhost', miscDBargs=None,
                adultSearch=1, *arguments, **keywords):
        """Initialize the access system."""
        IMDbLocalAndSqlAccessSystem.__init__(self, *arguments, **keywords)
        if miscDBargs is None: miscDBargs = {}
        initdict = miscDBargs
        initdict.update({'db': db, 'user': user, 'host': host, 'passwd': passwd,
                        'use_unicode': 'latin1'})
        try:
            self._db = MySQLdb.connect(**initdict)
            self._curs = self._db.cursor()
        except _mysql_exceptions.Error, e:
            errstr = 'Error connecting to database (PARAMS: %s)' % initdict
            errstr += '\n%s' % str(e)
            raise IMDbDataAccessError, errstr
        try: self._curs.execute('SET NAMES "latin1";')
        except _mysql_exceptions.MySQLError: pass
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
        self.do_adult_search(adultSearch)

    def _getNameID(self, name):
        """Given a long imdb canonical name, returns a personID or
        None if not found."""
        nd = analyze_name(name)
        sql = 'SELECT personid FROM names WHERE name = %s'
        data = [nd.get('name', u'').encode('latin_1', 'replace')]
        indx = nd.get('imdbIndex', u'').encode('latin_1', 'replace')
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
        data = [td.get('title', u'').encode('latin_1', 'replace'),
                td.get('kind', u'').encode('latin_1', 'replace')]
        indx = td.get('imdbIndex', u'').encode('latin_1', 'replace')
        if indx:
            sql += ' AND imdbindex = %s'
            data.append(indx)
        year = td.get('year', u'').encode('latin_1', 'replace')
        if year and year != '????':
            sql += ' AND year = %s'
            data.append(year)
        sql += ' LIMIT 1;'
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
        # possibile that the current user has not update privileges).
        # There're times when I think I'm a genius; this one of
        # those times... <g>
        try:
            if imdbID is not None:
                self.query('UPDATE titles SET imdbid = %s WHERE movieid = %s;' %
                            (imdbID, movieID))
        except IMDbDataAccessError:
            pass
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

    def do_adult_search(self, doAdult):
        """If set to 0 or False, movies in the Adult category are not
        shown in the results of a search."""
        self.doAdult = doAdult

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
        title = title.strip()
        if not title: return []
        # Up to 3 variations of the title are searched, plus the
        # long imdb canonical title, if provided.
        title1, title2, title3 = titleVariations(title)
        resd = {}
        # Build the SOUNDEX(title) IN ... clause.
        sndex = "(SOUNDEX('%s')" % _(title1)
        if title2 and title2 != title1: sndex += ", SOUNDEX('%s')" % _(title2)
        sndex += ')'

        sqlq = "SELECT movieid, title, imdbindex, kind, year " + \
                "FROM titles WHERE LEFT(SOUNDEX(title),5) IN %s " % sndex + \
                "OR LEFT(SOUNDEX(LEFT(title, LENGTH(title)-" + \
                "LOCATE(' ,', REVERSE(title))+1)),5) = " + \
                "LEFT(SOUNDEX('%s'),5)" % _(title2)

        if type(sqlq) is _uctype: sqlq = sqlq.encode('latin_1', 'replace')
        qr = list(self.query(sqlq, escape=0))
        qr += list(self.query(sqlq.replace('titles', 'akatitles', 1), escape=0))

        resultsST = results
        if not self.doAdult: resultsST = 0
        res = scan_titles(qr, title1, title2, title3, resultsST)
        if self.doAdult and results > 0: res[:] = res[:results]
        res[:] = [x[1] for x in res]

        if not self.doAdult:
            mids = '(%s)' % ', '.join([str(x[0]) for x in res])
            adultlist = self.query('SELECT movieid FROM moviesinfo WHERE ' +
                                'movieid IN ' + mids + ' AND infoid = 3 AND ' +
                                'info = "Adult"', escape=0)
            adultlist = [x[0] for x in list(adultlist)]
            res[:] = [x for x in res if x[0] not in adultlist]
            if results > 0: res[:] = res[:results]

        returnl = []
        for x in res:
            tmpd = {'title': x[1], 'kind': x[3]}
            if x[2]: tmpd['imdbIndex'] = x[2]
            if x[4]: tmpd['year'] = x[4]
            returnl.append((x[0], tmpd))
        return returnl
        
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
        if not res:
            raise IMDbDataAccessError, 'unable to get movieID "%s"' % movieID
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
        castdata[:] =  _groupListBy(tmpcast, 4)
        for group in castdata:
            duty = self._roles[group[0][4]]
            for pdata in group:
                p = Person(personID=pdata[0], name=pdata[5],
                            currentRole=pdata[1] or u'', notes=pdata[2] or u'',
                            accessSystem='sql')
                if pdata[6]: p['imdbIndex'] = pdata[6]
                p.billingPos = pdata[3]
                res.setdefault(duty, []).append(p)
            res[duty].sort(sortPeople)
        # Info about the movie.
        minfo = self.query('SELECT infoid, info, note from moviesinfo ' +
                            'WHERE movieid = %s' % movieID)
        minfo = _groupListBy(minfo, 0)
        for group in minfo:
            sect = self._info[group[0][0]]
            for mdata in group:
                data = mdata[1]
                if mdata[2]: data += '::%s' % mdata[2]
                res.setdefault(sect, []).append(data)
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
                if t[4]:
                    net = self._changeAKAencoding(t[4], nt)
                    if net is not None: nt = net
                    nt += '::%s' % t[4]
                if nt not in res['akas']: res['akas'].append(nt)
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
        if res.has_key('mpaa'):
            res['mpaa'] = res['mpaa'][0]
        if res.has_key('guest'):
            res['guests'] = res['guest']
            del res['guest']
        trefs,nrefs = self._extractRefs(sub_dict(res,Movie.keys_tomodify_list))
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
    def get_movie_guests(self, movieID): return self.get_movie_main(movieID)

    def _search_person(self, name, results):
        name = name.strip()
        if not name: return []
        name1, name2, name3 = nameVariations(name)

        sndex = "(LEFT(SOUNDEX('%s'),5)" % _(name1)
        if name2 and name2 != name1:
            sndex += ", LEFT(SOUNDEX('%s'),5)" % _(name2)
        sndex += ')'

        # In the database there's a list of "Surname, Name".
        # Try matching against "Surname, Name", "Surname"
        # and "Name Surname".
        sqlq = "SELECT personid, name, imdbindex FROM names WHERE " + \
                "LEFT(SOUNDEX(name),5) IN %s " % sndex + \
                "OR LEFT(SOUNDEX(SUBSTRING_INDEX(name, ', ', 1)),5)" + \
                " IN %s " % sndex + \
                "OR LEFT(SOUNDEX(CONCAT(SUBSTRING_INDEX(name, ', ', -1)," + \
                " ' ', (SUBSTRING_INDEX(name, ', ', 1)))),5) IN %s;" % sndex
        # XXX: add a "LIMIT 5000" clause or something?

        if type(sqlq) is _uctype: sqlq = sqlq.encode('latin_1', 'replace')
        qr = list(self.query(sqlq, escape=0))
        qr += list(self.query(sqlq.replace('names', 'akanames', 1), escape=0))

        resultsST = results
        if not self.doAdult: resultsST = 0
        res = scan_names(qr, name1, name2, name3, resultsST)
        if results > 0: res[:] = res[:results]
        res[:] = [x[1] for x in res]
        # Purge empty imdbIndex and year.
        returnl = []
        for x in res:
            tmpd = {'name': x[1]}
            if x[2]: tmpd['imdbIndex'] = x[2]
            returnl.append((x[0], tmpd))
        return returnl

    def get_person_main(self, personID):
        # Every person information is retrieved from here.
        infosets = self.get_person_infoset()
        res = self._getDict('names', ('name', 'imdbIndex'),
                            'personid = %s' % personID, unique=1)
        if not res:
            raise IMDbDataAccessError, 'unable to get personID "%s"' % personID
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
        castdata[:] =  _groupListBy(castdata, 3)
        for group in castdata:
            duty = self._roles[group[0][3]]
            for mdata in group:
                m = Movie(movieID=mdata[0], title=mdata[4],
                            currentRole=mdata[1] or u'', notes=mdata[2] or u'',
                            accessSystem='sql')
                m['kind'] = mdata[6]
                if mdata[5]: m['imdbIndex'] = mdata[5]
                if mdata[7]: m['year'] = mdata[7]
                res.setdefault(duty, []).append(m)
            res[duty].sort(sortMovies)
        if res.has_key('guest'):
            res['notable tv guest appearances'] = res['guest']
            del res['guest']
        # Info about the person.
        pinfo = self.query('SELECT infoid, info, note from personsinfo ' +
                            'WHERE personid = %s' % personID)
        pinfo = _groupListBy(pinfo, 0)
        for group in pinfo:
            sect = self._info[group[0][0]]
            for pdata in group:
                data = pdata[1]
                if pdata[2]: data += '::%s' % pdata[2]
                res.setdefault(sect, []).append(data)
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
    def get_person_filmography(self, personID): return self.get_person_main(personID)
    def get_person_biography(self, personID): return self.get_person_main(personID)
    def get_person_other_works(self, personID): return self.get_person_main(personID)

    def __del__(self):
        """Ensure that the connection is closed."""
        self._db.close()


