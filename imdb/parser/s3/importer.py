# Copyright 2017-2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Import IMDb's downloadable datasets into a Cinemagoer database."""

import gzip
import json
import logging
import os
import tempfile

from imdb._exceptions import IMDbDataAccessError, IMDbError
from imdb.version import __version__

from .adapters import sqlite_path_from_uri
from .utils import DB_TRANSFORM, name_soundexes, title_soundex

TSV_EXT = '.tsv.gz'
BLOCK_SIZE = 10000
MANIFEST_FILENAME = 'cinemagoer-import-manifest.json'
DATASET_HEADERS = {
    'name.basics.tsv.gz': (
        'nconst', 'primaryName', 'birthYear', 'deathYear',
        'primaryProfession', 'knownForTitles',
    ),
    'title.akas.tsv.gz': (
        'titleId', 'ordering', 'title', 'region', 'language', 'types',
        'attributes', 'isOriginalTitle',
    ),
    'title.basics.tsv.gz': (
        'tconst', 'titleType', 'primaryTitle', 'originalTitle', 'isAdult',
        'startYear', 'endYear', 'runtimeMinutes', 'genres',
    ),
    'title.crew.tsv.gz': ('tconst', 'directors', 'writers'),
    'title.episode.tsv.gz': (
        'tconst', 'parentTconst', 'seasonNumber', 'episodeNumber',
    ),
    'title.principals.tsv.gz': (
        'tconst', 'ordering', 'nconst', 'category', 'job', 'characters',
    ),
    'title.ratings.tsv.gz': ('tconst', 'averageRating', 'numVotes'),
}
logger = logging.getLogger(__name__)


def table_name_from_filename(filename):
    return os.path.basename(filename).replace(TSV_EXT, '').replace('.', '_')


def _dataset_error(filename, line_number, message):
    location = '%s:%d' % (filename, line_number)
    return IMDbDataAccessError('%s: %s' % (location, message))


def _read_headers(fd, filename):
    try:
        header_line = fd.readline()
        if not header_line:
            raise _dataset_error(filename, 1, 'missing header row')
        headers = header_line.decode('utf-8').rstrip('\r\n').split('\t')
    except UnicodeDecodeError as exc:
        raise _dataset_error(filename, 1, 'header is not valid UTF-8') from exc
    expected = DATASET_HEADERS[os.path.basename(filename)]
    if tuple(headers) != expected:
        raise _dataset_error(
            filename,
            1,
            'unsupported header; expected %s' % '\t'.join(expected),
        )
    return headers


def generate_content(fd, headers, table_name, block_size=BLOCK_SIZE,
                     filename='<dataset>'):
    """Yield transformed blocks of rows from an open gzipped TSV stream."""
    data = []
    transforms = {
        column: conf['transform']
        for column, conf in DB_TRANSFORM.get(table_name, {}).items()
        if 'transform' in conf
    }
    for line_number, line in enumerate(fd, start=2):
        try:
            values = line.decode('utf-8').rstrip('\r\n').split('\t')
        except UnicodeDecodeError as exc:
            raise _dataset_error(
                filename, line_number, 'row is not valid UTF-8'
            ) from exc
        if len(values) != len(headers):
            raise _dataset_error(
                filename,
                line_number,
                'expected %d fields, found %d' % (len(headers), len(values)),
            )
        info = {
            header: value if value != r'\N' else None
            for header, value in zip(headers, values)
        }
        try:
            for key, transform in transforms.items():
                if key in info:
                    info[key] = transform(info[key])
            if table_name == 'title_basics':
                info['t_soundex'] = title_soundex(info['primaryTitle'])
            elif table_name == 'title_akas':
                info['t_soundex'] = title_soundex(info['title'])
            elif table_name == 'name_basics':
                soundexes = name_soundexes(info['primaryName'])
                info['ns_soundex'], info['sn_soundex'], info['s_soundex'] = \
                    soundexes
        except IMDbError:
            raise
        except Exception as exc:
            raise _dataset_error(
                filename, line_number, 'invalid field value: %s' % exc
            ) from exc
        data.append(info)
        if len(data) >= block_size:
            yield data
            data = []
    if data:
        yield data


