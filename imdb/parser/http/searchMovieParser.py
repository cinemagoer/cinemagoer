# Copyright 2004-2022 Davide Alberani <da@erlug.linux.it>
#           2008-2018 H. Turgut Uyar <uyar@tekir.org>
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
the results of a search for a given title.

For example, when searching for the title "the passion", the parsed page
would be:

http://www.imdb.com/find?q=the+passion&s=tt
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from imdb.utils import analyze_title, re_m_kind

from .piculet import Path, Rule, Rules, reducers
from .utils import DOMParserBase, analyze_imdbid


def process_title(tdict):
    """Process parsed data and build a tuple that
    can be used to create a list of results."""
    imdbid = analyze_imdbid(tdict.get('link'))
    title = tdict.get('title', '').strip()
    kind = (tdict.get('kind') or '').strip()
    if not re_m_kind.match('(%s)' % kind):
        kind = ''
    year = (tdict.get('year') or '').strip()
    if year:
        title += ' (%s)' % year
    if kind:
        title += ' (%s)' % kind
    if title:
        analized_title = analyze_title(title)
    else:
        analized_title = {}
    akas = tdict.get('akas')
    cover = tdict.get('cover url')
    return imdbid, analized_title, akas, cover


class DOMHTMLSearchMovieParser(DOMParserBase):
    """A parser for the title search page."""

    rules = [
        Rule(
            key='data',
            extractor=Rules(
                foreach='//li[contains(@class, "find-title-result")]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('.//a[@class="ipc-metadata-list-summary-item__t"]/@href',
                                       reduce=reducers.first)
                    ),
                    Rule(
                        key='title',
                        extractor=Path('.//a[@class="ipc-metadata-list-summary-item__t"]/text()')
                    ),
                    Rule(
                        key='year',
                        extractor=Path('.//span[@class="ipc-metadata-list-summary-item__li"]/text()',
                                       reduce=reducers.first)
                    ),
                    Rule(
                        key='kind',
                        extractor=Path('(.//span[@class="ipc-metadata-list-summary-item__li"])[2]/text()')
                    ),
                    Rule(
                        key='cover url',
                        extractor=Path('.//img[@class="ipc-image"]/@src')
                    )
                ],
                transform=process_title
            )
        )
    ]

    def _init(self):
        self.url = ''
        self.img_type = 'cover url'

    def _reset(self):
        self.url = ''

    def postprocess_data(self, data):
        if 'data' not in data:
            return {'data': []}
        results = getattr(self, 'results', None)
        if results is not None:
            data['data'][:] = data['data'][:results]
        # Horrible hack to support AKAs.
            data['data'] = [x for x in data['data'] if x[0] and x[1]]
        if data and data['data'] and len(data['data'][0]) == 4 and isinstance(data['data'][0], tuple):
            for idx, datum in enumerate(data['data']):
                if not isinstance(datum, tuple):
                    continue
                if not datum[0] and datum[1]:
                    continue
                if datum[2] is not None:
                    akas = [aka[1:-1] for aka in datum[2]]  # remove the quotes
                    datum[1]['akas'] = akas
                if datum[3] is not None:
                    datum[1][self.img_type] = datum[3]
                data['data'][idx] = (datum[0], datum[1])
        return data

    def add_refs(self, data):
        return data


_OBJECTS = {
    'search_movie_parser': ((DOMHTMLSearchMovieParser,), None)
}
