# Copyright 2009-2017 Davide Alberani <da@erlug.linux.it>
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

from imdb.utils import analyze_title

from .piculet import Path, Rule, Rules
from .utils import DOMParserBase, analyze_imdbid


class DOMHTMLTop250Parser(DOMParserBase):
    """A parser for the "top 250 movies" page."""
    ranktext = 'top 250 rank'

    rules = [
        Rule(
            key='chart',
            extractor=Rules(
                foreach='//div[@id="main"]//div[1]//div//table//tbody//tr',
                rules=[
                    Rule(
                        key='rank',
                        extractor=Path('./td[2]/text()')
                    ),
                    Rule(
                        key='rating',
                        extractor=Path('./td[3]//strong//text()')
                    ),
                    Rule(
                        key='title',
                        extractor=Path('./td[2]//a//text()')
                    ),
                    Rule(
                        key='year',
                        extractor=Path('./td[2]//span//text()')
                    ),
                    Rule(
                        key='movieID',
                        extractor=Path('./td[2]//a/@href')
                    ),
                    Rule(
                        key='votes',
                        extractor=Path('./td[3]//strong/@title')
                    )
                ]
            )
        )
    ]

    def postprocess_data(self, data):
        if (not data) or ('chart' not in data):
            return []

        movies = []
        for entry in data['chart']:
            if ('movieID' not in entry) or ('rank' not in entry) or ('title' not in entry):
                continue

            movie_id = analyze_imdbid(entry['movieID'])
            if movie_id is None:
                continue

            movie_info = analyze_title(entry['title'] + ' ' + entry.get('year', ''))
            try:
                movie_info[self.ranktext] = int(entry['rank'].replace('.', ''))
            except ValueError:
                pass
            del entry['rank']

            if 'votes' in entry:
                try:
                    votes = entry['votes'].replace(' user ratings', '')
                    votes = votes.split(' based on ')[1]    # is IndexError possible?
                    movie_info['votes'] = int(votes.replace(',', ''))
                except (IndexError, ValueError):
                    pass

            if 'rating' in entry:
                try:
                    movie_info['rating'] = float(entry['rating'])
                except ValueError:
                    pass

            movies.append((movie_id, movie_info))
        return movies


class DOMHTMLBottom100Parser(DOMHTMLTop250Parser):
    """A parser for the "bottom 100 movies" page."""
    ranktext = 'bottom 100 rank'


_OBJECTS = {
    'top250_parser': ((DOMHTMLTop250Parser,), None),
    'bottom100_parser': ((DOMHTMLBottom100Parser,), None)
}
