#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s32cinemagoer.py script.

This script imports the s3 dataset distributed by IMDb into a SQL database.

Copyright 2017-2018 Davide Alberani <da@mimante.net>

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

import os
import glob
import gzip
import logging
import argparse
import sqlalchemy

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from imdb.parser.s3.utils import DB_TRANSFORM, title_soundex, name_soundexes

TSV_EXT = '.tsv.gz'
# how many entries to write to the database at a time.
BLOCK_SIZE = 10000

logger = logging.getLogger()
logger.setLevel(logging.INFO)
metadata = sqlalchemy.MetaData()


def generate_content(fd, headers, table):
    """Generate blocks of rows to be written to the database.

    :param fd: a file descriptor for the .tsv.gz file
    :type fd: :class:`_io.TextIOWrapper`
    :param headers: headers in the file
    :type headers: list
    :param table: the table that will populated
    :type table: :class:`sqlalchemy.Table`
    :returns: block of data to insert
    :rtype: list
    """
    data = []
    headers_len = len(headers)
    data_transf = {}
    table_name = table.name
    soundex_key = None
    soundex_fn = None
    for column, conf in DB_TRANSFORM.get(table_name, {}).items():
        if 'transform' in conf:
            data_transf[column] = conf['transform']
    if table_name == 'title_basics':
        soundex_key = 'primaryTitle'
        soundex_fn = title_soundex
    elif table_name == 'title_akas':
        soundex_key = 'title'
        soundex_fn = title_soundex
    for line in fd:
        s_line = line.decode('utf-8').strip().split('\t')
        if len(s_line) != headers_len:
            continue
        info = {
            header: (value if value != r'\N' else None)
            for header, value in zip(headers, s_line)
        }
        for key, tranf in data_transf.items():
            if key not in info:
                continue
            info[key] = tranf(info[key])
        if soundex_fn is not None:
            info['t_soundex'] = soundex_fn(info[soundex_key])
        elif table_name == 'name_basics':
            info['ns_soundex'], info['sn_soundex'], info['s_soundex'] = name_soundexes(info['primaryName'])
        data.append(info)
        if len(data) >= BLOCK_SIZE:
            yield data
            data = []
    if data:
        yield data
        data = []


def build_table(fn, headers, create_indexes=True):
    """Build a Table object from a .tsv.gz file.

    :param fn: the .tsv.gz file
    :type fn: str
    :param headers: headers in the file
    :type headers: list
    """
    logging.debug('building table for file %s' % fn)
    table_name = fn.replace(TSV_EXT, '').replace('.', '_')
    table_map = DB_TRANSFORM.get(table_name) or {}
    columns = []
    indexed_columns = []
    all_headers = set(headers)
    all_headers.update(table_map.keys())
    for header in all_headers:
        col_info = table_map.get(header) or {}
        col_type = col_info.get('type') or sqlalchemy.UnicodeText
        if 'length' in col_info and col_type is sqlalchemy.String:
            col_type = sqlalchemy.String(length=col_info['length'])
        col_args = {
            'name': header,
            'type_': col_type,
            'index': bool(col_info.get('index', False) and create_indexes)
        }
        if col_info.get('index', False):
            indexed_columns.append(header)
        col_obj = sqlalchemy.Column(**col_args)
        columns.append(col_obj)
    table = sqlalchemy.Table(table_name, metadata, *columns)
    table.info['indexed_columns'] = indexed_columns
    return table


def create_table_indexes(connection, table):
    """Create indexes for a table after bulk loading data."""
    for column_name in table.info.get('indexed_columns', []):
        index_name = 'ix_%s_%s' % (table.name, column_name)
        index = sqlalchemy.Index(index_name, table.c[column_name])
        index.create(connection, checkfirst=True)


def import_file(fn, engine):
    """Import data from a .tsv.gz file.

    :param fn: the .tsv.gz file
    :type fn: str
    :param engine: SQLAlchemy engine
    :type engine: :class:`sqlalchemy.engine.base.Engine`
    """
    logging.info('begin processing file %s' % fn)
    count = 0
    fn_basename = os.path.basename(fn)
    with gzip.GzipFile(fn, 'rb') as gz_file:
        headers = gz_file.readline().decode('utf-8').strip().split('\t')
        logging.debug('headers of file %s: %s' % (fn, ','.join(headers)))
        table = build_table(fn_basename, headers, create_indexes=False)
        insert = table.insert()
        use_tqdm = HAS_TQDM and logger.isEnabledFor(logging.DEBUG)
        try:
            with engine.begin() as connection:
                try:
                    table.drop(bind=connection, checkfirst=True)
                    logging.debug('table %s dropped' % table.name)
                except Exception:
                    pass
                table.create(bind=connection, checkfirst=True)
                iterator = tqdm(gz_file) if use_tqdm else gz_file
                for block in generate_content(iterator, headers, table):
                    try:
                        connection.execute(insert, block)
                    except Exception as e:
                        logging.error('error processing data: %d entries lost: %s' % (len(block), e))
                        continue
                    count += len(block)
                create_table_indexes(connection, table)
        except Exception as e:
            logging.error('error processing data on table %s: %s' % (table.name, e))
        logging.info('processed file %s: %d entries' % (fn, count))


def import_dir(dir_name, engine, cleanup=False):
    """Import data from a series of .tsv.gz files.

    :param dir_name: directory containing the .tsv.gz files
    :type dir_name: str
    :param engine: SQLAlchemy engine
    :type engine: :class:`sqlalchemy.engine.base.Engine`
    """
    for fn in glob.glob(os.path.join(dir_name, '*%s' % TSV_EXT)):
        if not os.path.isfile(fn):
            logging.debug('skipping file %s' % fn)
            continue
        import_file(fn, engine)
        if cleanup:
            logging.debug('Removing file %s' % fn)
            os.remove(fn)

 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tsv_files_dir')
    parser.add_argument('db_uri')
    parser.add_argument('--verbose', help='increase verbosity and show progress', action='store_true')
    parser.add_argument('--cleanup', help='Remove files after they\'re imported', action='store_true')
    args = parser.parse_args()
    dir_name = args.tsv_files_dir
    db_uri = args.db_uri
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    cleanup = args.cleanup
    engine = sqlalchemy.create_engine(db_uri, echo=False)
    metadata.bind = engine
    import_dir(dir_name, engine, cleanup)

