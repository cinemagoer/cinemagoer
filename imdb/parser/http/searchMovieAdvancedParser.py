# -*- coding: utf-8 -*-

# Copyright 2019 H. Turgut Uyar <uyar@tekir.org>
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
the results of an advanced search for a given title.

For example, when searching for the title "the passion", the parsed page
would be:

http://www.imdb.com/search/title/?title=the+passion
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re

from .piculet import Path, Rule, Rules, preprocessors, reducers
from .utils import DOMParserBase, analyze_imdbid, build_movie, build_person

_re_secondary_info = re.compile(
    r'''(\(([IVXLCM]+)\)\s+)?\((\d{4})(–(\s|(\d{4})))?(\s+(.*))?\)|(\(([IVXLCM]+)\))'''
)

_re_index = re.compile(r'(\d+)\.\s+(.+)')

_KIND_MAP = {
    'tv short': 'tv short movie',
    'video': 'video movie'
}

def cleanup_title(title):
    """Cleanup the title string by removing the index and leading/trailing spaces."""
    if title:
        match = _re_index.match(title)
        if match:
            return match.group(2).strip()
    return title.strip() if title else title

def _parse_secondary_info(info):
    parsed = {}
    match = _re_secondary_info.match(info)
    if not match:
        return parsed
    kind = None
    if match.group(2):
        parsed['imdbIndex'] = match.group(2)
    if match.group(3):
        parsed['year'] = int(match.group(3))
    if match.group(4):
        kind = 'tv series'
    if match.group(6):
        parsed['series years'] = match.group(3) + "-" + match.group(6)
    if match.group(8):
        kind = match.group(8).lower()
    if match.group(10):  # Added to support case of imdbIndex but no year
        parsed['imdbIndex'] = match.group(10)
    if kind is None:
        kind = 'movie'
    parsed['kind'] = _KIND_MAP.get(kind, kind)
    return parsed


class DOMHTMLSearchMovieAdvancedParser(DOMParserBase):
    """A parser for the title search page."""

    person_rules = [
        Rule(key='name', extractor=Path('./text()', reduce=reducers.first)),
        Rule(key='link', extractor=Path('./@href', reduce=reducers.first))
    ]
    rules = [
        Rule(
            key='data',
            extractor=Rules(
                foreach='//li[contains(@class, "ipc-metadata-list-summary-item")]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path(
                            './/a[contains(@class, "ipc-title-link-wrapper")]/@href',
                            reduce=reducers.first
                        )
                    ),
                    Rule(
                        key='title',
                        extractor=Path(
                            './/a[contains(@class, "ipc-title-link-wrapper")]/h3/text()',
                            reduce=reducers.first,
                            transform=cleanup_title
                        )
                    ),
                    Rule(
                        key='secondary_info',
                        extractor=Path('.//div[contains(@class, "dli-title-metadata")]//text()',
                                       reduce=reducers.join)
                    ),
                    Rule(
                        key='certificates',
                        extractor=Path('.//span[@class="certificate"]/text()',
                                       reduce=reducers.first,
                                       transform=lambda s: [s])
                    ),
                    Rule(
                        key='runtimes',
                        extractor=Path('.//span[@class="runtime"]/text()',
                                       reduce=reducers.first,
                                       transform=lambda s: [[w for w in s.split() if w.isdigit()][0]])
                    ),
                    Rule(
                        key='genres',
                        extractor=Path('.//span[@class="genre"]/text()',
                                       reduce=reducers.first,
                                       transform=lambda s: [w.strip() for w in s.split(',')])
                    ),
                    Rule(
                        key='rating',
                        extractor=Path('.//div[@name="ir"]/@data-value',
                                       reduce=reducers.first,
                                       transform=float)
                    ),
                    Rule(
                        key='votes',
                        extractor=Path('.//span[@name="nv"]/@data-value',
                                       reduce=reducers.first,
                                       transform=int)
                    ),
                    Rule(
                        key='metascore',
                        extractor=Path('.//span[@class="metascore  favorable"]/text()',
                                       reduce=reducers.first,
                                       transform=int)
                    ),
                    Rule(
                        key='gross',
                        extractor=Path('.//span[@name="GROSS"]/@data-value',
                                       reduce=reducers.normalize,
                                       transform=int)
                    ),
                    Rule(
                        key='plot',
                        extractor=Path('./p[@class="text-muted"]//text()',
                                       reduce=reducers.clean)
                    ),
                    Rule(
                        key='cover url',
                        extractor=Path('//img[contains(@class, "ipc-image")]/@src', reduce=reducers.first)
                    ),
                    Rule(
                        key='episode',
                        extractor=Rules(
                            rules=[
                                Rule(key='link',
                                     extractor=Path('./h3/small/a/@href', reduce=reducers.first)),
                                Rule(key='title',
                                     extractor=Path(
                                         './h3/small/a/text()',
                                         reduce=reducers.first,
                                         transform=cleanup_title
                                    )
                                ),
                                Rule(key='secondary_info',
                                     extractor=Path('./h3/small/span[@class="lister-item-year text-muted unbold"]/text()',  # noqa: E501
                                                    reduce=reducers.first)),
                            ]
                        )
                    )
                ]
            )
        )
    ]

    def _init(self):
        self.url = ''

    def _reset(self):
        self.url = ''

    def postprocess_data(self, data):
        if 'data' not in data:
            data = {'data': []}
        results = getattr(self, 'results', None)
        if results is not None:
            data['data'][:] = data['data'][:results]

        result = []
        idx = 1
        for movie in data['data']:
            episode = movie.pop('episode', None)
            if episode is not None:
                series = build_movie(movie.get('title'), movieID=analyze_imdbid(movie['link']))
                series['kind'] = 'tv series'
                series_secondary = movie.get('secondary_info')
                if series_secondary:
                    series.update(_parse_secondary_info(series_secondary))

                movie['episode of'] = series
                movie['link'] = episode['link']
                movie['title'] = episode['title']
                ep_secondary = episode.get('secondary_info')
                if ep_secondary is not None:
                    movie['secondary_info'] = ep_secondary

            secondary_info = movie.pop('secondary_info', None)
            if secondary_info is not None:
                secondary = _parse_secondary_info(secondary_info)
                movie.update(secondary)
                if episode is not None:
                    movie['kind'] = 'episode'

            result.append((analyze_imdbid(movie.pop('link')), movie))
            idx += 1
        data['data'] = result

        return data

    def add_refs(self, data):
        return data


_OBJECTS = {
    'search_movie_advanced_parser': ((DOMHTMLSearchMovieAdvancedParser,), None)
}
