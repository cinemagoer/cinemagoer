# Copyright 2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Database adapters used by the dataset-backed access system."""

from pathlib import Path
from urllib.parse import unquote

from imdb._exceptions import IMDbDataAccessError, IMDbError

from ._uri import redact_uri_secrets

NO_SOUNDEX_TITLE_LIMIT = 100
SEARCH_CANDIDATE_LIMIT = 1000
SEARCH_CANDIDATE_MAX = 10000
SEARCH_CANDIDATE_MULTIPLIER = 20


def search_candidate_limit(results):
    """Return a bounded candidate pool sized for the requested results."""
    try:
        requested = max(1, int(results))
    except (TypeError, ValueError, OverflowError):
        requested = 1
    scaled = max(SEARCH_CANDIDATE_LIMIT,
                 requested * SEARCH_CANDIDATE_MULTIPLIER)
    return max(requested, min(SEARCH_CANDIDATE_MAX, scaled))


def sqlite_path_from_uri(uri):
    """Return the sqlite3 filename represented by a canonical SQLite URI."""
    if uri in ('sqlite://', 'sqlite:///:memory:'):
        return ':memory:'
    if not uri.startswith('sqlite:///'):
        raise IMDbError(
            'invalid SQLite URI %r; use sqlite:///relative.db, '
            'sqlite:////absolute/path.db, or sqlite://'
            % redact_uri_secrets(uri)
        )
    path = unquote(uri[len('sqlite:///'):])
    if not path or '?' in path or '#' in path:
        raise IMDbError(
            'invalid SQLite URI %r' % redact_uri_secrets(uri)
        )
    if path.startswith('/'):
        return path
    return str(Path(path))


def adapter_for_uri(uri):
    """Create the appropriate adapter without importing SQLAlchemy for SQLite."""
    if uri.startswith('sqlite:'):
        return SQLiteAdapter(sqlite_path_from_uri(uri))
    try:
        from .sqlalchemy_adapter import SQLAlchemyAdapter
    except ImportError as exc:
        if exc.name == 'sqlalchemy' or (exc.name or '').startswith('sqlalchemy.'):
            raise IMDbError(
                'SQLAlchemy database support requires the '
                'cinemagoer[sqlalchemy] extra and an appropriate database driver'
            ) from exc
        raise
    return SQLAlchemyAdapter(uri)


