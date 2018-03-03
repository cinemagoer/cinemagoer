"""
parser.http.personParser module (imdb package).

This module provides the classes (and the instances), used to parse
the IMDb pages on the www.imdb.com server about a person.
E.g., for "Mel Gibson" the referred pages would be:
    categorized:    http://www.imdb.com/name/nm0000154/maindetails
    biography:      http://www.imdb.com/name/nm0000154/bio
    ...and so on...

Copyright 2004-2018 Davide Alberani <da@erlug.linux.it>
          2008-2017 H. Turgut Uyar <uyar@tekir.org>

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

import re

from imdb.utils import analyze_name, canonicalName

from .movieParser import (
    DOMHTMLAwardsParser,
    DOMHTMLNewsParser,
    DOMHTMLOfficialsitesParser,
    DOMHTMLTechParser
)
from .utils import Attribute, DOMParserBase, Extractor, analyze_imdbid, build_movie


_re_spaces = re.compile(r'\s+')
_reRoles = re.compile(r'(<li>.*? \.\.\.\. )(.*?)(</li>|<br>)', re.I | re.M | re.S)


class DOMHTMLMaindetailsParser(DOMParserBase):
    """Parser for the "categorized" (maindetails) page of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        cparser = DOMHTMLMaindetailsParser()
        result = cparser.parse(categorized_html_string)
    """
    _containsObjects = True
    _name_imdb_index = re.compile(r'\([IVXLCDM]+\)')

    _birth_attrs = [
        Attribute(
            key='birth date',
            path='.//time[@itemprop="birthDate"]/@datetime'
        ),

        Attribute(
            key='birth place',
            path=".//a[starts-with(@href, '/search/name?birth_place=')]/text()"
        )
    ]

    _death_attrs = [
        Attribute(
            key='death date',
            path='.//time[@itemprop="deathDate"]/@datetime'
        ),

        Attribute(
            key='death place',
            path=".//a[starts-with(@href, '/search/name?death_place=')]/text()"
        )
    ]

    _film_attrs = [
        Attribute(
            key=None,
            multi=True,
            path={
                'link': "./b/a[1]/@href",
                'title': "./b/a[1]/text()",
                'notes': "./b/following-sibling::text()",
                'year': "./span[@class='year_column']/text()",
                'status': "./a[@class='in_production']/text()",
                'rolesNoChar': './/br/following-sibling::text()',
                'chrRoles': "./a[@imdbpyname]/@imdbpyname"
            },
            postprocess=lambda x: build_movie(
                x.get('title') or '',
                year=x.get('year'),
                movieID=analyze_imdbid(x.get('link') or ''),
                rolesNoChar=(x.get('rolesNoChar') or '').strip(),
                chrRoles=(x.get('chrRoles') or '').strip(),
                additionalNotes=x.get('notes'),
                status=x.get('status') or None
            )
        )
    ]

    extractors = [
        Extractor(
            label='name',
            path="//h1[@class='header']",
            attrs=Attribute(
                key='name',
                path=".//text()",
                postprocess=lambda x: analyze_name(x, canonical=1)
            )
        ),

        Extractor(
            label='name_index',
            path="//h1[@class='header']/span[1]",
            attrs=Attribute(
                key='name_index',
                path="./text()"
            )
        ),

        Extractor(
            label='birth info',
            path="//div[h4='Born:']",
            attrs=_birth_attrs
        ),

        Extractor(
            label='death info',
            path="//div[h4='Died:']",
            attrs=_death_attrs
        ),

        Extractor(
            label='headshot',
            path="//td[@id='img_primary']/div[@class='image']/a",
            attrs=Attribute(
                key='headshot',
                path="./img/@src"
            )
        ),

        Extractor(
            label='akas',
            path="//div[h4='Alternate Names:']",
            attrs=Attribute(
                key='akas',
                path="./text()",
                postprocess=lambda x: x.strip().split('  ')
            )
        ),

        Extractor(
            label='filmography',
            group="//div[starts-with(@id, 'filmo-head-')]",
            group_key="./a[@name]/text()",
            group_key_normalize=lambda x: x.lower().replace(': ', ' '),
            path="./following-sibling::div[1]/div[starts-with(@class, 'filmo-row')]",
            attrs=_film_attrs
        ),

        Extractor(
            label='indevelopment',
            path="//div[starts-with(@class,'devitem')]",
            attrs=Attribute(
                key='in development',
                multi=True,
                path={
                    'link': './a/@href',
                    'title': './a/text()'
                },
                postprocess=lambda x: build_movie(
                    x.get('title') or '',
                    movieID=analyze_imdbid(x.get('link') or ''),
                    roleID=(x.get('roleID') or '').split('/'),
                    status=x.get('status') or None
                )
            )
        )
    ]

    preprocessors = [
        ('<div class="clear"/> </div>', ''), ('<br/>', '<br />')
    ]

    def postprocess_data(self, data):
        for what in 'birth date', 'death date':
            if what in data and not data[what]:
                del data[what]
        name_index = (data.get('name_index') or '').strip()
        if name_index:
            if self._name_imdb_index.match(name_index):
                data['imdbIndex'] = name_index[1:-1]
            del data['name_index']
        # XXX: the code below is for backwards compatibility
        # probably could be removed
        for key in list(data.keys()):
            if key.startswith('actor '):
                if 'actor' not in data:
                    data['actor'] = []
                data['actor'].extend(data[key])
                del data[key]
            if key.startswith('actress '):
                if 'actress' not in data:
                    data['actress'] = []
                data['actress'].extend(data[key])
                del data[key]
            if key.startswith('self '):
                if 'self' not in data:
                    data['self'] = []
                data['self'].extend(data[key])
                del data[key]
            if key == 'birth place':
                data['birth notes'] = data[key]
                del data[key]
            if key == 'death place':
                data['death notes'] = data[key]
                del data[key]
        return data


class DOMHTMLBioParser(DOMParserBase):
    """Parser for the "biography" page of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        bioparser = DOMHTMLBioParser()
        result = bioparser.parse(biography_html_string)
    """
    _defGetRefs = True

    _birth_attrs = [
        Attribute(
            key='birth date',
            path="./time[@itemprop='birthDate']/@datetime"
        ),

        Attribute(
            key='birth notes',
            path="./a[starts-with(@href, '/search/name?birth_place=')]/text()"
        )
    ]

    _death_attrs = [
        Attribute(
            key='death date',
            path="./time[@itemprop='deathDate']/@datetime"
        ),

        Attribute(
            key='death cause',
            path="./text()",
            # TODO: check if this slicing is always correct
            postprocess=lambda x: ''.join(x).strip()[2:].lstrip()
        ),

        Attribute(
            key='death notes',
            path="..//text()",
            postprocess=lambda x: _re_spaces.sub(' ', (x or '').strip().split('\n')[-1])
        )
    ]

    extractors = [
        Extractor(
            label='headshot',
            path="//img[@class='poster']",
            attrs=Attribute(
                key='headshot',
                path="./@src"
            )
        ),

        Extractor(
            label='birth info',
            path="//table[@id='overviewTable']"
                 "//td[text()='Born']/following-sibling::td[1]",
            attrs=_birth_attrs
        ),

        Extractor(
            label='death info',
            path="//table[@id='overviewTable']"
                 "//td[text()='Died']/following-sibling::td[1]",
            attrs=_death_attrs
        ),

        Extractor(
            label='nick names',
            path="//table[@id='overviewTable']"
                 "//td[starts-with(text(), 'Nickname')]/following-sibling::td[1]",
            attrs=Attribute(
                key='nick names',
                path="./text()",
                joiner='|',
                postprocess=lambda x: [n.strip().replace(' (', '::(', 1) for n in x.split('|')
                                       if n.strip()]
            )
        ),

        Extractor(
            label='birth name',
            path="//table[@id='overviewTable']"
                 "//td[text()='Birth Name']/following-sibling::td[1]",
            attrs=Attribute(
                key='birth name',
                path="./text()",
                postprocess=lambda x: canonicalName(x.strip())
            )
        ),

        Extractor(
            label='height',
            path="//table[@id='overviewTable']//td[text()='Height']/following-sibling::td[1]",
            attrs=Attribute(
                key='height',
                path="./text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='mini biography',
            path="//a[@name='mini_bio']/following-sibling::"
                 "div[1 = count(preceding-sibling::a[1] | ../a[@name='mini_bio'])]",
            attrs=Attribute(
                key='mini biography',
                multi=True,
                path={
                    'bio': ".//text()",
                    'by': ".//a[@name='ba']//text()"
                },
                postprocess=lambda x: "%s::%s" % (
                    (x.get('bio') or '').split('- IMDb Mini Biography By:')[0].strip(),
                    (x.get('by') or '').strip() or 'Anonymous'
                )
            )
        ),

        Extractor(
            label='spouse',
            path="//a[@name='spouse']/following::table[1]//tr",
            attrs=Attribute(
                key='spouse',
                multi=True,
                path={
                    'name': "./td[1]//text()",
                    'info': "./td[2]//text()"
                },
                postprocess=lambda x: ("%s::%s" % (
                    x.get('name').strip(),
                    (_re_spaces.sub(' ', x.get('info') or '')).strip())).strip(':')
            )
        ),

        Extractor(
            label='trade mark',
            path="//div[@class='_imdbpyh4']/h4[starts-with(text(), 'Trade Mark')]" +
                    "/.././div[contains(@class, 'soda')]",
            attrs=Attribute(
                key='trade mark',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='trivia',
            path="//div[@class='_imdbpyh4']/h4[starts-with(text(), 'Trivia')]" +
                    "/.././div[contains(@class, 'soda')]",
            attrs=Attribute(
                key='trivia',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='quotes',
            path="//div[@class='_imdbpyh4']/h4[starts-with(text(), 'Personal Quotes')]" +
                    "/.././div[contains(@class, 'soda')]",
            attrs=Attribute(
                key='quotes',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='salary',
            path="//a[@name='salary']/following::table[1]//tr",
            attrs=Attribute(
                key='salary history',
                multi=True,
                path={
                    'title': "./td[1]//text()",
                    'info': "./td[2]//text()",
                },
                postprocess=lambda x: "%s::%s" % (
                    x.get('title').strip(),
                    _re_spaces.sub(' ', (x.get('info') or '')).strip())
            )
        )
    ]

    preprocessors = [
        (re.compile('(<h5>)', re.I), r'</div><div class="_imdbpy">\1'),
        (re.compile('(<h4)', re.I), r'</div><div class="_imdbpyh4">\1'),
        (re.compile('(</table>\n</div>\s+)</div>', re.I + re.DOTALL), r'\1'),
        (re.compile('(<div id="tn15bot">)'), r'</div>\1'),
        (re.compile('\.<br><br>([^\s])', re.I), r'. \1')
    ]

    def postprocess_data(self, data):
        for what in 'birth date', 'death date', 'death cause':
            if what in data and not data[what]:
                del data[what]
        return data


class DOMHTMLOtherWorksParser(DOMParserBase):
    """Parser for the "other works" page of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        owparser = DOMHTMLOtherWorksParser()
        result = owparser.parse(otherworks_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='other works',
            path="//li[@class='ipl-zebra-list__item']",
            attrs=Attribute(
                key='other works',
                path=".//text()",
                multi=True,
                postprocess=lambda x: x.strip()
            )
        )
    ]


