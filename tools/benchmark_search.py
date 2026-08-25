# Copyright 2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Reproduce bounded-search measurements on a fixed SQLite snapshot."""

import argparse
import json
import sqlite3
import statistics
import sys
import time
import tracemalloc
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from imdb import Cinemagoer  # noqa: E402
from imdb.parser.s3.adapters import search_candidate_limit  # noqa: E402
from imdb.parser.s3.utils import name_soundexes, title_soundex  # noqa: E402

TITLE_QUERIES = ('Love', 'The Matrix')
PERSON_QUERIES = ('Li', 'John Smith')
TABLES = ('title_basics', 'title_akas', 'name_basics')


def _query_plan(connection, sql, parameters):
    rows = connection.execute(
        'EXPLAIN QUERY PLAN ' + sql, parameters
    ).fetchall()
    return [row[3] for row in rows]


def _title_measurement(connection, query):
    soundex = title_soundex(query)
    sources = []
    for table in ('title_basics', 'title_akas'):
        sql = 'SELECT * FROM %s WHERE t_soundex = ? LIMIT ?' % table
        sources.append({
            'source': table,
            'candidates': connection.execute(
                'SELECT count(*) FROM %s WHERE t_soundex = ?' % table,
                (soundex,),
            ).fetchone()[0],
            'plan': _query_plan(connection, sql, (soundex, 1)),
        })
    return {'query': query, 'soundex': soundex, 'sources': sources}


def _person_measurement(connection, query):
    soundexes = tuple(code for code in name_soundexes(query) if code)
    placeholders = ', '.join('?' for _ in soundexes)
    conditions = ' OR '.join(
        '%s IN (%s)' % (column, placeholders)
        for column in ('ns_soundex', 'sn_soundex', 's_soundex')
    )
    parameters = soundexes * 3
    sql = 'SELECT * FROM name_basics WHERE %s LIMIT ?' % conditions
    return {
        'query': query,
        'soundexes': soundexes,
        'candidates': connection.execute(
            'SELECT count(*) FROM name_basics WHERE ' + conditions,
            parameters,
        ).fetchone()[0],
        'plan': _query_plan(connection, sql, parameters + (1,)),
    }


def _time_search(access, kind, query, results, repeat):
    search = access.search_movie if kind == 'title' else access.search_person
    timings = []
    peak_bytes = []
    found = []
    for _ in range(repeat):
        tracemalloc.start()
        started = time.perf_counter()
        matches = search(query, results=results)
        timings.append(time.perf_counter() - started)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_bytes.append(peak)
        if kind == 'title':
            found = [(item.movieID, item.get('title')) for item in matches]
        else:
            found = [(item.personID, item.get('name')) for item in matches]
    return {
        'query': query,
        'median_seconds': round(statistics.median(timings), 6),
        'peak_python_bytes': max(peak_bytes),
        'results': found,
    }


def benchmark(database, adapter, results, repeat):
    database = database.resolve()
    sqlite_uri = database.as_uri() + '?mode=ro'
    with closing(sqlite3.connect(sqlite_uri, uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        dataset = {
            'path': str(database),
            'bytes': database.stat().st_size,
            'rows': {
                table: connection.execute(
                    'SELECT count(*) FROM %s' % table
                ).fetchone()[0]
                for table in TABLES
            },
        }
        candidates = {
            'titles': [
                _title_measurement(connection, query)
                for query in TITLE_QUERIES
            ],
            'people': [
                _person_measurement(connection, query)
                for query in PERSON_QUERIES
            ],
        }

    scheme = 'sqlite+pysqlite' if adapter == 'sqlalchemy' else 'sqlite'
    uri = '%s:///%s' % (scheme, database)
    started = time.perf_counter()
    with Cinemagoer('s3', uri=uri) as access:
        startup_seconds = time.perf_counter() - started
        searches = {
            'titles': [
                _time_search(access, 'title', query, results, repeat)
                for query in TITLE_QUERIES
            ],
            'people': [
                _time_search(access, 'person', query, results, repeat)
                for query in PERSON_QUERIES
            ],
        }
        reflected_tables = sorted(
            getattr(access._adapter, 'tables', {})
        )
    return {
        'adapter': adapter,
        'candidate_limit': search_candidate_limit(results),
        'dataset': dataset,
        'repeat': repeat,
        'requested_results': results,
        'startup_seconds': round(startup_seconds, 6),
        'reflected_tables': reflected_tables,
        'candidates': candidates,
        'searches': searches,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    parser.add_argument(
        '--adapter', choices=('native', 'sqlalchemy'), default='native'
    )
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--results', type=int, default=5)
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error('database must be an existing SQLite file')
    if args.repeat < 1 or args.results < 1:
        parser.error('--repeat and --results must be positive')
    output = json.dumps(
        benchmark(args.database, args.adapter, args.results, args.repeat),
        indent=2,
        sort_keys=True,
    )
    sys.stdout.write(output + '\n')


if __name__ == '__main__':
    main()
