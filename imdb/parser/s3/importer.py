# Copyright 2017-2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Import IMDb's downloadable datasets into a Cinemagoer database."""

import glob
import gzip
import logging
import os

from imdb._exceptions import IMDbDataAccessError, IMDbError

from .adapters import sqlite_path_from_uri
from .utils import DB_TRANSFORM, name_soundexes, title_soundex

TSV_EXT = '.tsv.gz'
BLOCK_SIZE = 10000
logger = logging.getLogger(__name__)


def table_name_from_filename(filename):
    return os.path.basename(filename).replace(TSV_EXT, '').replace('.', '_')


def generate_content(fd, headers, table_name, block_size=BLOCK_SIZE):
    """Yield transformed blocks of rows from an open gzipped TSV stream."""
    data = []
    transforms = {
        column: conf['transform']
        for column, conf in DB_TRANSFORM.get(table_name, {}).items()
        if 'transform' in conf
    }
    for line in fd:
        values = line.decode('utf-8').strip().split('\t')
        if len(values) != len(headers):
            continue
        info = {
            header: value if value != r'\N' else None
            for header, value in zip(headers, values)
        }
        for key, transform in transforms.items():
            if key in info:
                info[key] = transform(info[key])
        if table_name == 'title_basics':
            info['t_soundex'] = title_soundex(info['primaryTitle'])
        elif table_name == 'title_akas':
            info['t_soundex'] = title_soundex(info['title'])
        elif table_name == 'name_basics':
            soundexes = name_soundexes(info['primaryName'])
            info['ns_soundex'], info['sn_soundex'], info['s_soundex'] = soundexes
        data.append(info)
        if len(data) >= block_size:
            yield data
            data = []
    if data:
        yield data


def table_definition(filename, headers):
    """Return a neutral table definition for a dataset file."""
    table_name = table_name_from_filename(filename)
    table_map = DB_TRANSFORM.get(table_name, {})
    columns = list(headers)
    columns.extend(column for column in table_map if column not in columns)
    return table_name, [
        (column, table_map.get(column, {})) for column in columns
    ]


class SQLiteImporter:
    """Native sqlite3 dataset importer."""

    _TYPES = {
        'boolean': 'INTEGER',
        'float': 'REAL',
        'integer': 'INTEGER',
        'string': 'TEXT',
        None: 'TEXT',
    }

    def __init__(self, database):
        try:
            import sqlite3
        except ImportError as exc:  # pragma: no cover - platform dependent
            raise IMDbError(
                'this Python installation does not provide SQLite support'
            ) from exc
        self.connection = sqlite3.connect(database)

    def close(self):
        self.connection.close()

    def import_file(self, filename):
        count = 0
        with gzip.GzipFile(filename, 'rb') as gz_file:
            headers = gz_file.readline().decode('utf-8').strip().split('\t')
            table_name, columns = table_definition(filename, headers)
            definitions = ', '.join(
                '"%s" %s' % (name, self._TYPES[conf.get('type')])
                for name, conf in columns
            )
            column_names = [name for name, _conf in columns]
            quoted_columns = ', '.join('"%s"' % name for name in column_names)
            placeholders = ', '.join('?' for _ in column_names)
            insert = 'INSERT INTO "%s" (%s) VALUES (%s)' % (
                table_name, quoted_columns, placeholders
            )
            with self.connection:
                self.connection.execute('DROP TABLE IF EXISTS "%s"' % table_name)
                self.connection.execute(
                    'CREATE TABLE "%s" (%s)' % (table_name, definitions)
                )
                for block in generate_content(gz_file, headers, table_name):
                    values = [
                        tuple(row.get(column) for column in column_names)
                        for row in block
                    ]
                    self.connection.executemany(insert, values)
                    count += len(block)
                for column, conf in columns:
                    if conf.get('index'):
                        index_name = 'ix_%s_%s' % (table_name, column)
                        self.connection.execute(
                            'CREATE INDEX "%s" ON "%s" ("%s")' % (
                                index_name, table_name, column
                            )
                        )
        return count


class SQLAlchemyImporter:
    """Optional dialect-neutral SQLAlchemy dataset importer."""

    def __init__(self, uri):
        try:
            import sqlalchemy
        except ImportError as exc:
            raise IMDbError(
                'this database URI requires the cinemagoer[sqlalchemy] extra '
                'and an appropriate database driver'
            ) from exc
        self.sqlalchemy = sqlalchemy
        try:
            self.engine = sqlalchemy.create_engine(uri, echo=False)
        except ModuleNotFoundError as exc:
            raise IMDbDataAccessError(
                'the database driver required by %r is not installed: %s'
                % (uri, exc)
            ) from exc
        self.metadata = sqlalchemy.MetaData()

    def close(self):
        self.engine.dispose()

    def _table(self, filename, headers):
        sa = self.sqlalchemy
        type_map = {
            'boolean': sa.Boolean,
            'float': sa.Float,
            'integer': sa.Integer,
            'string': sa.String,
            None: sa.UnicodeText,
        }
        table_name, definition = table_definition(filename, headers)
        columns = []
        indexed = []
        for name, conf in definition:
            column_type = type_map[conf.get('type')]
            if conf.get('type') == 'string' and conf.get('length'):
                column_type = column_type(length=conf['length'])
            columns.append(sa.Column(name, column_type))
            if conf.get('index'):
                indexed.append(name)
        table = sa.Table(table_name, self.metadata, *columns)
        table.info['indexed_columns'] = indexed
        return table

    def import_file(self, filename):
        count = 0
        with gzip.GzipFile(filename, 'rb') as gz_file:
            headers = gz_file.readline().decode('utf-8').strip().split('\t')
            table = self._table(filename, headers)
            with self.engine.begin() as connection:
                table.drop(bind=connection, checkfirst=True)
                table.create(bind=connection, checkfirst=True)
                for block in generate_content(gz_file, headers, table.name):
                    connection.execute(table.insert(), block)
                    count += len(block)
                for column_name in table.info['indexed_columns']:
                    index = self.sqlalchemy.Index(
                        'ix_%s_%s' % (table.name, column_name),
                        table.c[column_name],
                    )
                    index.create(connection, checkfirst=True)
        return count


def importer_for_uri(uri):
    if uri.startswith('sqlite:'):
        return SQLiteImporter(sqlite_path_from_uri(uri))
    return SQLAlchemyImporter(uri)


def import_dir(directory, uri, cleanup=False):
    """Import every ``*.tsv.gz`` file in *directory* into *uri*."""
    importer = importer_for_uri(uri)
    try:
        for filename in sorted(glob.glob(os.path.join(directory, '*' + TSV_EXT))):
            if not os.path.isfile(filename):
                continue
            logger.info('begin processing file %s', filename)
            count = importer.import_file(filename)
            logger.info('processed file %s: %d entries', filename, count)
            if cleanup:
                os.remove(filename)
    finally:
        importer.close()
