"""
parser.http.searchMovieParser module (imdb package).

This module provides the HTMLSearchMovieParser class (and the
search_movie_parser instance), used to parse the results of a search
for a given title.
E.g., for when searching for the title "the passion", the parsed
page would be:
    http://www.imdb.com/find?q=the+passion&tt=on&mx=20

Copyright 2004-2018 Davide Alberani <da@erlug.linux.it>
               2008 H. Turgut Uyar <uyar@tekir.org>

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

from imdb.utils import analyze_title, build_title

from .utils import Attribute, DOMParserBase, Extractor, analyze_imdbid


def custom_analyze_title(title):
    """Remove garbage notes after the (year), (year/imdbIndex) or (year) (TV)"""
    # XXX: very crappy. :-(
    nt = title.split(' aka ')[0]
    if nt:
        title = nt
    if not title:
        return {}
    return analyze_title(title)


class DOMHTMLSearchMovieParser(DOMParserBase):
    """Parse the html page that the IMDb web server shows when the
    "new search system" is used, for movies."""

    _titleBuilder = lambda self, x: build_title(x)
    _linkPrefix = '/title/tt'

    _attrs = [
        Attribute(
            key='data',
            multi=True,
            path={
                'link': "./a[1]/@href",
                'info': ".//text()",
                'akas': "./i//text()"
            },
            postprocess=lambda x: (
                analyze_imdbid(x.get('link') or ''),
                custom_analyze_title(x.get('info') or ''),
                x.get('akas')
            )
        )
    ]

    extractors = [
        Extractor(
            label='search',
            path="//td[@class='result_text']",
            attrs=_attrs
        )
    ]

    def _init(self):
        self.url = ''

    def _reset(self):
        self.url = ''

    def postprocess_data(self, data):
        if 'data' not in data:
            data['data'] = []
        results = getattr(self, 'results', None)
        if results is not None:
            data['data'][:] = data['data'][:results]
        # Horrible hack to support AKAs.
        if data and data['data'] and len(data['data'][0]) == 3 and \
                isinstance(data['data'][0], tuple):
            data['data'] = [x for x in data['data'] if x[0] and x[1]]
            for idx, datum in enumerate(data['data']):
                if not isinstance(datum, tuple):
                    continue
                if not datum[0] and datum[1]:
                    continue
                if datum[2] is not None:
                    # akas = filter(None, datum[2].split('::'))
                    if self._linkPrefix == '/title/tt':
                        # XXX (HTU): couldn't find a result with multiple akas
                        aka = datum[2]
                        akas = [aka[1:-1]]      # remove the quotes
                        # akas = [a.replace('" - ', '::').rstrip() for a in akas]
                        # akas = [a.replace('aka "', '', 1).replace('aka  "',
                        #         '', 1).lstrip() for a in akas]
                    datum[1]['akas'] = akas
                    data['data'][idx] = (datum[0], datum[1])
                else:
                    data['data'][idx] = (datum[0], datum[1])
        return data

    def add_refs(self, data):
        return data


_OBJECTS = {
    'search_movie_parser': ((DOMHTMLSearchMovieParser,), None)
}
