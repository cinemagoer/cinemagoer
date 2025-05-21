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

import re

from . import jsel
from .piculet import Path, Rule, Rules, reducers
from .utils import DOMParserBase, analyze_imdbid, build_movie

# regular expression to match duration in the format like "1h 30m"
_re_duration = re.compile(r'(?:(\d+)h)?\s*(?:(\d+)?m)?')

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
    info = info or ''
    _certs = set(('pg-13', 'pg', 'r', 'g', 'nc-17', 'unrated', 'approved',
                 'not rated', 'm', 'x', 'tv-ma', 'tv-pg', 'tv-14', 'vm', 'vm-14',
                 'vm-18'))
    for item in info.strip().split('|'):
        item = item.strip()
        litem = item.lower()
        if item.isdigit():
            parsed['year'] = int(item)
        elif litem in _certs:
            parsed['certificates'] = item
        elif 'tv' in litem or 'series' in litem or 'episode' in litem or \
                'show' in litem or 'video' in litem or 'short' in litem:
            parsed['kind'] = _KIND_MAP.get(litem, litem)
        elif '–' in item or '-' in item:
            item = item.replace('–', '-')
            parsed['series years'] = item
        else:
            dg = _re_duration.match(item)
            duration = 0
            if dg:
                h, m = dg.groups()
                if h and h.isdigit():
                    duration += int(h) * 60
                if m and m.isdigit():
                    duration += int(m)
            if duration:
                parsed['runtimes'] = [duration]
    return parsed


def get_votes(votes):
    """Convert the votes string to an integer."""
    if votes:
        match = re.search(r'(\d+)', votes)
        if match:
            return int(match.group(1).replace(',', ''))
    return None


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
                        extractor=Path('.//span[contains(@class, "dli-title-metadata-item")]/text()',
                                       reduce=reducers.pipe_join)
                    ),
                    Rule(
                        key='kind',
                        extractor=Path('.//span[contains(@class, "dli-title-type-data")]/text()',
                                       reduce=reducers.first,
                                       transform=lambda x: _KIND_MAP.get(x.lower(), x.lower()))
                    ),
                    Rule(
                        key='genres',
                        extractor=Path('.//span[@class="genre"]/text()',
                                       reduce=reducers.first,
                                       transform=lambda s: [w.strip() for w in s.split(',')])
                    ),
                    Rule(
                        key='rating',
                        extractor=Path('.//span[contains(@class, "ipc-rating-star--rating")]/text()',
                                       reduce=reducers.first,
                                       transform=float)
                    ),
                    Rule(
                        key='votes',
                        extractor=Path('.//span[contains(@class, "ipc-rating-star--voteCount")]/text()',
                                       reduce=reducers.first,
                                       transform=get_votes)
                    ),
                    Rule(
                        key='metascore',
                        extractor=Path('.//span[contains(@class, "metacritic-score-box")]/text()',
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
                        extractor=Path('.//div[@role="presentation"][@class="ipc-html-content-inner-div"]/text()',
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
                                     extractor=Path('.//div[@ep-title]/a/@href', reduce=reducers.first)),
                                Rule(key='title',
                                     extractor=Path(
                                         './/div[@ep-title]/a/h3/text()',
                                         reduce=reducers.first,
                                         transform=cleanup_title
                                     )
                                ),
                                Rule(key='secondary_info',
                                     extractor=Path('.//span[@class="lister-item-year text-muted unbold"]/text()',  # noqa: E501
                                                    reduce=reducers.first)),
                            ]
                        )
                    )
                ]
            )
        ),
        Rule(
            key='__NEXT_DATA__',
            extractor=Path(
                '//script[@id="__NEXT_DATA__"]/text()',
                reduce=reducers.first,
                transform=lambda x: x.strip()
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
        jdata = None
        if '__NEXT_DATA__' in data:
            jdata = jsel.select(data['__NEXT_DATA__'], '.props.pageProps.searchResults.titleResults.titleListItems[]')
        for idx, movie in enumerate(data['data']):
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
            if jdata:
                movie_jdata = jsel.select(jdata, '.[%d]' % idx)
                if movie_jdata:
                    movie['genres'] = jsel.select(movie_jdata, '.genres[]')
            result.append((analyze_imdbid(movie.pop('link')), movie))
        data['data'] = result

        return data

    def add_refs(self, data):
        return data


_OBJECTS = {
    'search_movie_advanced_parser': ((DOMHTMLSearchMovieAdvancedParser,), None)
}