class DOMHTMLPersonGenresParser(DOMParserBase):
    """Parser for the "by genre" and "by keywords" pages of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = DOMHTMLPersonGenresParser()
        result = gparser.parse(bygenre_html_string)
    """
    kind = 'genres'
    _containsObjects = True

    extractors = [
        Extractor(
            label='genres',
            group="//b/a[@name]/following-sibling::a[1]",
            group_key="./text()",
            group_key_normalize=lambda x: x.lower(),
            path="../../following-sibling::ol[1]/li//a[1]",
            attrs=Attribute(
                key=None,
                multi=True,
                path={
                    'link': "./@href",
                    'title': "./text()",
                    'info': "./following-sibling::text()"
                },
                postprocess=lambda x: build_movie(
                    x.get('title') + x.get('info').split('[')[0],
                    analyze_imdbid(x.get('link')))
            )
        )
    ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        return {self.kind: data}


_OBJECTS = {
    'maindetails_parser': ((DOMHTMLMaindetailsParser,), None),
    'bio_parser': ((DOMHTMLBioParser,), None),
    'otherworks_parser': ((DOMHTMLOtherWorksParser,), None),
    'person_officialsites_parser': ((DOMHTMLOfficialsitesParser,), None),
    'person_awards_parser': ((DOMHTMLAwardsParser,), {'subject': 'name'}),
    'publicity_parser': ((DOMHTMLTechParser,), {'kind': 'publicity'}),
    'person_contacts_parser': ((DOMHTMLTechParser,), {'kind': 'contacts'}),
    'person_genres_parser': ((DOMHTMLPersonGenresParser,), None),
    'person_keywords_parser': ((DOMHTMLPersonGenresParser,), {'kind': 'keywords'}),
    'news_parser': ((DOMHTMLNewsParser,), None),
}
