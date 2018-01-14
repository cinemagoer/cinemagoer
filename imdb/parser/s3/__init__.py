"""
parser.s3 package (imdb package).

This package provides the IMDbS3AccessSystem class used to access
IMDb's data through the web interface.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "s3" or "s3dataset".

Copyright 2017 Davide Alberani <da@erlug.linux.it>

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

import logging
import sqlalchemy
from imdb import IMDbBase
from .utils import DB_TRANSFORM


class IMDbS3AccessSystem(IMDbBase):
    """The class used to access IMDb's data through the s3 dataset."""

    accessSystem = 's3'
    _s3_logger = logging.getLogger('imdbpy.parser.s3')
    _metadata = sqlalchemy.MetaData()

    def __init__(self, uri, adultSearch=True, *arguments, **keywords):
        """Initialize the access system."""
        IMDbBase.__init__(self, *arguments, **keywords)
        self._engine = sqlalchemy.create_engine(uri, echo=False)
        self._metadata.bind = self._engine
        self._metadata.reflect()
        self.T = self._metadata.tables

    def _rename(self, table, data):
        for column, conf in DB_TRANSFORM.get(table, {}).items():
            if 'rename' not in conf:
                continue
            if column not in data:
                continue
            data[conf['rename']] = data[column]
            del data[column]
        return data

    def get_movie_main(self, movieID):
        tb = self.T['title_basics']
        movieID = int(movieID)
        movie = tb.select(tb.c.tconst == movieID).execute().fetchone()
        data = self._rename('title_basics', dict(movie))
        return {'data': data}

    def get_movie_plot(self, movieID):
        return {}
