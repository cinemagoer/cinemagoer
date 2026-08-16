#!/usr/bin/env python3
# Copyright 2017-2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Import IMDb's downloadable datasets into a Cinemagoer database."""

import argparse
import logging

from imdb.parser.s3.importer import import_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tsv_files_dir')
    parser.add_argument('db_uri')
    parser.add_argument(
        '--verbose', help='increase verbosity', action='store_true'
    )
    parser.add_argument(
        '--cleanup', help='remove files after importing', action='store_true'
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO
    )
    import_dir(args.tsv_files_dir, args.db_uri, cleanup=args.cleanup)


if __name__ == '__main__':
    main()
