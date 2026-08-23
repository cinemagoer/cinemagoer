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

from imdb import IMDbBase
from imdb._exceptions import IMDbError
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import analyze_title

from .adapters import adapter_for_uri
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


def split_characters(text):
    """Return one role name or an ordered list of role names."""
    if not isinstance(text, str) or ' / ' not in text:
        return text
    return text.split(' / ')


def _normalize_imdb_id(value, prefix, label):
    """Return a canonical public IMDb ID for an S3 movie or person."""
    original_value = value
    if isinstance(value, str):
        value = value.strip()
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
    elif isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    else:
        raise IMDbError(
            'invalid %s IMDb id %r; expected digits or an optional %s prefix'
            % (label, original_value, prefix)
        )
    if not value.isdigit():
        raise IMDbError(
            'invalid %s IMDb id %r; expected digits or an optional %s prefix'
            % (label, original_value, prefix)
        )
    return str(int(value)).zfill(7)


class IMDbS3AccessSystem(IMDbBase):
    """The class used to access IMDb's data through the s3 dataset."""

    accessSystem = 's3'

    _KIND_REV = {v: k for k, v in KIND.items()}

    def get_movie_infoset(self):
        return ['main', 'plot', 'episodes']

    def get_person_infoset(self):
        return ['main', 'filmography', 'biography']
    _s3_logger = logging.getLogger('imdbpy.parser.s3')

    def _normalize_movieID(self, movieID):
        return _normalize_imdb_id(movieID, 'tt', 'movie')

    def _normalize_personID(self, personID):
        return _normalize_imdb_id(personID, 'nm', 'person')

    def _get_real_movieID(self, movieID):
        return self._normalize_movieID(movieID)

    def _get_real_personID(self, personID):
        return self._normalize_personID(personID)

    def __init__(self, uri='sqlite:///cinemagoer.db', adultSearch=True,
                 *arguments, **keywords):
        """Initialize the access system."""
        IMDbBase.__init__(self, *arguments, **keywords)
        self._adult_search = bool(adultSearch)
        self._adapter = adapter_for_uri(uri)

    def close(self):
        """Close database resources held by this access system."""
        adapter = getattr(self, '_adapter', None)
        if adapter is None:
            return
        self._adapter = None
        adapter.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

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

    def _base_title_info(self, movieID, movies_cache=None, persons_cache=None):
        if movies_cache is None:
            movies_cache = {}
        if persons_cache is None:
            persons_cache = {}
        if movieID in movies_cache:
            return movies_cache[movieID]
        movie = self._adapter.get_row('title_basics', 'tconst', movieID) or {}
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
        person = self._adapter.get_row('name_basics', 'nconst', personID) or {}
        data = self._rename('name_basics', person)
        movies = []
        for movieID in split_array(data.get('known for') or ''):
            if not movieID:
                continue
            movieID = int(movieID)
            movie_data = self._base_title_info(movieID, movies_cache=movies_cache, persons_cache=persons_cache)
            movie = Movie(
                movieID=self._normalize_movieID(movieID),
                data=movie_data,
                accessSystem=self.accessSystem,
            )
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

        movie = self._adapter.get_row('title_crew', 'tconst', movieID) or {}
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
                person = Person(
                    personID=self._normalize_personID(personID),
                    data=person_data,
                    accessSystem=self.accessSystem,
                )
                target.append(person)
        tc_data['director'] = directors
        tc_data['writer'] = writers
        data.update(tc_data)

        movie = self._adapter.get_row('title_episode', 'tconst', movieID) or {}
        te_data = self._rename('title_episode', movie)
        if 'parentTconst' in te_data:
            parent_id = te_data['parentTconst']
            parent_data = self._base_title_info(parent_id)
            te_data['episode of'] = Movie(
                movieID=self._normalize_movieID(parent_id),
                data=parent_data,
                accessSystem=self.accessSystem,
            )
        self._clean(te_data, ('parentTconst',))
        data.update(te_data)

        movie_rows = self._adapter.get_rows(
            'title_principals', 'tconst', movieID
        )
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
                person = Person(personID=self._normalize_personID(personID),
                                data=person_data,
                                billingPos=person_info.get('ordering'),
                                currentRole=split_characters(
                                    person_info.get('characters')
                                ),
                                notes=person_info.get('job'),
                                accessSystem=self.accessSystem)
                persons.append(person)
            data[role] = persons

        movie = self._adapter.get_row('title_ratings', 'tconst', movieID) or {}
        tr_data = self._rename('title_ratings', movie)
        data.update(tr_data)

        akas = self._adapter.get_rows('title_akas', 'titleId', movieID)
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

        episode_rows = self._adapter.episode_rows(movieID)
        if not episode_rows:
            return {
                'data': {'episodes': {}, 'number of episodes': 0},
                'info sets': ['episodes'],
            }

        parent_data = self._base_title_info(movieID)
        parent = Movie(
            movieID=self._normalize_movieID(movieID),
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
                key[len('_title_'):]: value
                for key, value in row.items()
                if key.startswith('_title_')
            }
            data = self._normalize_title_data(title_data)
            rating_data = {
                key[len('_rating_'):]: value
                for key, value in row.items()
                if key.startswith('_rating_')
            }
            rating_data = self._rename('title_ratings', rating_data)
            data.update(self._clean(rating_data, ('movieID',)))
            episode_data = {
                key: value for key, value in row.items()
                if not key.startswith(('_title_', '_rating_'))
            }
            episode_data = self._rename('title_episode', episode_data)
            self._clean(episode_data, ('movieID', 'parentTconst'))
            data.update(episode_data)
            data['episode of'] = parent
            episode = Movie(
                movieID=self._normalize_movieID(episode_id),
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

        if adult is None and not self._adult_search:
            adult = False

        title_info = analyze_title(title)
        search_title = title_info.get('title', title).strip()
        search_year = title_info.get('year')
        search_title_types = title_types

        def _search(search_title, search_year=None):
            t_soundex = title_soundex(search_title)
            normalized_types = None
            if search_title_types:
                if isinstance(search_title_types, str):
                    normalized_title_types = [search_title_types]
                else:
                    normalized_title_types = list(search_title_types)
                normalized_types = []
                for t in normalized_title_types:
                    # Current imports store transformed public kinds, while
                    # older databases may retain raw IMDb dataset values.
                    # Accept either spelling against both schema variants.
                    for candidate in (
                        t,
                        KIND.get(t, t),
                        self._KIND_REV.get(t, t),
                    ):
                        if candidate not in normalized_types:
                            normalized_types.append(candidate)

            results, ta_results = self._adapter.search_titles(
                t_soundex,
                search_title,
                year=search_year,
                episodes=_episodes,
                adult=adult,
                title_types=normalized_types,
            )
            results = [(x['tconst'], self._clean(self._normalize_title_data(x), ('t_soundex',)))
                       for x in results]

            # Also search the AKAs
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
        if sort is not None or sort_dir is not None:
            raise IMDbError(
                'sort and sort_dir are not supported by the s3 access system; '
                'omit both arguments to use relevance ranking'
            )
        return self._search_movie(title, results, adult=adult, title_types=title_types)

    def _search_episode(self, title, results):
        return self._search_movie(title, results=results, _episodes=True)

    def _search_person(self, name, results):
        name = name.strip()
        if not name:
            return []
        ns_soundex, sn_soundex, s_soundex = name_soundexes(name)
        query_soundexes = [x for x in (ns_soundex, sn_soundex, s_soundex) if x]
        if not query_soundexes:
            return []
        results = self._adapter.search_people(query_soundexes)
        results = [(x['nconst'], self._clean(self._rename('name_basics', dict(x)),
                                             ('ns_soundex', 'sn_soundex', 's_soundex')))
                   for x in results]
        results = scan_names(results, name)
        results = [x[1] for x in results]
        return results
