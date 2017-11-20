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


def list_movies(movies, key):
    print('     %(num)s result%(plural)s for "%(kw)s":' % {
        'num': len(movies),
        'plural': 's' if len(movies) != 1 else '',
        'kw': key
    })
    print('     IMDb id  movie title')
    print('     =======  ===========')
    for i, item in enumerate(movies):
        print('%(index)3d. %(imdb_id)7s  %(title)s' % {
            'index': i + 1,
            'imdb_id': item.movieID,
            'title': item['long imdb title']
        })


def search_entity(args):
    connection = IMDb()
    if args.type == 'movie':
        results = connection.search_movie(args.key)
        list_movies(results, args.key)


def get_entity(args):
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
        list_movies(results, args.key)


def get_top_movies(args):
    connection = IMDb()
    movies = connection.get_top250_movies()
    print('Top movies')
    print('    rating\t  votes\tIMDb id\ttitle')
    print('    ======\t=======\t=======\t=====')
    for i, movie in enumerate(movies[:args.n]):
        print('%(index)3d.   %(rating)s\t%(votes)7s\t%(imdb_id)7s\t%(title)s' % {
            'index': i + 1,
            'rating': movie.get('rating'),
            'votes': movie.get('votes'),
            'imdb_id': movie.movieID,
            'title': movie.get('long imdb title')
        })


def get_bottom_movies(args):
    connection = IMDb()
    movies = connection.get_bottom100_movies()
    print('Bottom movies')
    print('    rating\t  votes\ttitle')
    print('    ======\t=======\t=====')
    for i, movie in enumerate(movies[:args.n]):
        print('%(index)3d.   %(rating)s\t%(votes)7s\t%(imdb_id)7s\t%(title)s' % {
            'index': i + 1,
            'rating': movie.get('rating'),
            'votes': movie.get('votes'),
            'imdb_id': movie.movieID,
            'title': movie.get('long imdb title')
        })


def make_parser(prog):
    parser = ArgumentParser(prog)
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    commands = parser.add_subparsers(metavar='command', dest='command')
    commands.required = True

    command_search_parser = commands.add_parser('search', help='search for an entity')
    command_search_parser.add_argument('type', help='type of entity to search for',
                                       choices=['movie', 'person', 'character', 'company', 'keyword'])
    command_search_parser.add_argument('key', help='title or name of entity to search for')
    command_search_parser.set_defaults(func=search_entity)

    command_get_parser = commands.add_parser('get', help='get information about an entity')
    command_get_parser.add_argument('type', help='type of entity to get',
                                    choices=['movie', 'person', 'character', 'company', 'keyword'])
    command_get_parser.add_argument('key', help='IMDb id (or keyword name) of entity to get')
    command_get_parser.set_defaults(func=get_entity)

    command_top_parser = commands.add_parser('top', help='get top ranked movies')
    command_top_parser.add_argument('n', type=int, help='number of movies to list (max 250)')
    command_top_parser.set_defaults(func=get_top_movies)

    command_bottom_parser = commands.add_parser('bottom', help='get bottom ranked movies')
    command_bottom_parser.add_argument('n', type=int, help='number of movies to list (max 100)')
    command_bottom_parser.set_defaults(func=get_bottom_movies)

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = make_parser(prog='imdbpy')
    arguments = parser.parse_args(argv[1:])
    arguments.func(arguments)


if __name__ == '__main__':
    main()
