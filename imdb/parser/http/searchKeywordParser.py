# Copyright 2009-2022 Davide Alberani <da@erlug.linux.it>
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
the results of a search for a given keyword.

For example, when searching for the keyword "alabama", the parsed page
would be:

http://www.imdb.com/find?q=alabama&s=kw
"""

from imdb.utils import analyze_title

from . import jsel
from .piculet import Path, Rule, Rules, reducers
from .searchMovieParser import DOMHTMLSearchMovieParser
from .utils import analyze_imdbid


class DOMHTMLSearchKeywordParser(DOMHTMLSearchMovieParser):
    """A parser for the keyword search page."""

    rules = [
        Rule(
            key='data',
            extractor=Path(
                foreach='//li[contains(@class, "find-keyword-result")]',
                path='.//a[@class="ipc-metadata-list-summary-item__t"]/text()'
            )
        )
    ]


def custom_analyze_title4kwd(title, yearNote, outline):
    """Return a dictionary with the needed info."""
    title = title.strip()
    if not title:
        return {}
    if yearNote:
        yearNote = '%s)' % yearNote.split(' ')[0]
        title = title + ' ' + yearNote
    retDict = analyze_title(title)
    if outline:
        retDict['plot outline'] = outline
    return retDict


# Map IMDB title type IDs to cinemagoer kind values
_KIND_MAP = {
    'movie': 'movie',
    'tvSeries': 'tv series',
    'tvMiniSeries': 'tv mini series',
    'tvMovie': 'tv movie',
    'tvSpecial': 'tv special',
    'tvShort': 'tv short movie',
    'video': 'video movie',
    'videoGame': 'video game',
    'short': 'short',
    'tvEpisode': 'episode',
    'tvPilot': 'tv pilot',
    'podcastSeries': 'podcast series',
    'podcastEpisode': 'podcast episode',
    'musicVideo': 'music video',
}


class DOMHTMLSearchMovieKeywordParser(DOMHTMLSearchMovieParser):
    """A parser for the movie search by keyword page."""

    rules = [
        Rule(
            key='data',
            extractor=Rules(
                foreach='//li[contains(@class, "ipc-metadata-list-summary-item")]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('.//a[contains(@class, "ipc-title-link-wrapper")]/@href',
                                       reduce=reducers.first)
                    ),
                    Rule(
                        key='title',
                        extractor=Path('.//a[contains(@class, "ipc-title-link-wrapper")]/h3/text()',
                                       reduce=reducers.first)
                    ),
                ],
                transform=lambda x: (
                    analyze_imdbid(x.get('link')),
                    {'title': x.get('title', '').strip()}
                )
            )
        ),
        Rule(
            key='__NEXT_DATA__',
            extractor=Path(
                '//script[@id="__NEXT_DATA__"]/text()',
                reduce=reducers.first,
                transform=lambda x: x.strip() if x else None
            )
        )
    ]

    def postprocess_data(self, data):
        """Process data, preferring JSON from __NEXT_DATA__ when available."""
        results = getattr(self, 'results', None)
        result = []

        # Prefer JSON data from __NEXT_DATA__
        if '__NEXT_DATA__' in data and data['__NEXT_DATA__']:
            jdata = jsel.select(data['__NEXT_DATA__'],
                               '.props.pageProps.searchResults.titleResults.titleListItems[]')
            if jdata:
                for item in jdata:
                    movie = self._parse_json_item(item)
                    if movie:
                        movie_id = movie.pop('movieID', None)
                        if movie_id:
                            result.append((movie_id, movie))
        else:
            # Fallback to HTML-based data
            result = data.get('data', [])

        # Limit results if specified
        if results is not None:
            result = result[:results]

        data['data'] = result
        return data

    def _parse_json_item(self, item):
        """Parse a single item from __NEXT_DATA__ JSON."""
        if not item:
            return None

        movie = {}

        # Movie ID
        title_id = item.get('titleId', '')
        if title_id.startswith('tt'):
            movie['movieID'] = title_id[2:]
        else:
            movie['movieID'] = title_id

        # Title
        movie['title'] = item.get('titleText') or item.get('originalTitleText', '')

        # Year
        year = item.get('releaseYear')
        if year:
            movie['year'] = year

        # Kind
        title_type = item.get('titleType', {})
        kind_id = title_type.get('id', '')
        movie['kind'] = _KIND_MAP.get(kind_id, kind_id)

        return movie

    def preprocess_string(self, html_string):
        return html_string.replace(' + >', '>')


_OBJECTS = {
    'search_keyword_parser': ((DOMHTMLSearchKeywordParser,), {'kind': 'keyword'}),
    'search_moviekeyword_parser': ((DOMHTMLSearchMovieKeywordParser,), None)
}
