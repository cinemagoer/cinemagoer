# Copyright 2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Optional SQLAlchemy adapter for non-native database dialects."""

from pathlib import Path

import sqlalchemy

from imdb._exceptions import IMDbDataAccessError

from ._uri import redact_uri_secrets
from .adapters import NO_SOUNDEX_TITLE_LIMIT, SEARCH_CANDIDATE_LIMIT


class SQLAlchemyAdapter:
    """Dialect-neutral query adapter backed by SQLAlchemy."""

    def __init__(self, uri):
        self._display_uri = redact_uri_secrets(uri)
        try:
            url = sqlalchemy.engine.make_url(uri)
        except sqlalchemy.exc.ArgumentError as exc:
            raise IMDbDataAccessError(
                'invalid SQLAlchemy database URI %r: %s'
                % (self._display_uri, redact_uri_secrets(exc))
            ) from exc
        sqlite_path = None
        engine_uri = uri
        if url.get_backend_name() == 'sqlite' and \
                url.database not in (None, '', ':memory:'):
            sqlite_path = Path(url.database)
            if not sqlite_path.is_file():
                raise IMDbDataAccessError(
                    'SQLite database does not exist or is not a file: %r'
                    % url.database
                )
            query = dict(url.query)
            query.update({'mode': 'ro', 'uri': 'true'})
            engine_uri = url.set(
                database='file:%s' % sqlite_path.resolve().as_posix(),
                query=query,
            )
        try:
            self.engine = sqlalchemy.create_engine(engine_uri, echo=False)
        except ModuleNotFoundError as exc:
            raise IMDbDataAccessError(
                'the database driver required by %r is not installed: %s'
                % (self._display_uri, redact_uri_secrets(exc))
            ) from exc
        except sqlalchemy.exc.SQLAlchemyError as exc:
            raise IMDbDataAccessError(
                'unable to configure database %r: %s'
                % (self._display_uri, redact_uri_secrets(exc))
            ) from exc
        if sqlite_path is not None:
            @sqlalchemy.event.listens_for(self.engine, 'connect')
            def _set_query_only(dbapi_connection, _connection_record):
                dbapi_connection.execute('PRAGMA query_only = ON')
        self.metadata = sqlalchemy.MetaData()
        self.tables = self.metadata.tables

    def close(self):
        self.engine.dispose()

    def _fetchone(self, statement):
        try:
            with self.engine.connect() as connection:
                row = connection.execute(statement).mappings().first()
        except sqlalchemy.exc.SQLAlchemyError as exc:
            raise self._database_error('query', exc) from exc
        return dict(row) if row else None

    def _fetchall(self, statement):
        try:
            with self.engine.connect() as connection:
                rows = connection.execute(statement).mappings().all()
        except sqlalchemy.exc.SQLAlchemyError as exc:
            raise self._database_error('query', exc) from exc
        return [dict(row) for row in rows]

    def _database_error(self, operation, exc):
        return IMDbDataAccessError(
            'unable to %s database %r: %s'
            % (operation, self._display_uri, redact_uri_secrets(exc))
        )

    def _table(self, name):
        table = self.tables.get(name)
        if table is not None:
            return table
        try:
            return sqlalchemy.Table(
                name, self.metadata, autoload_with=self.engine
            )
        except sqlalchemy.exc.NoSuchTableError as exc:
            raise IMDbDataAccessError(
                'invalid or incomplete Cinemagoer database %r: '
                'missing table %r' % (self._display_uri, name)
            ) from exc
        except sqlalchemy.exc.SQLAlchemyError as exc:
            raise self._database_error('inspect', exc) from exc

    def _column(self, table, name):
        try:
            return table.c[name]
        except KeyError as exc:
            raise IMDbDataAccessError(
                'invalid or incomplete Cinemagoer database %r: '
                'missing column %r in table %r'
                % (self._display_uri, name, table.name)
            ) from exc

    def column_names(self, table):
        return set(self._table(table).c.keys())

    def _column_is_indexed(self, table, column):
        return any(
            indexed_column.name == column
            for index in self._table(table).indexes
            for indexed_column in index.columns
        )

    def get_row(self, table, column, value):
        table_obj = self._table(table)
        return self._fetchone(
            sqlalchemy.select(table_obj).where(
                self._column(table_obj, column) == value
            )
        )

    def get_rows(self, table, column, value):
        table_obj = self._table(table)
        return self._fetchall(
            sqlalchemy.select(table_obj).where(
                self._column(table_obj, column) == value
            )
        )

    def episode_rows(self, parent_id):
        te = self._table('title_episode')
        tb = self._table('title_basics')
        tr = self._table('title_ratings')
        title_columns = [
            column.label('_title_%s' % column.name) for column in tb.c
        ]
        rating_columns = [
            column.label('_rating_%s' % column.name) for column in tr.c
        ]
        tb_tconst = self._column(tb, 'tconst')
        te_tconst = self._column(te, 'tconst')
        tr_tconst = self._column(tr, 'tconst')
        return self._fetchall(
            sqlalchemy.select(*te.c, *title_columns, *rating_columns)
            .select_from(te)
            .outerjoin(tb, tb_tconst == te_tconst)
            .outerjoin(tr, tr_tconst == te_tconst)
            .where(self._column(te, 'parentTconst') == parent_id)
        )

    def _bounded_rows(self, statement, exact_condition, exact_order, limit):
        """Fetch exact rows first, then fill a fixed-size candidate pool."""
        limit = max(1, int(limit))
        if exact_condition is None:
            return self._fetchall(statement.limit(limit))
        exact_rows = self._fetchall(
            statement.where(exact_condition).order_by(*exact_order).limit(limit)
        )
        remaining = limit - len(exact_rows)
        if remaining <= 0:
            return exact_rows
        fuzzy_rows = self._fetchall(
            statement.where(sqlalchemy.not_(exact_condition)).limit(remaining)
        )
        return exact_rows + fuzzy_rows

    def search_titles(self, soundex, search_title, year=None, episodes=False,
                      adult=None, title_types=None,
                      candidate_limit=SEARCH_CANDIDATE_LIMIT,
                      exact_titles=()):
        tb = self._table('title_basics')
        title_soundex = self._column(tb, 't_soundex')
        if soundex is None:
            conditions = [
                title_soundex.is_(None),
                self._column(tb, 'primaryTitle') == search_title,
            ]
        else:
            conditions = [title_soundex == soundex]
        filters = []
        if year is not None:
            filters.append(self._column(tb, 'startYear') == year)
        kind_column = tb.c.get('titleType')
        if kind_column is None:
            kind_column = tb.c.get('kind')
        if episodes and kind_column is not None:
            filters.append(kind_column.in_(('episode', 'tvEpisode')))
        adult_column = tb.c.get('isAdult')
        if adult_column is None:
            adult_column = tb.c.get('adult')
        if adult is not None and adult_column is not None:
            filters.append(adult_column == bool(adult))
        if title_types and kind_column is not None:
            filters.append(kind_column.in_(title_types))
        title_statement = sqlalchemy.select(tb).where(
            sqlalchemy.and_(*(conditions + filters))
        )
        if soundex is None:
            title_statement = title_statement.limit(NO_SOUNDEX_TITLE_LIMIT)
        if soundex is not None or \
                self._column_is_indexed('title_basics', 'primaryTitle'):
            if soundex is None:
                title_rows = self._fetchall(title_statement)
            else:
                exact_values = tuple(dict.fromkeys(
                    value.lower() for value in exact_titles if value
                ))
                exact_condition = None
                if exact_values:
                    exact_condition = sqlalchemy.func.lower(
                        self._column(tb, 'primaryTitle')
                    ).in_(exact_values)
                exact_order = []
                if kind_column is not None:
                    exact_order.append(sqlalchemy.case(
                        {
                            'movie': 6,
                            'tv movie': 5,
                            'tv series': 4,
                            'tv mini series': 4,
                            'tv special': 3,
                            'tv short': 2,
                            'short': 1,
                            'video': 1,
                        },
                        value=kind_column,
                        else_=0,
                    ).desc())
                year_column = tb.c.get('startYear')
                if year_column is not None:
                    exact_order.append(sqlalchemy.case(
                        (year_column.is_(None), 0),
                        else_=1,
                    ).desc())
                exact_order.append(self._column(tb, 'tconst').asc())
                title_rows = self._bounded_rows(
                    title_statement,
                    exact_condition,
                    exact_order,
                    candidate_limit,
                )
        else:
            title_rows = []

        ta = self._table('title_akas')
        aka_soundex = self._column(ta, 't_soundex')
        if soundex is None:
            aka_conditions = [
                aka_soundex.is_(None),
                self._column(ta, 'title') == search_title,
            ]
        else:
            aka_conditions = [aka_soundex == soundex]
        statement = sqlalchemy.select(ta)
        if filters:
            statement = statement.join(
                tb,
                self._column(ta, 'titleId') == self._column(tb, 'tconst'),
            )
        statement = statement.where(
            sqlalchemy.and_(*(aka_conditions + filters))
        )
        if soundex is None:
            statement = statement.limit(NO_SOUNDEX_TITLE_LIMIT)
        if soundex is not None or \
                self._column_is_indexed('title_akas', 'title'):
            if soundex is None:
                aka_rows = self._fetchall(statement)
            else:
                exact_values = tuple(dict.fromkeys(
                    value.lower() for value in exact_titles if value
                ))
                exact_condition = None
                if exact_values:
                    exact_condition = sqlalchemy.func.lower(
                        self._column(ta, 'title')
                    ).in_(exact_values)
                exact_order = [self._column(ta, 'titleId').asc()]
                ordering_column = ta.c.get('ordering')
                if ordering_column is not None:
                    exact_order.append(ordering_column.asc())
                aka_rows = self._bounded_rows(
                    statement,
                    exact_condition,
                    exact_order,
                    candidate_limit,
                )
        else:
            aka_rows = []
        return title_rows, aka_rows

    def search_people(self, soundexes,
                      candidate_limit=SEARCH_CANDIDATE_LIMIT,
                      exact_names=()):
        if not soundexes:
            return []
        nb = self._table('name_basics')
        conditions = []
        for soundex in soundexes:
            conditions.extend((
                self._column(nb, 'ns_soundex') == soundex,
                self._column(nb, 'sn_soundex') == soundex,
                self._column(nb, 's_soundex') == soundex,
            ))
        statement = sqlalchemy.select(nb).where(sqlalchemy.or_(*conditions))
        exact_values = tuple(dict.fromkeys(
            value.lower() for value in exact_names if value
        ))
        exact_condition = None
        if exact_values:
            exact_condition = sqlalchemy.func.lower(
                self._column(nb, 'primaryName')
            ).in_(exact_values)
        return self._bounded_rows(
            statement,
            exact_condition,
            [self._column(nb, 'nconst').desc()],
            candidate_limit,
        )
