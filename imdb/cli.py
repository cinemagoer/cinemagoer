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

import os
import sys
from argparse import ArgumentParser, ArgumentTypeError

from imdb import VERSION, IMDb, IMDbError
from imdb._logging import imdbpyLogger

DEFAULT_RESULT_SIZE = 20
EXIT_ERROR = 1


class CLIError(Exception):
    """An expected command-line failure with a concise user-facing message."""


def positive_int(value):
    """Return a positive integer for argparse options."""
    try:
        value = int(value)
    except ValueError as exc:
        raise ArgumentTypeError('must be a positive integer') from exc
    if value < 1:
        raise ArgumentTypeError('must be a positive integer')
    return value


def normalize_imdb_id(type_, value):
    """Validate a movie or person IMDb ID and remove its optional prefix."""
    original_value = value
    prefix = 'tt' if type_ == 'movie' else 'nm'
    if value.startswith(prefix):
        value = value[len(prefix):]
    if not value.isdigit():
        raise CLIError(
            'invalid %s IMDb id %r; expected digits or a %s-prefixed id'
            % (type_, original_value, prefix)
        )
    return value


def get_connection(args):
    uri = args.uri or os.getenv('CINEMAGOER_S3_URI')
    if uri:
        return IMDb('s3', uri=uri)
    return IMDb()


def list_results(items, type_, n=None):
    field = 'title' if type_ == 'movie' else 'name'
    items = items[:n]
    imdb_id_width = max(
        len('IMDb id'),
        *(len(str(getattr(item, type_ + 'ID'))) for item in items),
    ) if items else len('IMDb id')
    print('  # %s %s' % ('IMDb id'.ljust(imdb_id_width), field))
    print('=== %s %s' % ('=' * imdb_id_width, '=' * len(field)))
    for i, item in enumerate(items):
        imdb_id = str(getattr(item, type_ + 'ID'))
        print('%(index)3d %(imdb_id)s %(title)s' % {
            'index': i + 1,
            'imdb_id': imdb_id.rjust(imdb_id_width),
            'title': item['long imdb ' + field]
        })


def search_item(args):
    connection = get_connection(args)
    try:
        if args.type == 'movie':
            items = connection.search_movie(args.key)
        else:
            items = connection.search_person(args.key)

        if not items:
            raise CLIError('no %s results found for %r' % (args.type, args.key))
        if args.first:
            connection.update(items[0])
            print(items[0].summary())
        else:
            list_results(items, type_=args.type, n=args.n)
    finally:
        connection.close()


def get_item(args):
    item_id = normalize_imdb_id(args.type, args.key)
    connection = get_connection(args)
    try:
        if args.type == 'movie':
            item = connection.get_movie(item_id)
        else:
            item = connection.get_person(item_id)
        if not item:
            raise CLIError(
                '%s with IMDb id %r was not found' % (args.type, args.key)
            )
        print(item.summary())
    finally:
        connection.close()


def make_parser(prog='cinemagoer'):
    parser = ArgumentParser(prog)
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
    parser.add_argument('--uri', default=os.getenv('CINEMAGOER_S3_URI'),
                        help='database URI for the s3 access system')
    parser.add_argument('--debug', action='store_true',
                        help='show a traceback for expected runtime errors')

    command_parsers = parser.add_subparsers(metavar='command', dest='command')
    command_parsers.required = True

    command_search_parser = command_parsers.add_parser('search', help='search for items')
    command_search_parser.add_argument('type', help='type of item to search for',
                                                    choices=['movie', 'person'])
    command_search_parser.add_argument('key', help='title or name of item to search for')
    command_search_parser.add_argument(
        '-n', type=positive_int, help='positive number of items to list'
    )
    command_search_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_search_parser.set_defaults(func=search_item)

    command_get_parser = command_parsers.add_parser('get', help='retrieve information about an item')
    command_get_parser.add_argument('type', help='type of item to retrieve',
                                                choices=['movie', 'person'])
    command_get_parser.add_argument(
        'key', help='IMDb id (digits or the appropriate tt/nm prefix)'
    )
    command_get_parser.set_defaults(func=get_item)

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = make_parser()
    arguments = parser.parse_args(argv[1:])
    logger_disabled = imdbpyLogger.disabled
    if not arguments.debug:
        imdbpyLogger.disabled = True
    try:
        try:
            arguments.func(arguments)
        except (CLIError, IMDbError) as exc:
            if arguments.debug:
                raise
            print('%s: error: %s' % (parser.prog, exc), file=sys.stderr)
            return EXIT_ERROR
    finally:
        imdbpyLogger.disabled = logger_disabled
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
