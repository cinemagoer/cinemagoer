"""
cli package (imdb package).

This package provides the command line interface for IMDbPY.

Copyright 2017 H. Turgut Uyar <uyar@tekir.org>

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

import sys
from argparse import ArgumentParser

from imdb import VERSION, IMDb


DEFAULT_RESULT_SIZE = 20


def list_results(results, key, type_):
    print('     %(num)s result%(plural)s for "%(key)s":' % {
        'num': len(results),
        'plural': 's' if len(results) != 1 else '',
        'key': key
    })
    field = 'title' if type_ == 'movie' else 'name'
    print('     IMDb id  %s' % field)
    print('     =======  %s' % ('=' * len(field),))
    for i, item in enumerate(results):
        print('%(index)3d. %(imdb_id)7s  %(title)s' % {
            'index': i + 1,
            'imdb_id': getattr(item, type_ + 'ID'),
            'title': item['long imdb ' + field]
        })


def process_results(results, key, type_, first, connection):
    if first:
        item = results[0]
        connection.update(item)
        print(item.summary())
    else:
        list_results(results, key, type_=type_)


def search_item(args):
    connection = IMDb()
    if args.type == 'movie':
        results = connection.search_movie(args.key, results=args.n)
        process_results(results, args.key, type_='movie', first=args.first, connection=connection)
    elif args.type == 'person':
        results = connection.search_person(args.key, results=args.n)
        process_results(results, args.key, type_='person', first=args.first, connection=connection)
    elif args.type == 'character':
        results = connection.search_character(args.key, results=args.n)
        process_results(results, args.key, type_='character', first=args.first, connection=connection)
    elif args.type == 'company':
        results = connection.search_company(args.key, results=args.n)
        process_results(results, args.key, type_='company', first=args.first, connection=connection)
    elif args.type == 'keyword':
        results = connection.search_keyword(args.key, results=args.n)
        if args.first:
            item = results[0]
            results = connection.get_keyword(item, results=20)
            list_results(results, args.key, type_='movie')
        else:
            print('     %(num)s result%(plural)s for "%(key)s":' % {
                'num': len(results),
                'plural': 's' if len(results) != 1 else '',
                'key': args.key
            })
            print('     keyword')
            print('     =======')
            for i, keyword in enumerate(results):
                print('%(index)3d. %(kw)s' % {'index': i + 1, 'kw': keyword})


def get_item(args):
    connection = IMDb()
    if args.type == 'movie':
        movie = connection.get_movie(args.key)
        print(movie.summary())
    elif args.type == 'person':
        person = connection.get_person(args.key)
        print(person.summary())
    elif args.type == 'character':
        character = connection.get_character(args.key)
        print(character.summary())
    elif args.type == 'company':
        company = connection.get_company(args.key)
        print(company.summary())
    elif args.type == 'keyword':
        results = connection.get_keyword(args.key, results=20)
        list_results(results, args.key, type_='movie')


def list_ranking(items, n=None):
    print('  # rating   votes IMDb id title')
    print('=== ====== ======= ======= =====')
    n = n if n is not None else DEFAULT_RESULT_SIZE
    for i, movie in enumerate(items[:n]):
        print('%(index)3d    %(rating)s %(votes)7s %(imdb_id)7s %(title)s' % {
            'index': i + 1,
            'rating': movie.get('rating'),
            'votes': movie.get('votes'),
            'imdb_id': movie.movieID,
            'title': movie.get('long imdb title')
        })


def get_top_movies(args):
    connection = IMDb()
    items = connection.get_top250_movies()
    if args.first:
        connection.update(items[0])
        print(items[0].summary())
    else:
        list_ranking(items, n=args.n)


def get_bottom_movies(args):
    connection = IMDb()
    items = connection.get_bottom100_movies()
    if args.first:
        connection.update(items[0])
        print(items[0].summary())
    else:
        list_ranking(items, n=args.n)


def make_parser(prog):
    parser = ArgumentParser(prog)
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    command_parsers = parser.add_subparsers(metavar='command', dest='command')
    command_parsers.required = True

    command_search_parser = command_parsers.add_parser('search', help='search for items')
    command_search_parser.add_argument('type', help='type of item to search for',
                                       choices=['movie', 'person', 'character', 'company', 'keyword'])
    command_search_parser.add_argument('key', help='title or name of item to search for')
    command_search_parser.add_argument('-n', type=int, help='number of items to list')
    command_search_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_search_parser.set_defaults(func=search_item)

    command_get_parser = command_parsers.add_parser('get', help='retrieve information about an item')
    command_get_parser.add_argument('type', help='type of item to retrieve',
                                    choices=['movie', 'person', 'character', 'company', 'keyword'])
    command_get_parser.add_argument('key', help='IMDb id (or keyword name) of item to retrieve')
    command_get_parser.set_defaults(func=get_item)

    command_top_parser = command_parsers.add_parser('top', help='get top ranked movies')
    command_top_parser.add_argument('-n', type=int, help='number of movies to list')
    command_top_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_top_parser.set_defaults(func=get_top_movies)

    command_bottom_parser = command_parsers.add_parser('bottom', help='get bottom ranked movies')
    command_bottom_parser.add_argument('-n', type=int, help='number of movies to list')
    command_bottom_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_bottom_parser.set_defaults(func=get_bottom_movies)

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = make_parser(prog='imdbpy')
    arguments = parser.parse_args(argv[1:])
    arguments.func(arguments)


if __name__ == '__main__':
    main()
