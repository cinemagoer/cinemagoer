# Copyright 2009-2020 Davide Alberani <da@erlug.linux.it>
#                2018 H. Turgut Uyar <uyar@tekir.org>
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
This module provides the classes (and the instances) that are used to parse
the pages for the lists of top 250 and bottom 100 movies.

Pages:

http://www.imdb.com/chart/top

http://www.imdb.com/chart/bottom
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from .piculet import Path, Rule, Rules, reducers
from .utils import DOMParserBase, analyze_imdbid


class DOMHTMLMoviesNearYou(DOMParserBase):
    rules = [
        Rule(
            foreach='//h3[@itemprop="name"]/a',
            key=Path('./text()'),
            extractor=Rules(
                rules=[
                    Rule(
                        foreach='//span[@itemprop="name"]/a',
                        key=Path('./text()'),
                        extractor=Path('./../../..//div[@class="showtimes"]/text()')
                    )
                ]
               
            )
        )
    ]

    def postprocess_data(self, data):
        for movies in data.values():
            for movie, showtimes in movies.items():
                    movies[movie] = " ".join(showtimes.replace("\n", "").strip().split())
        return data


_OBJECTS = {
    'showtime_parser': ((DOMHTMLMoviesNearYou,), None),
}
