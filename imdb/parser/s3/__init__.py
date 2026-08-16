# Copyright 2017-2019 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
This package provides the IMDbS3AccessSystem class used to access IMDb's data
through the Amazon S3 dataset.

The :func:`imdb.IMDb` function will return an instance of this class when
called with the ``accessSystem`` parameter is set to "s3" or an s3 alias.
"""

import logging
from operator import itemgetter

import sqlalchemy

from imdb import IMDbBase
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import analyze_title

from .utils import (
    DB_TRANSFORM,
    KIND,
    name_soundexes,
    scan_names,
    scan_titles,
    title_soundex,
)


def split_array(text):
    """Split a string assuming it's an array.

    :param text: the text to split
    :type text: str
    :returns: list of splitted strings
    :rtype: list
    """
    if not isinstance(text, str):
        return text
    # for some reason, titles.akas.tsv.gz contains \x02 as a separator
    sep = ',' if ',' in text else '\x02'
    return text.split(sep)


class IMDbS3AccessSystem(IMDbBase):
    """The class used to access IMDb's data through the s3 dataset."""

    accessSystem = 's3'

    _KIND_REV = {v: k for k, v in KIND.items()}

    def get_movie_infoset(self):
        return ['main', 'plot', 'episodes']

    def get_person_infoset(self):
        return ['main', 'filmography', 'biography']
    _s3_logger = logging.getLogger('imdbpy.parser.s3')

    def __init__(self, uri='sqlite://cinemagoer.db', adultSearch=True, *arguments, **keywords):
        """Initialize the access system."""
        IMDbBase.__init__(self, *arguments, **keywords)
        self._engine = sqlalchemy.create_engine(uri, echo=False)
        self._metadata = sqlalchemy.MetaData()
        self._metadata.reflect(bind=self._engine)
        self.T = self._metadata.tables

    def _rename(self, table, data):
        for column, conf in DB_TRANSFORM.get(table, {}).items():
            if 'rename' not in conf:
                continue
            if column not in data:
                continue
            data[conf['rename']] = data[column]
            del data[column]
        return data

    def _clean(self, data, keys_to_remove=None):
        if keys_to_remove is None:
            keys_to_remove = []
        for key in list(data.keys()):
            if key in keys_to_remove or data[key] in (None, '', []):
                del data[key]
        return data

    def _normalize_title_data(self, row_data):
        data = self._rename('title_basics', dict(row_data))
        data['year'] = str(data.get('startYear') or '')
        if 'endYear' in data and data['endYear']:
            data['year'] += '-%s' % data['endYear']
        genres = data.get('genres') or ''
        data['genres'] = split_array(genres.lower())
        if 'runtimes' in data and data['runtimes']:
            data['runtimes'] = [data['runtimes']]
        self._clean(data, ('startYear', 'endYear', 'movieID'))
        return data

    def _fetchone(self, statement):
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return dict(row) if row else None

    def _fetchall(self, statement):
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [dict(row) for row in rows]

    def _base_title_info(self, movieID, movies_cache=None, persons_cache=None):
        if movies_cache is None:
            movies_cache = {}
        if persons_cache is None:
            persons_cache = {}
        if movieID in movies_cache:
            return movies_cache[movieID]
        tb = self.T['title_basics']
        movie = self._fetchone(sqlalchemy.select(tb).where(tb.c.tconst == movieID)) or {}
        data = self._normalize_title_data(movie)
        movies_cache[movieID] = data
        return data

    def _base_person_info(self, personID, movies_cache=None, persons_cache=None):
        if movies_cache is None:
            movies_cache = {}
        if persons_cache is None:
            persons_cache = {}
        if personID in persons_cache:
            return persons_cache[personID]
        nb = self.T['name_basics']
        person = self._fetchone(sqlalchemy.select(nb).where(nb.c.nconst == personID)) or {}
        data = self._rename('name_basics', person)
        movies = []
        for movieID in split_array(data.get('known for') or ''):
            if not movieID:
                continue
            movieID = int(movieID)
            movie_data = self._base_title_info(movieID, movies_cache=movies_cache, persons_cache=persons_cache)
            movie = Movie(movieID=movieID, data=movie_data, accessSystem=self.accessSystem)
            movies.append(movie)
        data['known for'] = movies
        self._clean(data, ('ns_soundex', 'sn_soundex', 's_soundex', 'personID'))
        persons_cache[personID] = data
        return data

    def get_movie_main(self, movieID):
        movieID = int(movieID)
        data = self._base_title_info(movieID)
        _movies_cache = {movieID: data}
        _persons_cache = {}

        tc = self.T['title_crew']
        movie = self._fetchone(sqlalchemy.select(tc).where(tc.c.tconst == movieID)) or {}
        tc_data = self._rename('title_crew', movie)
        writers = []
        directors = []
        for key, target in (('director', directors), ('writer', writers)):
            for personID in split_array(tc_data.get(key) or ''):
                if not personID:
                    continue
                personID = int(personID)
                person_data = self._base_person_info(personID,
                                                     movies_cache=_movies_cache,
                                                     persons_cache=_persons_cache)
                person = Person(personID=personID, data=person_data, accessSystem=self.accessSystem)
                target.append(person)
        tc_data['director'] = directors
        tc_data['writer'] = writers
        data.update(tc_data)

        te = self.T['title_episode']
        movie = self._fetchone(sqlalchemy.select(te).where(te.c.tconst == movieID)) or {}
        te_data = self._rename('title_episode', movie)
        if 'parentTconst' in te_data:
            parent_id = te_data['parentTconst']
            parent_data = self._base_title_info(parent_id)
            te_data['episode of'] = Movie(
                movieID=parent_id,
                data=parent_data,
                accessSystem=self.accessSystem,
            )
        self._clean(te_data, ('parentTconst',))
        data.update(te_data)

        tp = self.T['title_principals']
        movie_rows = self._fetchall(sqlalchemy.select(tp).where(tp.c.tconst == movieID)) or []
        roles = {}
        for movie_row in movie_rows:
            tp_data = self._rename('title_principals', dict(movie_row))
            category = tp_data.get('category')
            if not category:
                continue
            if category in ('actor', 'actress', 'self'):
                category = 'cast'
            roles.setdefault(category, []).append(movie_row)
        for role in roles:
            roles[role].sort(key=itemgetter('ordering'))
            persons = []
            for person_info in roles[role]:
                personID = person_info.get('nconst')
                if not personID:
                    continue
                person_data = self._base_person_info(personID,
                                                     movies_cache=_movies_cache,
                                                     persons_cache=_persons_cache)
                person = Person(personID=personID, data=person_data,
                                billingPos=person_info.get('ordering'),
                                currentRole=person_info.get('characters'),
                                notes=person_info.get('job'),
                                accessSystem=self.accessSystem)
                persons.append(person)
            data[role] = persons

        tr = self.T['title_ratings']
        movie = self._fetchone(sqlalchemy.select(tr).where(tr.c.tconst == movieID)) or {}
        tr_data = self._rename('title_ratings', movie)
        data.update(tr_data)

        ta = self.T['title_akas']
        akas = self._fetchall(sqlalchemy.select(ta).where(ta.c.titleId == movieID))
        akas_list = []
        for aka in akas:
            ta_data = self._rename('title_akas', aka) or {}
            for key in list(ta_data.keys()):
                if not ta_data[key]:
                    del ta_data[key]
            for key in 't_soundex', 'movieID':
                if key in ta_data:
                    del ta_data[key]
            for key in 'types', 'attributes':
                if key not in ta_data:
                    continue
                ta_data[key] = split_array(ta_data[key])
            akas_list.append(ta_data)
        if akas_list:
            data['akas'] = akas_list

        self._clean(data, ('movieID', 't_soundex'))
        return {'data': data, 'info sets': ['main', 'plot']}

    # we don't really have plot information, yet
    get_movie_plot = get_movie_main

    def get_movie_episodes(self, movieID, season_nums='all'):
        """Return all known episodes of a series, optionally by season."""
        movieID = int(movieID)
        if season_nums == 'all':
            selected_seasons = None
        else:
            if isinstance(season_nums, (int, str)):
                season_nums = (season_nums,)
            selected_seasons = {
                int(season) if isinstance(season, str) and season.isdigit() else season
                for season in season_nums
            }

        te = self.T['title_episode']
        tb = self.T['title_basics']
        tr = self.T['title_ratings']
        title_columns = [
            column.label('_title_%s' % column.name)
            for column in tb.c
        ]
        rating_columns = [
            column.label('_rating_%s' % column.name)
            for column in tr.c
        ]
        episode_rows = self._fetchall(
            sqlalchemy.select(*te.c, *title_columns, *rating_columns)
            .select_from(te)
            .outerjoin(tb, tb.c.tconst == te.c.tconst)
            .outerjoin(tr, tr.c.tconst == te.c.tconst)
            .where(te.c.parentTconst == movieID)
        )
        if not episode_rows:
            return {
                'data': {'episodes': {}, 'number of episodes': 0},
                'info sets': ['episodes'],
            }

        parent_data = self._base_title_info(movieID)
        parent = Movie(
            movieID=movieID,
            data=parent_data,
            accessSystem=self.accessSystem,
        )

        episodes = {}
        number_of_episodes = 0
        for row in episode_rows:
            episode_id = row['tconst']
            season_number = row.get('seasonNumber')
            episode_number = row.get('episodeNumber')
            season_key = season_number if season_number is not None else 'unknown season'
            if selected_seasons is not None and season_key not in selected_seasons:
                continue

            title_data = {
                column.name: row['_title_%s' % column.name]
                for column in tb.c
            }
            data = self._normalize_title_data(title_data)
            rating_data = {
                column.name: row['_rating_%s' % column.name]
                for column in tr.c
            }
            rating_data = self._rename('title_ratings', rating_data)
            data.update(self._clean(rating_data, ('movieID',)))
            episode_data = {
                column.name: row[column.name]
                for column in te.c
            }
            episode_data = self._rename('title_episode', episode_data)
            self._clean(episode_data, ('movieID', 'parentTconst'))
            data.update(episode_data)
            data['episode of'] = parent
            episode = Movie(
                movieID=episode_id,
                data=data,
                accessSystem=self.accessSystem,
            )

            season = episodes.setdefault(season_key, {})
            episode_key = episode_number
            if episode_key is None or episode_key in season:
                episode_key = 'tt%07d' % episode_id
            season[episode_key] = episode
            number_of_episodes += 1

        return {
            'data': {
                'episodes': episodes,
                'number of episodes': number_of_episodes,
            },
            'info sets': ['episodes'],
        }

    def get_person_main(self, personID):
        personID = int(personID)
        data = self._base_person_info(personID)
        self._clean(data, ('personID',))
        return {'data': data, 'info sets': self.get_person_infoset()}

    get_person_filmography = get_person_main
    get_person_biography = get_person_main

    def _search_movie(self, title, results, _episodes=False, adult=None, title_types=None):
        title = title.strip()
        if not title:
            return []

        title_info = analyze_title(title)
        search_title = title_info.get('title', title).strip()
        search_year = title_info.get('year')
        search_title_types = title_types

        def _search(search_title, search_year=None):
            t_soundex = title_soundex(search_title)
            tb = self.T['title_basics']
            conditions = [tb.c.t_soundex == t_soundex]
            filter_conditions = []
            if search_year is not None:
                year_condition = tb.c.startYear == search_year
                conditions.append(year_condition)
                filter_conditions.append(year_condition)
            if _episodes:
                title_type_col = getattr(tb.c, 'titleType', None)
                if title_type_col is None:
                    title_type_col = getattr(tb.c, 'kind', None)
                if title_type_col is not None:
                    episode_condition = title_type_col.in_(('episode', 'tvEpisode'))
                    conditions.append(episode_condition)
                    filter_conditions.append(episode_condition)
            if adult is not None:
                adult_col = getattr(tb.c, 'isAdult', None)
                if adult_col is None:
                    adult_col = getattr(tb.c, 'adult', None)
                if adult_col is not None:
                    adult_condition = adult_col == bool(adult)
                    conditions.append(adult_condition)
                    filter_conditions.append(adult_condition)
            if search_title_types:
                if isinstance(search_title_types, str):
                    normalized_title_types = [search_title_types]
                else:
                    normalized_title_types = list(search_title_types)
                normalized_types = []
                for t in normalized_title_types:
                    if t in self._KIND_REV:
                        normalized_types.append(self._KIND_REV[t])
                    else:
                        normalized_types.append(t)
                title_type_col = getattr(tb.c, 'titleType', None)
                if title_type_col is None:
                    title_type_col = getattr(tb.c, 'kind', None)
                if title_type_col is not None:
                    title_type_condition = title_type_col.in_(normalized_types)
                    conditions.append(title_type_condition)
                    filter_conditions.append(title_type_condition)

            statement = sqlalchemy.select(tb).where(sqlalchemy.and_(*conditions))
            results = self._fetchall(statement)
            results = [(x['tconst'], self._clean(self._normalize_title_data(x), ('t_soundex',)))
                       for x in results]

            # Also search the AKAs
            ta = self.T['title_akas']
            if t_soundex is not None:
                ta_conditions = [ta.c.t_soundex == t_soundex]
            else:
                ta_conditions = [ta.c.title.ilike('%%%s%%' % search_title)]
            if filter_conditions:
                ta_statement = (
                    sqlalchemy.select(ta)
                    .join(tb, ta.c.titleId == tb.c.tconst)
                    .where(sqlalchemy.and_(*(ta_conditions + filter_conditions)))
                )
            else:
                ta_statement = sqlalchemy.select(ta).where(sqlalchemy.and_(*ta_conditions))
            ta_results = self._fetchall(ta_statement)
            ta_results = [(x['titleId'], self._clean(self._rename('title_akas', dict(x)), ('t_soundex',)))
                          for x in ta_results]
            results += ta_results

            results = scan_titles(results, search_title)
            return [x[1] for x in results]

        if search_year is not None:
            results = _search(search_title, search_year)
            if results:
                return results
        return _search(search_title)

    def _search_movie_advanced(self, title=None, adult=None, results=None, sort=None,
                               sort_dir=None, title_types=None):
        return self._search_movie(title, results, adult=adult, title_types=title_types)

    def _search_episode(self, title, results):
        return self._search_movie(title, results=results, _episodes=True)

    def _search_person(self, name, results):
        name = name.strip()
        if not name:
            return []
        results = []
        ns_soundex, sn_soundex, s_soundex = name_soundexes(name)
        nb = self.T['name_basics']
        query_soundexes = [x for x in (ns_soundex, sn_soundex, s_soundex) if x]
        conditions = []
        for query_soundex in query_soundexes:
            conditions.extend([
                nb.c.ns_soundex == query_soundex,
                nb.c.sn_soundex == query_soundex,
                nb.c.s_soundex == query_soundex,
            ])
        statement = sqlalchemy.select(nb).where(sqlalchemy.or_(*conditions))
        results = self._fetchall(statement)
        results = [(x['nconst'], self._clean(self._rename('name_basics', dict(x)),
                                             ('ns_soundex', 'sn_soundex', 's_soundex')))
                   for x in results]
        results = scan_names(results, name)
        results = [x[1] for x in results]
        return results