def _preflight_file(filename):
    """Validate one complete archive and return its source metadata."""
    row_count = 0
    try:
        with gzip.GzipFile(filename, 'rb') as gz_file:
            headers = _read_headers(gz_file, filename)
            table_name = table_name_from_filename(filename)
            for block in generate_content(
                    gz_file, headers, table_name, filename=filename):
                row_count += len(block)
    except IMDbError:
        raise
    except (EOFError, OSError) as exc:
        raise IMDbDataAccessError(
            '%s: unreadable gzip archive: %s' % (filename, exc)
        ) from exc
    if not row_count:
        raise IMDbDataAccessError('%s: dataset contains no rows' % filename)
    return {
        'filename': os.path.basename(filename),
        'size': os.path.getsize(filename),
        'source_rows': row_count,
        'imported_rows': None,
    }


def preflight_directory(directory):
    """Validate the complete supported dataset without opening a database."""
    if not os.path.isdir(directory):
        raise IMDbDataAccessError(
            'dataset directory does not exist or is not a directory: %r'
            % directory
        )
    try:
        filenames = sorted(
            os.path.join(directory, name)
            for name in os.listdir(directory)
            if name.endswith(TSV_EXT)
        )
    except OSError as exc:
        raise IMDbDataAccessError(
            'unable to read dataset directory %r: %s' % (directory, exc)
        ) from exc
    if not filenames:
        raise IMDbDataAccessError(
            'dataset directory contains no %s files: %r'
            % (TSV_EXT, directory)
        )
    basenames = {os.path.basename(filename) for filename in filenames}
    unsupported = sorted(basenames.difference(DATASET_HEADERS))
    if unsupported:
        raise IMDbDataAccessError(
            'unsupported dataset archive(s): %s' % ', '.join(unsupported)
        )
    missing = sorted(set(DATASET_HEADERS).difference(basenames))
    if missing:
        raise IMDbDataAccessError(
            'missing required dataset archive(s): %s' % ', '.join(missing)
        )
    for filename in filenames:
        if not os.path.isfile(filename):
            raise IMDbDataAccessError(
                'dataset archive is not a regular file: %r' % filename
            )
    return filenames, [_preflight_file(filename) for filename in filenames]


def validate_destination_uri(uri):
    """Reject invalid and ephemeral importer destinations."""
    if not isinstance(uri, str) or '://' not in uri:
        raise IMDbError('invalid database URI %r' % uri)
    if uri.startswith('sqlite:'):
        database = sqlite_path_from_uri(uri)
        if database == ':memory:':
            raise IMDbError(
                'the importer requires a persistent database; '
                'in-memory SQLite URI %r is not supported' % uri
            )
    elif uri.startswith('sqlite+'):
        location = uri.partition('://')[2].partition('?')[0]
        if location in ('', '/', '/:memory:') or ':memory:' in location or \
                'mode=memory' in uri:
            raise IMDbError(
                'the importer requires a persistent database; '
                'in-memory SQLite URI %r is not supported' % uri
            )