class SQLiteAdapter:
    """Query IMDb datasets using Python's standard-library sqlite3 module."""

    def __init__(self, database):
        try:
            import sqlite3
        except ImportError as exc:  # pragma: no cover - platform dependent
            raise IMDbError(
                'this Python installation does not provide SQLite support'
            ) from exc
        self._sqlite3 = sqlite3
        self.database = database
        self._database_uri = None
        self.connection = None
        try:
            if database == ':memory:':
                self.connection = self._connect()
            else:
                database_path = Path(database)
                if not database_path.is_file():
                    raise IMDbDataAccessError(
                        'SQLite database does not exist or is not a file: %r'
                        % database
                    )
                self._database_uri = '%s?mode=ro' % \
                    database_path.resolve().as_uri()
                connection = self._connect()
                connection.close()
        except IMDbDataAccessError:
            raise
        except sqlite3.Error as exc:
            raise IMDbDataAccessError(
                'unable to open SQLite database %r: %s' % (database, exc)
            ) from exc

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def _connect(self):
        if self._database_uri is None:
            connection = self._sqlite3.connect(self.database)
        else:
            connection = self._sqlite3.connect(self._database_uri, uri=True)
        connection.row_factory = self._sqlite3.Row
        return connection

    def _fetchall(self, sql, parameters=()):
        try:
            if self.connection is not None:
                rows = self.connection.execute(sql, parameters).fetchall()
            else:
                connection = self._connect()
                try:
                    rows = connection.execute(sql, parameters).fetchall()
                finally:
                    connection.close()
        except self._sqlite3.Error as exc:
            raise IMDbDataAccessError(
                'invalid or incomplete Cinemagoer SQLite database: %s' % exc
            ) from exc
        return [dict(row) for row in rows]

    def _fetchone(self, sql, parameters=()):
        rows = self._fetchall(sql, parameters)
        return rows[0] if rows else None

    def column_names(self, table):
        rows = self._fetchall('PRAGMA table_info("%s")' % table)
        return {row['name'] for row in rows}

    def _column_is_indexed(self, table, column):
        indexes = self._fetchall('PRAGMA index_list("%s")' % table)
        for index in indexes:
            index_name = index['name'].replace('"', '""')
            indexed_columns = self._fetchall(
                'PRAGMA index_info("%s")' % index_name
            )
            if any(item['name'] == column for item in indexed_columns):
                return True
        return False

    def get_row(self, table, column, value):
        return self._fetchone(
            'SELECT * FROM "%s" WHERE "%s" = ? LIMIT 1' % (table, column),
            (value,),
        )

    def get_rows(self, table, column, value):
        return self._fetchall(
            'SELECT * FROM "%s" WHERE "%s" = ?' % (table, column),
            (value,),
        )

    def episode_rows(self, parent_id):
        title_columns = [
            'tb."%s" AS "_title_%s"' % (column, column)
            for column in sorted(self.column_names('title_basics'))
        ]
        rating_columns = [
            'tr."%s" AS "_rating_%s"' % (column, column)
            for column in sorted(self.column_names('title_ratings'))
        ]
        selected = ', '.join(['te.*'] + title_columns + rating_columns)
        sql = '''SELECT %s
                   FROM title_episode AS te
              LEFT JOIN title_basics AS tb ON tb.tconst = te.tconst
              LEFT JOIN title_ratings AS tr ON tr.tconst = te.tconst
                  WHERE te.parentTconst = ?''' % selected
        return self._fetchall(sql, (parent_id,))

    def _bounded_rows(self, select, where, parameters, exact_condition,
                      exact_parameters, exact_order, limit):
        """Fetch exact rows first, then fill a fixed-size candidate pool."""
        limit = max(1, int(limit))
        if not exact_condition:
            return self._fetchall(
                '%s WHERE %s LIMIT ?' % (select, where),
                parameters + [limit],
            )

        exact_rows = self._fetchall(
            '%s WHERE %s AND %s%s LIMIT ?' % (
                select,
                where,
                exact_condition,
                ' ORDER BY %s' % exact_order if exact_order else '',
            ),
            parameters + exact_parameters + [limit],
        )
        remaining = limit - len(exact_rows)
        if remaining <= 0:
            return exact_rows
        fuzzy_rows = self._fetchall(
            '%s WHERE %s AND NOT (%s) LIMIT ?' % (
                select, where, exact_condition,
            ),
            parameters + exact_parameters + [remaining],
        )
        return exact_rows + fuzzy_rows

    def search_titles(self, soundex, search_title, year=None, episodes=False,
                      adult=None, title_types=None,
                      candidate_limit=SEARCH_CANDIDATE_LIMIT,
                      exact_titles=()):
        columns = self.column_names('title_basics')
        kind_column = None
        if 'titleType' in columns:
            kind_column = 'titleType'
        elif 'kind' in columns:
            kind_column = 'kind'
        adult_column = None
        if 'isAdult' in columns:
            adult_column = 'isAdult'
        elif 'adult' in columns:
            adult_column = 'adult'
        if soundex is None:
            conditions = [
                'tb.t_soundex IS NULL',
                'tb.primaryTitle = ?',
            ]
            parameters = [search_title]
        else:
            conditions = ['tb.t_soundex = ?']
            parameters = [soundex]
        filter_conditions = []
        filter_parameters = []
        if year is not None:
            filter_conditions.append('tb.startYear = ?')
            filter_parameters.append(year)
        if episodes and kind_column is not None:
            filter_conditions.append('tb."%s" IN (?, ?)' % kind_column)
            filter_parameters.extend(('episode', 'tvEpisode'))
        if adult is not None and adult_column is not None:
            filter_conditions.append('tb."%s" = ?' % adult_column)
            filter_parameters.append(bool(adult))
        if title_types and kind_column is not None:
            placeholders = ', '.join('?' for _ in title_types)
            filter_conditions.append(
                'tb."%s" IN (%s)' % (kind_column, placeholders)
            )
            filter_parameters.extend(title_types)
        where = ' AND '.join(conditions + filter_conditions)
        title_limit = ' LIMIT %d' % NO_SOUNDEX_TITLE_LIMIT \
            if soundex is None else ''
        if soundex is not None or \
                self._column_is_indexed('title_basics', 'primaryTitle'):
            if soundex is None:
                rows = self._fetchall(
                    'SELECT tb.* FROM title_basics AS tb WHERE ' +
                    where + title_limit,
                    parameters + filter_parameters,
                )
            else:
                exact_values = tuple(dict.fromkeys(
                    value.lower() for value in exact_titles if value
                ))
                exact_placeholders = ', '.join('?' for _ in exact_values)
                exact_condition = ''
                if exact_values:
                    exact_condition = \
                        'LOWER(tb.primaryTitle) IN (%s)' % exact_placeholders
                order = []
                if kind_column is not None:
                    order.append(
                        'CASE tb."%s" '
                        "WHEN 'movie' THEN 6 WHEN 'tv movie' THEN 5 "
                        "WHEN 'tv series' THEN 4 "
                        "WHEN 'tv mini series' THEN 4 "
                        "WHEN 'tv special' THEN 3 "
                        "WHEN 'tv short' THEN 2 "
                        "WHEN 'short' THEN 1 WHEN 'video' THEN 1 "
                        'ELSE 0 END DESC' % kind_column
                    )
                if 'startYear' in columns:
                    order.append(
                        "CASE WHEN tb.startYear IS NULL OR "
                        "tb.startYear = '' THEN 0 ELSE 1 END DESC"
                    )
                order.append('tb.tconst ASC')
                rows = self._bounded_rows(
                    'SELECT tb.* FROM title_basics AS tb',
                    where,
                    parameters + filter_parameters,
                    exact_condition,
                    list(exact_values),
                    ', '.join(order),
                    candidate_limit,
                )
        else:
            rows = []

        if soundex is None:
            aka_conditions = ['ta.t_soundex IS NULL', 'ta.title = ?']
            aka_parameters = [search_title]
        else:
            aka_conditions = ['ta.t_soundex = ?']
            aka_parameters = [soundex]
        aka_where = ' AND '.join(aka_conditions + filter_conditions)
        aka_parameters.extend(filter_parameters)
        join = ' JOIN title_basics AS tb ON ta.titleId = tb.tconst' \
            if filter_conditions else ''
        if soundex is not None or \
                self._column_is_indexed('title_akas', 'title'):
            if soundex is None:
                aka_rows = self._fetchall(
                    'SELECT ta.* FROM title_akas AS ta%s WHERE %s%s' % (
                        join, aka_where, title_limit,
                    ),
                    aka_parameters,
                )
            else:
                exact_values = tuple(dict.fromkeys(
                    value.lower() for value in exact_titles if value
                ))
                exact_placeholders = ', '.join('?' for _ in exact_values)
                exact_condition = ''
                if exact_values:
                    exact_condition = \
                        'LOWER(ta.title) IN (%s)' % exact_placeholders
                aka_columns = self.column_names('title_akas')
                order = ['ta.titleId ASC']
                if 'ordering' in aka_columns:
                    order.append('ta.ordering ASC')
                aka_rows = self._bounded_rows(
                    'SELECT ta.* FROM title_akas AS ta%s' % join,
                    aka_where,
                    aka_parameters,
                    exact_condition,
                    list(exact_values),
                    ', '.join(order),
                    candidate_limit,
                )
        else:
            aka_rows = []
        return rows, aka_rows

    def search_people(self, soundexes,
                      candidate_limit=SEARCH_CANDIDATE_LIMIT,
                      exact_names=()):
        if not soundexes:
            return []
        conditions = []
        parameters = []
        for soundex in soundexes:
            conditions.append(
                '(ns_soundex = ? OR sn_soundex = ? OR s_soundex = ?)'
            )
            parameters.extend((soundex, soundex, soundex))
        exact_values = tuple(dict.fromkeys(
            value.lower() for value in exact_names if value
        ))
        exact_placeholders = ', '.join('?' for _ in exact_values)
        exact_condition = ''
        if exact_values:
            exact_condition = \
                'LOWER(primaryName) IN (%s)' % exact_placeholders
        return self._bounded_rows(
            'SELECT * FROM name_basics',
            '(%s)' % ' OR '.join(conditions),
            parameters,
            exact_condition,
            list(exact_values),
            'nconst DESC',
            candidate_limit,
        )
