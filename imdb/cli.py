"""
cli package (imdb package).

This package provides the command line for IMDbPY.

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


def get_entity(args):
    connection = IMDb()
    if args.type == 'movie':
        movie = connection.get_movie(args.id)
        print(movie.summary())
    elif args.type == 'person':
        person = connection.get_person(args.id)
        print(person.summary())
    elif args.type == 'character':
        character = connection.get_character(args.id)
        print(character.summary())
    elif args.type == 'company':
        company = connection.get_company(args.id)
        print(company.summary())
    elif args.type == 'keyword':
        results = connection.get_keyword(args.id, results=20)
        print('    %(num)s result%(plural)s for "%(kw)s":' % {
            'num': len(results),
            'plural': 's' if len(results) != 1 else '',
            'kw': args.id
        })
        print(' : movie title')
        for i, movie in enumerate(results):
            print('%d: %s' % (i + 1, movie['long imdb title']))

def make_parser(prog):
    parser = ArgumentParser(prog)
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    commands = parser.add_subparsers(metavar='command', dest='command')
    commands.required = True

    command_get_parser = commands.add_parser('get', help='get information about an entity')
    command_get_parser.add_argument('type', help='type of entity to get',
                                    choices=['movie', 'person', 'character', 'company', 'keyword'])
    command_get_parser.add_argument('id', help='IMDb id of entity to get')
    command_get_parser.set_defaults(func=get_entity)

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = make_parser(prog='imdbpy')
    arguments = parser.parse_args(argv[1:])
    arguments.func(arguments)


if __name__ == '__main__':
    main()
