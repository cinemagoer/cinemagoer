# Copyright 2017 H. Turgut Uyar <uyar@tekir.org>
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
This module provides the command line interface for Cinemagoer.
"""

import sys
from argparse import ArgumentParser

from imdb import VERSION, IMDb

DEFAULT_RESULT_SIZE = 20


def list_results(items, type_, n=None):
    field = 'title' if type_ == 'movie' else 'name'
    print('  # IMDb id %s' % field)
    print('=== ======= %s' % ('=' * len(field),))
    for i, item in enumerate(items[:n]):
        print('%(index)3d %(imdb_id)7s %(title)s' % {
            'index': i + 1,
            'imdb_id': getattr(item, type_ + 'ID'),
            'title': item['long imdb ' + field]
        })


def search_item(args):
    connection = IMDb()
    if args.type == 'movie':
        items = connection.search_movie(args.key)
    else:
        items = connection.search_person(args.key)

    if args.first:
        connection.update(items[0])
        print(items[0].summary())
    else:
        list_results(items, type_=args.type, n=args.n)


def get_item(args):
    connection = IMDb()
    if args.type == 'movie':
        item = connection.get_movie(args.key)
    else:
        item = connection.get_person(args.key)
    print(item.summary())


def make_parser(prog):
    parser = ArgumentParser(prog)
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    command_parsers = parser.add_subparsers(metavar='command', dest='command')
    command_parsers.required = True

    command_search_parser = command_parsers.add_parser('search', help='search for items')
    command_search_parser.add_argument('type', help='type of item to search for',
                                                    choices=['movie', 'person'])
    command_search_parser.add_argument('key', help='title or name of item to search for')
    command_search_parser.add_argument('-n', type=int, help='number of items to list')
    command_search_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_search_parser.set_defaults(func=search_item)

    command_get_parser = command_parsers.add_parser('get', help='retrieve information about an item')
    command_get_parser.add_argument('type', help='type of item to retrieve',
                                                choices=['movie', 'person'])
    command_get_parser.add_argument('key', help='IMDb id (or keyword name) of item to retrieve')
    command_get_parser.set_defaults(func=get_item)

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = make_parser(prog='imdbpy')
    arguments = parser.parse_args(argv[1:])
    arguments.func(arguments)


if __name__ == '__main__':
    main()
