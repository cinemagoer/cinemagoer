# Copyright 2009-2018 Davide Alberani <da@erlug.linux.it>
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

http://www.imdb.com/find?s=kw;mx=20;q=alabama
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from imdb.utils import analyze_title

from .piculet import Path, Rule, Rules
from .searchMovieParser import DOMHTMLSearchMovieParser
from .utils import analyze_imdbid


class DOMHTMLSearchKeywordParser(DOMHTMLSearchMovieParser):
    """Parse the html page that the IMDb web server shows when the
    "new search system" is used, searching for keywords similar to
    the one given."""
    _linkPrefix = '/keyword/'

    rules = [
        Rule(
            key='data',
            extractor=Path(
                foreach='//a[starts-with(@href, "/keyword/")]/..',
                path='./a[1]/text()'
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


class DOMHTMLSearchMovieKeywordParser(DOMHTMLSearchMovieParser):
    """Parse the html page that the IMDb web server shows when the
    "new search system" is used, searching for movies with the given
    keyword."""

    rules = [
        Rule(
            key='data',
            extractor=Rules(
                foreach='//div[@class="lister-list"]//h3//a[starts-with(@href, "/title/tt")]/..',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('./a[1]/@href')
                    ),
                    Rule(
                        key='info',
                        extractor=Path('./a[1]//text()')
                    ),
                    Rule(
                        key='ynote',
                        extractor=Path('./span[@class="lister-item-year text-muted unbold"]/text()')
                    ),
                    Rule(
                        key='outline',
                        extractor=Path('./span[@class="outline"]//text()')
                    )
                ],
                transform=lambda x: (
                    analyze_imdbid(x.get('link') or ''),
                    custom_analyze_title4kwd(x.get('info') or '',
                                             x.get('ynote') or '',
                                             x.get('outline') or '')
                )
            )
        )
    ]


_OBJECTS = {
    'search_keyword_parser': ((DOMHTMLSearchKeywordParser,), {'kind': 'keyword'}),
    'search_moviekeyword_parser': ((DOMHTMLSearchMovieKeywordParser,), None)
}
