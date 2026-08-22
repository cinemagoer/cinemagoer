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


class SQLAlchemyAdapter:
    """Dialect-neutral query adapter backed by SQLAlchemy."""

    def __init__(self, uri):
        try:
            url = sqlalchemy.engine.make_url(uri)
        except sqlalchemy.exc.ArgumentError as exc:
            raise IMDbDataAccessError(
                'invalid SQLAlchemy database URI %r: %s' % (uri, exc)
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
                % (uri, exc)
            ) from exc
        if sqlite_path is not None:
            @sqlalchemy.event.listens_for(self.engine, 'connect')
            def _set_query_only(dbapi_connection, _connection_record):
                dbapi_connection.execute('PRAGMA query_only = ON')
        self.metadata = sqlalchemy.MetaData()
        try:
            self.metadata.reflect(bind=self.engine)
        except sqlalchemy.exc.SQLAlchemyError as exc:
            self.engine.dispose()
            raise IMDbDataAccessError(
                'unable to inspect database %r: %s' % (uri, exc)
            ) from exc
        self.tables = self.metadata.tables

    def close(self):
        self.engine.dispose()

    def _fetchone(self, statement):
        with self.engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return dict(row) if row else None

    def _fetchall(self, statement):
        with self.engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [dict(row) for row in rows]

    def column_names(self, table):
        return set(self.tables[table].c.keys())

    def get_row(self, table, column, value):
        table_obj = self.tables[table]
        return self._fetchone(
            sqlalchemy.select(table_obj).where(table_obj.c[column] == value)
        )

    def get_rows(self, table, column, value):
        table_obj = self.tables[table]
        return self._fetchall(
            sqlalchemy.select(table_obj).where(table_obj.c[column] == value)
        )

    def episode_rows(self, parent_id):
        te = self.tables['title_episode']
        tb = self.tables['title_basics']
        tr = self.tables['title_ratings']
        title_columns = [
            column.label('_title_%s' % column.name) for column in tb.c
        ]
        rating_columns = [
            column.label('_rating_%s' % column.name) for column in tr.c
        ]
        return self._fetchall(
            sqlalchemy.select(*te.c, *title_columns, *rating_columns)
            .select_from(te)
            .outerjoin(tb, tb.c.tconst == te.c.tconst)
            .outerjoin(tr, tr.c.tconst == te.c.tconst)
            .where(te.c.parentTconst == parent_id)
        )

    def search_titles(self, soundex, search_title, year=None, episodes=False,
                      adult=None, title_types=None):
        tb = self.tables['title_basics']
        conditions = [tb.c.t_soundex == soundex]
        filters = []
        if year is not None:
            filters.append(tb.c.startYear == year)
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
        title_rows = self._fetchall(
            sqlalchemy.select(tb).where(sqlalchemy.and_(*(conditions + filters)))
        )

        ta = self.tables['title_akas']
        aka_conditions = [
            ta.c.t_soundex == soundex if soundex is not None
            else ta.c.title.ilike('%%%s%%' % search_title)
        ]
        statement = sqlalchemy.select(ta)
        if filters:
            statement = statement.join(tb, ta.c.titleId == tb.c.tconst)
        aka_rows = self._fetchall(
            statement.where(sqlalchemy.and_(*(aka_conditions + filters)))
        )
        return title_rows, aka_rows

    def search_people(self, soundexes):
        nb = self.tables['name_basics']
        conditions = []
        for soundex in soundexes:
            conditions.extend((
                nb.c.ns_soundex == soundex,
                nb.c.sn_soundex == soundex,
                nb.c.s_soundex == soundex,
            ))
        return self._fetchall(
            sqlalchemy.select(nb).where(sqlalchemy.or_(*conditions))
        )
