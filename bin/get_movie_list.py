#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_movie_list.py

Usage: get_movie_list.py ls091843609

Parse the list and print the results.
"""

import sys

# Import the Cinemagoer package.
try:
    import imdb
except ImportError:
    print('You need to install the Cinemagoer package!')
    sys.exit(1)


if len(sys.argv) != 2:
    print('Only one argument is required:')
    print('  %s "movie list id"' % sys.argv[0])
    sys.exit(2)

listId = sys.argv[1]

i = imdb.IMDb()

out_encoding = sys.stdout.encoding or sys.getdefaultencoding()

try:
    # Do the search, and get the results (a list of Movie objects).
    results = i.get_movie_list(list_=listId)
except imdb.IMDbError as e:
    print("Probably you're not connected to Internet.  Complete error report:")
    print(e)
    sys.exit(3)

# Print the long imdb title for every movie.
for movie in results:
    outp = '%s\t: %s' % (movie['rank'], movie['long imdb title'])
    print(outp)
