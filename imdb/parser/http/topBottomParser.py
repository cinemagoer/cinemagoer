# Copyright 2009-2023 Davide Alberani <da@erlug.linux.it>
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

from imdb.parser.http import jextr
from imdb.utils import analyze_title

from . import jsel
from .piculet import Path, Rule, Rules, reducers
from .utils import DOMParserBase, analyze_imdbid


class DOMHTMLTop250Parser(DOMParserBase):
    """A parser for the "top 250 movies" page."""
    ranktext = 'top 250 rank'

    rules = [
        Rule(
            key='__NEXT_DATA__',
            extractor=Path(
                '//script[@id="__NEXT_DATA__"]/text()',
                reduce=reducers.first,
                transform=lambda x: x.strip()
            )
        )
    ]

    def postprocess_data(self, data):
        if '__NEXT_DATA__' not in data:
            return []
        movies = []
        jdata = jsel.select(data['__NEXT_DATA__'], '.props.pageProps.pageData.chartTitles.edges')
        if not jdata:
            return []
        for item in jdata:
            mdata = {}
            node = item.get('node', {})
            if not node:
                continue
            mdata = jextr.movie_data(node)
            if not mdata:
                continue
            rank = item.get('currentRank', None)
            if rank:
                mdata[self.ranktext] = rank
            movie_id = mdata['id']
            del mdata['id']
            movies.append((movie_id, mdata))
        return movies


class DOMHTMLBottom100Parser(DOMHTMLTop250Parser):
    """A parser for the "bottom 100 movies" page."""
    ranktext = 'bottom 100 rank'


class DOMHTMLMoviemeter100Parser(DOMHTMLTop250Parser):
    """A parser for the "Most Popular Movies" page."""
    ranktext = 'popular movies 100 rank'


class DOMHTMLTVmeter100Parser(DOMHTMLTop250Parser):
    """A parser for the "Most Popular TV Shows" page."""
    ranktext = 'popular tv 100 rank'


class DOMHTMLTVTop250Parser(DOMHTMLTop250Parser):
    """A parser for the "Top Rated TV Shows" page."""
    ranktext = 'top tv 250 rank'


class DOMHTMLTopIndian250Parser(DOMHTMLTop250Parser):
    """A parser for the "Top Rated Indian Movies" page."""
    ranktext = 'top indian 250 rank'
    rules = [
        Rule(
            key='chart',
            extractor=Rules(
                foreach='//ul[contains(@class, "ipc-metadata-list")]/li',
                rules=[
                    Rule(
                        key='movieID',
                        extractor=Path('.//a[contains(@class, "ipc-metadata-list-item__icon-link")]/@href', reduce=reducers.first)
                    ),
                    Rule(
                        key='title',
                        extractor=Path('.//span[contains(@data-testid, "rank-list-item-title")]/text()')
                    ),
                    Rule(
                        key='rating',
                        extractor=Path('.//span[contains(@class, "ipc-rating-star")]//text()',
                                       reduce=reducers.first,
                                       transform=lambda x: round(float(x), 1))
                    )
                ]
            )
        )
    ]

    def postprocess_data(self, data):
        if (not data) or ('chart' not in data):
            return []
        movies = []
        for count, entry in enumerate(data['chart']):
            if ('movieID' not in entry) or ('title' not in entry):
                continue
            movie_id = analyze_imdbid(entry['movieID'])
            entry[self.ranktext] = count + 1
            movies.append((movie_id, entry))
        return movies


class DOMHTMLBoxOfficeParser(DOMParserBase):
    """A parser for the "top boxoffice movies" page."""
    ranktext = 'top box office rank'
    rules = [
        Rule(
            key='chart',
            extractor=Rules(
                foreach='//ul[contains(@class, "ipc-metadata-list")]/li',
                rules=[
                    Rule(
                        key='movieID',
                        extractor=Path('.//a[contains(@class, "ipc-title-link-wrapper")]/@href', reduce=reducers.first)
                    ),
                    Rule(
                        key='title',
                        extractor=Path('.//h3[contains(@class, "ipc-title__text")]/text()', reduce=reducers.first)
                    ),
                    Rule(
                        key='weekend',
                        extractor=Path('.//span[contains(@class, "sc-3a4309f8-0") and contains(@data-testid, "boxoffice-weekend-gross-to-date")]/text()', reduce=reducers.first)
                    ),
                    Rule(
                        key='gross',
                        extractor=Path('.//span[contains(@class, "sc-3a4309f8-0") and contains(@data-testid, "boxoffice-total-gross-to-date")]/text()', reduce=reducers.first)
                    ),
                    Rule(
                        key='weeks',
                        extractor=Path('.//span[contains(@class, "sc-3a4309f8-0") and contains(@data-testid, "boxoffice-week-in-release")]/text()', reduce=reducers.first)
                    ),
                ]
            )
        )
    ]

    def postprocess_data(self, data):
        if (not data) or ('chart' not in data):
            return []

        movies = []
        for count, entry in enumerate(data['chart']):
            if ('movieID' not in entry) or ('title' not in entry):
                continue

            movie_id = analyze_imdbid(entry['movieID'])
            if movie_id is None:
                continue
            del entry['movieID']

            title = analyze_title(entry['title'])
            entry.update(title)
            entry[self.ranktext] = count + 1

            # Clean up fields
            if 'weekend' in entry and entry['weekend']:
                entry['weekend'] = entry['weekend'].strip()
            if 'gross' in entry and entry['gross']:
                entry['gross'] = entry['gross'].strip()
            if 'weeks' in entry and entry['weeks']:
                entry['weeks'] = entry['weeks'].strip()

            movies.append((movie_id, entry))
        return movies


_OBJECTS = {
    'top250_parser': ((DOMHTMLTop250Parser,), None),
    'bottom100_parser': ((DOMHTMLBottom100Parser,), None),
    'moviemeter100_parser': ((DOMHTMLMoviemeter100Parser,), None),
    'toptv250_parser': ((DOMHTMLTVTop250Parser,), None),
    'tvmeter100_parser': ((DOMHTMLTVmeter100Parser,), None),
    'topindian250_parser': ((DOMHTMLTopIndian250Parser,), None),
    'boxoffice_parser': ((DOMHTMLBoxOfficeParser,), None)
}
