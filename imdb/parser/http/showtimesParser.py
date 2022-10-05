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
the pages for the showtimes of movies near you.

Pages:

https://www.imdb.com/showtimes/
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from .piculet import Path, Rule, Rules
from .utils import DOMParserBase, analyze_imdbid, build_movie


class DOMHTMLMoviesNearYou(DOMParserBase):
    # foreach='//h3[@itemprop="name"]/a'
    rules = [
        Rule(
            foreach='//h3[@itemprop="name"]/a',
            key=Path('./text()'),
            extractor=Rules(
                foreach='//span[@itemprop="name"]/a',
                rules=[
                    Rule(        
                        key='movie',
                        extractor=Rules(
                            rules=[
                                Rule(
                                    key='link',
                                    extractor=Path("./@href")
                                ),
                                Rule(
                                    key='title',
                                    extractor=Path("./text()")
                                ),
                            ],
                            transform=lambda x: build_movie(x.get('title'), analyze_imdbid(x.get('link')))
                        )
                    ),
                    Rule(
                        key='showtimes',
                        extractor=Path(
                            './../../..//div[@class="showtimes"]//text()',
                            transform=lambda x: " ".join(x.replace("\n", "").strip().split())
                        )
                    )
                ],
            )
        ),
        Rule(
            key='num_cinemas',
            extractor=Path(
                '//ul[@class="list_tabs"]/li[2]/a/span/text()',
                transform=lambda x: int(x.replace('(', '').replace(')', '').strip())
            ),
        ),
        Rule(
            key='num_movies',
            extractor=Path(
                '//ul[@class="list_tabs"]/li[1]/a/span/text()',
                transform=lambda x: int(x.replace('(', '').replace(')', '').strip())
            ),
        )
    ]

_OBJECTS = {
    'showtime_parser': ((DOMHTMLMoviesNearYou,), None),
}
