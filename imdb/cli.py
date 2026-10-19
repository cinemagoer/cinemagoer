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
from argparse import (
    ArgumentParser,
    ArgumentTypeError,
    RawDescriptionHelpFormatter,
)

from imdb import VERSION, IMDb, IMDbError

DEFAULT_RESULT_SIZE = 20
EXIT_ERROR = 1
ID_PREFIX = {'movie': 'tt', 'person': 'nm'}


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
    prefix = ID_PREFIX[type_]
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


def print_item(item, type_, urls):
    """Print an item's summary followed by its IMDb id and web page."""
    imdb_id = getattr(item, type_ + 'ID')
    summary = item.summary()
    print(summary, end='' if summary.endswith('\n') else '\n')
    print('IMDb ID: %s%s' % (ID_PREFIX[type_], imdb_id))
    print('IMDb page: %s' % (urls[type_ + '_main'] % imdb_id))


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
            print_item(items[0], args.type, connection.urls)
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
        print_item(item, args.type, connection.urls)
    finally:
        connection.close()


class CommandParser(ArgumentParser):
    """Accept a bare help topic as an alias for the help option."""

    def parse_known_args(self, args=None, namespace=None):
        if args == ['help']:
            args = ['--help']
        return super().parse_known_args(args, namespace)


def make_parser(prog='cinemagoer'):
    parser = ArgumentParser(
        prog, description=(
            'Search and retrieve movies and people from a local IMDb '
            'dataset database.'
        ),
        formatter_class=RawDescriptionHelpFormatter,
        epilog=(
            'Database setup:\n'
            '  Import downloaded IMDb datasets with s32cinemagoer.py first.\n'
            '  Set --uri before the command or use CINEMAGOER_S3_URI.\n\n'
            'Examples:\n'
            f'  {prog} --uri sqlite:///cinemagoer.db '
            'search movie "Miss Jerry" -n 5\n'
            f'  {prog} --uri sqlite:///cinemagoer.db '
            'search person "Fred Astaire" --first\n'
            f'  {prog} --uri sqlite:///cinemagoer.db '
            'get movie tt0000009\n'
            f'  {prog} --uri sqlite:///cinemagoer.db '
            'get person nm0000001\n\n'
            f'Use "{prog} help COMMAND" or "{prog} COMMAND --help" '
            f'or "{prog} COMMAND help" for command details.'
        ),
    )
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
    parser.add_argument('--uri', default=os.getenv('CINEMAGOER_S3_URI'),
                        help='database URI (defaults to CINEMAGOER_S3_URI)')
    parser.add_argument('--debug', action='store_true',
                        help='show a traceback for expected runtime errors')

    command_parsers = parser.add_subparsers(
        metavar='command', dest='command', parser_class=CommandParser
    )
    command_parsers.required = True

    command_search_parser = command_parsers.add_parser(
        'search', help='search for movies or people',
        description='Search by movie title or person name.',
    )
    command_search_parser.add_argument('type', help='type of item to search for',
                                                    choices=['movie', 'person'])
    command_search_parser.add_argument('key', help='title or name of item to search for')
    command_search_parser.add_argument(
        '-n', type=positive_int, metavar='COUNT',
        help='maximum items to list (default: 20; ignored with --first)'
    )
    command_search_parser.add_argument('--first', action='store_true', help='display the full summary of the first result')
    command_search_parser.set_defaults(func=search_item)

    command_get_parser = command_parsers.add_parser(
        'get', help='retrieve a movie or person by IMDb id',
        description=(
            'Display a movie or person summary, IMDb id, and IMDb page URL. '
            'Use digits, movie ids starting with tt, or person ids starting with nm.'
        ),
    )
    command_get_parser.add_argument('type', help='type of item to retrieve',
                                                choices=['movie', 'person'])
    command_get_parser.add_argument(
        'key', help='IMDb id (digits or the appropriate tt/nm prefix)'
    )
    command_get_parser.set_defaults(func=get_item)

    help_topics = {
        'search': command_search_parser,
        'get': command_get_parser,
    }
    command_help_parser = command_parsers.add_parser(
        'help', help='show general or command-specific help',
        description='Show help without connecting to a database.',
    )
    command_help_parser.add_argument(
        'topic', nargs='?', choices=help_topics,
        help='command to explain (default: general help)',
    )
    command_help_parser.set_defaults(
        func=lambda args: help_topics.get(args.topic, parser).print_help()
    )

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = make_parser()
    arguments = parser.parse_args(argv[1:])
    try:
        arguments.func(arguments)
    except (CLIError, IMDbError) as exc:
        if arguments.debug:
            raise
        print('%s: error: %s' % (parser.prog, exc), file=sys.stderr)
        return EXIT_ERROR
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
