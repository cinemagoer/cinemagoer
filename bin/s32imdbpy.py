#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import glob
import gzip
import sqlalchemy

BLOCK_SIZE = 10000

metadata = sqlalchemy.MetaData()

re_imdbids = re.compile(r'(nm|tt)')


def transf_imdbid(x):
    return int(x[2:])

def transf_multi_imdbid(x):
    return re_imdbids.sub('', x)


def transf_int(x):
    try:
        return int(x)
    except:
        return None


def transf_float(x):
    try:
        return float(x)
    except:
        return None


def transf_bool(x):
    try:
        return bool(x)
    except:
        return None


DB_TRANSFORM = {
    'title_basics': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'isAdult': {'type': sqlalchemy.Boolean, 'transform': transf_bool},
        'startYear': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'endYear': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'runtimeMinutes': {'type': sqlalchemy.Integer, 'transform': transf_int}
    },
    'name_basics': {
        'nconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'birthYear': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'deathYear': {'type': sqlalchemy.Integer, 'transform': transf_int}
    },
    'title_crew': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'directors': {'transform': transf_multi_imdbid},
        'writers': {'transform': transf_multi_imdbid}
    },
    'title_episode': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'parentTconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'seasonNumber': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'episodeNumber': {'type': sqlalchemy.Integer, 'transform': transf_int}
    },
    'title_principals': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'principlaCast': {'transform': transf_multi_imdbid}
    },
    'title_ratings': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'averageRating': {'type': sqlalchemy.Float, 'transform': transf_float},
        'numVotes': {'type': sqlalchemy.Integer, 'transform': transf_int}
    },

}

def generate_content(fd, headers, table):
    data = []
    headers_len = len(headers)
    data_transf = {}
    for column, conf in DB_TRANSFORM.get(table.name, {}).items():
        if 'transform' in conf:
            data_transf[column] = conf['transform']
    for line in fd:
        s_line = line.decode('utf-8').strip().split('\t')
        if len(s_line) != headers_len:
            continue
        info = dict(zip(headers, s_line))
        for key, tranf in data_transf.items():
            if key not in info:
                continue
            info[key] = tranf(info[key])
        data.append(info)
        if len(data) >= BLOCK_SIZE:
            yield data
            data = []
    if data:
        yield data
        data = []


def build_table(fn, headers):
    table_name = fn.replace('.tsv.gz', '').replace('.', '_')
    table_map = DB_TRANSFORM.get(table_name) or {}
    columns = []
    for header in headers:
        col_info = table_map.get(header) or {}
        col_type = col_info.get('type') or sqlalchemy.UnicodeText
        col_obj = sqlalchemy.Column(header, col_type)
        columns.append(col_obj)
    return sqlalchemy.Table(table_name, metadata, *columns)


def import_file(fn, engine):
    connection = engine.connect()
    with gzip.GzipFile(fn, 'r') as gz_file:
        headers = gz_file.readline().decode('utf-8').strip().split('\t')
        table = build_table(os.path.basename(fn), headers)
        insert = table.insert()
        metadata.create_all(tables=[table])
        for block in generate_content(gz_file, headers, table):
            connection.execute(insert, block)


def import_dir(dir_name, engine):
    for fn in glob.glob(os.path.join(dir_name, '*')):
        if not os.path.isfile(fn):
            continue
        import_file(fn, engine)


if __name__ == '__main__':
    dir_name = sys.argv[1]
    engine = sqlalchemy.create_engine(sys.argv[2], echo=False)
    metadata.bind = engine
    import_dir(dir_name, engine)