def _write_manifest(directory, manifest):
    manifest_path = os.path.join(directory, MANIFEST_FILENAME)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=directory,
                prefix='.%s.' % MANIFEST_FILENAME, delete=False) as stream:
            temporary = stream.name
            json.dump(manifest, stream, indent=2, sort_keys=True)
            stream.write('\n')
        os.replace(temporary, manifest_path)
    except OSError as exc:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        raise IMDbDataAccessError(
            'unable to write import manifest %r: %s' % (manifest_path, exc)
        ) from exc
    return manifest_path


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
        try:
            self.connection = sqlite3.connect(database)
        except sqlite3.Error as exc:
            raise IMDbDataAccessError(
                'unable to open SQLite database %r: %s' % (database, exc)
            ) from exc

    def check_connection(self):
        self.connection.execute('SELECT 1')

    def begin(self):
        self.connection.execute('BEGIN')

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()

    def import_file(self, filename):
        count = 0
        with gzip.GzipFile(filename, 'rb') as gz_file:
            headers = _read_headers(gz_file, filename)
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
            self.connection.execute('DROP TABLE IF EXISTS "%s"' % table_name)
            self.connection.execute(
                'CREATE TABLE "%s" (%s)' % (table_name, definitions)
            )
            for block in generate_content(
                    gz_file, headers, table_name, filename=filename):
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
        self.connection = None
        self.transaction = None

    def check_connection(self):
        try:
            with self.engine.connect() as connection:
                connection.execute(self.sqlalchemy.text('SELECT 1'))
        except self.sqlalchemy.exc.SQLAlchemyError as exc:
            raise IMDbDataAccessError(
                'unable to connect to database: %s' % exc
            ) from exc

    def begin(self):
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        if self.engine.dialect.name == 'sqlite':
            # The sqlite3 driver otherwise uses legacy transaction control,
            # where DDL can auto-commit before the first data-changing DML.
            self.connection.exec_driver_sql('BEGIN')

    def commit(self):
        self.transaction.commit()
        self.transaction = None

    def rollback(self):
        if self.transaction is not None:
            self.transaction.rollback()
            self.transaction = None

    def _close_connection(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def close(self):
        self._close_connection()
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
            headers = _read_headers(gz_file, filename)
            table = self._table(filename, headers)
            connection = self.connection
            table.drop(bind=connection, checkfirst=True)
            table.create(bind=connection, checkfirst=True)
            for block in generate_content(
                    gz_file, headers, table.name, filename=filename):
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
    """Preflight and import a complete IMDb dataset into *uri*."""
    validate_destination_uri(uri)
    filenames, file_metadata = preflight_directory(directory)
    manifest = {
        'cinemagoer_version': __version__,
        'cleanup_requested': bool(cleanup),
        'files': file_metadata,
        'removed_files': [],
        'status': 'preflight-complete',
    }
    manifest_path = _write_manifest(directory, manifest)
    importer = None
    try:
        importer = importer_for_uri(uri)
        importer.check_connection()
        importer.begin()
        metadata_by_name = {
            item['filename']: item for item in manifest['files']
        }
        for filename in filenames:
            logger.info('begin processing file %s', filename)
            count = importer.import_file(filename)
            metadata = metadata_by_name[os.path.basename(filename)]
            metadata['imported_rows'] = count
            if count != metadata['source_rows']:
                raise IMDbDataAccessError(
                    '%s: imported %d of %d preflighted rows'
                    % (filename, count, metadata['source_rows'])
                )
            logger.info('processed file %s: %d entries', filename, count)
        importer.commit()
    except Exception as exc:
        if importer is not None:
            try:
                importer.rollback()
            except Exception:
                logger.exception('unable to roll back failed import')
        manifest['status'] = 'failed'
        manifest['failure_type'] = type(exc).__name__
        try:
            _write_manifest(directory, manifest)
        except IMDbError:
            logger.exception('unable to update failed import manifest')
        raise
    finally:
        if importer is not None:
            importer.close()

    if cleanup:
        try:
            for filename in filenames:
                os.remove(filename)
                manifest['removed_files'].append(os.path.basename(filename))
                logger.info('removed source archive %s', filename)
        except OSError as exc:
            manifest['status'] = 'database-complete-cleanup-failed'
            manifest['failure_type'] = type(exc).__name__
            _write_manifest(directory, manifest)
            raise IMDbDataAccessError(
                'database import completed, but cleanup failed for %r: %s'
                % (filename, exc)
            ) from exc

    manifest['status'] = 'completed'
    _write_manifest(directory, manifest)
    logger.info('completed import manifest %s', manifest_path)
    return manifest
