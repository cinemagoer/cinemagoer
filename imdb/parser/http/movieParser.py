# Copyright 2004-2025 Davide Alberani <da@erlug.linux.it>
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
the IMDb pages on the www.imdb.com server about a movie.

For example, for Brian De Palma's "The Untouchables", the referred pages
would be:

combined details
    http://www.imdb.com/title/tt0094226/reference

plot summary
    http://www.imdb.com/title/tt0094226/plotsummary

...and so on.
"""

import functools
import re
from urllib.parse import unquote

from imdb import imdbURL_base
from imdb.Company import Company
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import KIND_MAP, _Container

from .piculet import Path, Rule, Rules, preprocessors, transformers
from .utils import DOMParserBase, analyze_imdbid, build_movie, build_person

# Dictionary used to convert some section's names.
_SECT_CONV = {
    'directed': 'director',
    'directed by': 'director',
    'directors': 'director',
    'editors': 'editor',
    'writing credits': 'writer',
    'writers': 'writer',
    'produced': 'producer',
    'cinematography': 'cinematographer',
    'film editing': 'editor',
    'casting': 'casting director',
    'costume design': 'costume designer',
    'makeup department': 'make up',
    'production management': 'production manager',
    'second unit director or assistant director': 'assistant director',
    'costume and wardrobe department': 'costume department',
    'costume departmen': 'costume department',
    'sound department': 'sound crew',
    'stunts': 'stunt performer',
    'other crew': 'miscellaneous crew',
    'also known as': 'akas',
    'country': 'countries',
    'runtime': 'runtimes',
    'language': 'languages',
    'certification': 'certificates',
    'genre': 'genres',
    'created': 'creator',
    'creators': 'creator',
    'color': 'color info',
    'plot': 'plot outline',
    'art director': 'art direction',
    'art directors': 'art direction',
    'composers': 'composer',
    'assistant directors': 'assistant director',
    'set decorator': 'set decoration',
    'set decorators': 'set decoration',
    'visual effects department': 'visual effects',
    'miscellaneous': 'miscellaneous crew',
    'make up department': 'make up',
    'plot summary': 'plot outline',
    'cinematographers': 'cinematographer',
    'camera department': 'camera and electrical department',
    'costume designers': 'costume designer',
    'production designer': 'production design',
    'production designers': 'production design',
    'production managers': 'production manager',
    'music original': 'original music',
    'casting directors': 'casting director',
    'other companies': 'miscellaneous companies',
    'producers': 'producer',
    'special effects by': 'special effects department',
}

re_space = re.compile(r'\s+')


def clean_section_name(section):
    """Clean and replace some section names."""
    section = re_space.sub(' ', section.replace('_', ' ').strip().lower())
    if section.endswith(' by'):
        section = section[:-3]
    return _SECT_CONV.get(section, section)


def _manageRoles(mo):
    """Perform some transformation on the html, so that roleIDs can
    be easily retrieved."""
    firstHalf = mo.group(1)
    secondHalf = mo.group(2)
    newRoles = []
    roles = secondHalf.split(' / ')
    for role in roles:
        role = role.strip()
        if not role:
            continue
        roleID = analyze_imdbid(role)
        if roleID is None:
            roleID = '/'
        else:
            roleID += '/'
        newRoles.append('<div class="_imdbpyrole" roleid="%s">%s</div>' % (
            roleID, role.strip()
        ))
    return firstHalf + ' / '.join(newRoles) + mo.group(3)


_reRolesMovie = re.compile(r'(<td class="character">)(.*?)(</td>)', re.I | re.M | re.S)


def makeSplitter(lstrip=None, sep='|', comments=True,
                 origNotesSep=' (', newNotesSep='::(', strip=None):
    """Return a splitter function suitable for a given set of data."""

    def splitter(x):
        if not x:
            return x
        x = x.strip()
        if not x:
            return x
        if lstrip is not None:
            x = x.lstrip(lstrip).lstrip()
        lx = x.split(sep)
        lx[:] = [_f for _f in [j.strip() for j in lx] if _f]
        if comments:
            lx[:] = [j.replace(origNotesSep, newNotesSep, 1) for j in lx]
        if strip:
            lx[:] = [j.strip(strip) for j in lx]
        return lx

    return splitter


def _toInt(val, replace=()):
    """Return the value, converted to integer, or None; if present, 'replace'
    must be a list of tuples of values to replace."""
    for before, after in replace:
        val = val.replace(before, after)
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


_re_og_title = re.compile(
    r'(.*) \((?:(?:(.+)(?= ))? ?(\d{4})(?:(–)(\d{4}| ))?|(.+))\)',
    re.UNICODE
)


def special_kind(og_title):
    specialKind = re.compile(r"\n(.*)").findall(og_title)
    if len(specialKind):
        return specialKind[0].strip()
    return None


def analyze_og_title(og_title):
    data = {}
    og_kind = special_kind(og_title)
    match = _re_og_title.match(og_title)
    if og_title and not match:
        # assume it's a title in production, missing release date information
        return {'title': og_title}
    data['title'] = match.group(1)
    if match.group(3):
        data['year'] = int(match.group(3))
    kind = match.group(2) or match.group(6)
    if kind is None:
        if og_kind is None:
            kind = 'movie'
        else:
            kind = og_kind.lower()
    else:
        kind = kind.lower()
        kind = KIND_MAP.get(kind, kind)
    data['kind'] = kind
    year_separator = match.group(4)
    # There is a year separator so assume an ongoing or ended series
    if year_separator is not None:
        end_year = match.group(5)
        if end_year is not None:
            data['series years'] = '%(year)d-%(end_year)s' % {
                'year': data['year'],
                'end_year': end_year.strip(),
            }
        elif kind.endswith('series'):
            data['series years'] = '%(year)d-' % {'year': data['year']}
    # No year separator and series, so assume that it ended the same year
    elif kind.endswith('series') and 'year' in data:
        data['series years'] = '%(year)d-%(year)d' % {'year': data['year']}

    if data['kind'] == 'episode' and data['title'][0] == '"':
        quote_end = data['title'].find('"', 1)
        data['tv series title'] = data['title'][1:quote_end]
        data['title'] = data['title'][quote_end + 1:].strip()
    return data


def analyze_certificates(certificates):
    def reducer(acc, el):
        cert_re = re.compile(r'^(.+):(.+)$', re.UNICODE)

        if cert_re.match(el):
            acc.append(el)
        elif acc:
            acc[-1] = u'{}::{}'.format(
                acc[-1],
                el,
            )
        return acc

    certificates = [el.strip() for el in certificates.split('\n') if el.strip()]
    return functools.reduce(reducer, certificates, [])


def clean_akas(aka):
    aka = re_space.sub(' ', aka).strip()
    if aka.lower().startswith('see more'):
        aka = ''
    return aka


class DOMHTMLMovieParser(DOMParserBase):
    """Parser for the "reference" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        mparser = DOMHTMLMovieParser()
        result = mparser.parse(reference_html_string)
    """
    _containsObjects = True

    rules = [
        Rule(
            key='title',
            extractor=Path('//meta[@property="og:title"]/@content|//*[@id="main"]/section/div/div/ul[1]/li[5]/text()',
                           transform=analyze_og_title)
        ),
        Rule(
            key='alternative kind',
            extractor=Path('//h3[@itemprop="name"]/following-sibling::ul/li[last()]/text()',
                           transform=lambda x: KIND_MAP.get(x.strip().lower(), x.strip().lower()))
        ),
        Rule(
            key='original title',
            extractor=Path('//div[@class="titlereference-header"]//span[@class="titlereference-original-title-label"]/preceding-sibling::text()',  # noqa: E501
                           transform=lambda x: re_space.sub(' ', x).strip())

        ),
        Rule(
            key='original title title-year',
            extractor=Path('//div[@class="titlereference-header"]//span[@class="titlereference-title-year"]/preceding-sibling::text()',  # noqa: E501
                           transform=lambda x: re_space.sub(' ', x).strip())
        ),
        Rule(
            key='localized title',
            extractor=Path('//meta[@name="title"]/@content',
                           transform=lambda x: analyze_og_title(x).get('title'))
        ),
        Rule(
            key="stars",
            extractor=Path(
                foreach='//div[@class="titlereference-overview-section" and '
                        'contains(text(), "Stars:")]/ul/li[1]/a',
                path='./text()')
        ),

        # parser for misc sections like 'casting department', 'stunts', ...
        Rule(
            key='misc sections',
            extractor=Rules(
                foreach='//h4[contains(@class, "ipl-header__content")]',
                rules=[
                    Rule(
                        key=Path('./@name', transform=clean_section_name),
                        extractor=Rules(
                            foreach='../../following-sibling::table[1]//tr',
                            rules=[
                                Rule(
                                    key='person',
                                    extractor=Path('.//text()')
                                ),
                                Rule(
                                    key='link',
                                    extractor=Path('./td[1]/a[@href]/@href')
                                )
                            ],
                            transform=lambda x: build_person(
                                x.get('person') or '',
                                personID=analyze_imdbid(x.get('link'))
                            )
                        )
                    )
                ]
            )
        ),
        Rule(
            key='cast',
            extractor=Rules(
                foreach='//table[@class="cast_list"]//tr',
                rules=[
                    Rule(
                        key='person',
                        extractor=Path('.//text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('./td[2]/a/@href')
                    ),
                    Rule(
                        key='roleID',
                        extractor=Path('./td[4]//div[@class="_imdbpyrole"]/@roleid')
                    )
                ],
                transform=lambda x: build_person(
                    x.get('person') or '',
                    personID=analyze_imdbid(x.get('link')),
                    roleID=(x.get('roleID') or '').split('/')
                )
            )
        ),
        Rule(
            key='recommendations',
            extractor=Rules(
                foreach='//div[contains(@class, "rec_item")]',
                rules=[
                    Rule(
                        key='movieID',
                        extractor=Path(
                            './@data-tconst',
                            transform=lambda x: (x or '').replace('tt', '')
                        )
                    ),
                    Rule(
                        key='title',
                        extractor=Path(
                            './/a//img/@title',
                            transform=lambda x: re_space.sub(' ', x or '').strip()
                        )
                    ),
                ],
                transform=lambda x: build_movie(x.get('title', ''), movieID=x.get('movieID'))
            )
        ),
        Rule(
            key='myrating',
            extractor=Path('//span[@id="voteuser"]//text()')
        ),
        Rule(
            key='plot summary',
            extractor=Path('//td[starts-with(text(), "Plot")]/..//p/text()',
                           transform=lambda x: x.strip().rstrip('|').rstrip())
        ),
        Rule(
            key='genres',
            extractor=Path(
                foreach='//td[starts-with(text(), "Genre")]/..//li/a',
                path='./text()'
            )
        ),
        Rule(
            key='runtimes',
            extractor=Path(
                foreach='//td[starts-with(text(), "Runtime")]/..//li',
                path='./text()',
                transform=lambda x: x.strip().replace(' min', '')
            )
        ),
        Rule(
            key='countries',
            extractor=Path(
                foreach='//td[starts-with(text(), "Countr")]/..//li/a',
                path='./text()'
            )
        ),
        Rule(
            key='country codes',
            extractor=Path(
                foreach='//td[starts-with(text(), "Countr")]/..//li/a',
                path='./@href',
                transform=lambda x: x.split('/')[2].strip().lower()
            )
        ),
        Rule(
            key='language',
            extractor=Path(
                foreach='//td[starts-with(text(), "Language")]/..//li/a',
                path='./text()'
            )
        ),
        Rule(
            key='language codes',
            extractor=Path(
                foreach='//td[starts-with(text(), "Language")]/..//li/a',
                path='./@href',
                transform=lambda x: x.split('/')[2].strip()
            )
        ),
        Rule(
            key='color info',
            extractor=Path(
                foreach='//td[starts-with(text(), "Color")]/..//li/a',
                path='./text()',
                transform=lambda x: x.replace(' (', '::(')
            )
        ),
        Rule(
            key='aspect ratio',
            extractor=Path(
                '//td[starts-with(text(), "Aspect")]/..//li/text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='sound mix',
            extractor=Path(
                foreach='//td[starts-with(text(), "Sound Mix")]/..//li/a',
                path='./text()',
                transform=lambda x: x.replace(' (', '::(')
            )
        ),
        Rule(
            key='box office',
            extractor=Rules(
                foreach='//section[contains(@class, "titlereference-section-box-office")]'
                        '//table[contains(@class, "titlereference-list")]//tr',
                rules=[
                    Rule(
                        key='box_office_title',
                        extractor=Path('./td[1]/text()')
                    ),
                    Rule(
                        key='box_office_detail',
                        extractor=Path('./td[2]/text()')
                    )
                ],
                transform=lambda x: (x['box_office_title'].strip(),
                                     x['box_office_detail'].strip())
            ),
        ),
        Rule(
            key='certificates',
            extractor=Path(
                '//td[starts-with(text(), "Certificat")]/..//text()',
                transform=analyze_certificates
            )
        ),
        # Collects akas not encosed in <i> tags.
        Rule(
            key='other akas',
            extractor=Path(
                foreach='//section[contains(@class, "listo")]//td[starts-with(text(), "Also Known As")]/..//ul/li',
                path='.//text()',
                transform=clean_akas
            )
        ),
        Rule(
            key='creator',
            extractor=Rules(
                foreach='//div[starts-with(normalize-space(text()), "Creator")]/ul/li[1]/a',
                rules=[
                    Rule(
                        key='name',
                        extractor=Path('./text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('./@href')
                    )
                ],
                transform=lambda x: build_person(
                    x.get('name') or '',
                    personID=analyze_imdbid(x.get('link'))
                )
            )
        ),
        Rule(
            key='thin writer',
            extractor=Rules(
                foreach='//div[starts-with(normalize-space(text()), "Writer")]/ul/li[1]/a',
                rules=[
                    Rule(
                        key='name',
                        extractor=Path('./text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('./@href')
                    )
                ],
                transform=lambda x: build_person(
                    x.get('name') or '',
                    personID=analyze_imdbid(x.get('link'))
                )
            )
        ),
        Rule(
            key='thin director',
            extractor=Rules(
                foreach='//div[starts-with(normalize-space(text()), "Director")]/ul/li[1]/a',
                rules=[
                    Rule(
                        key='name',
                        extractor=Path('./text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('./@href')
                    )
                ],
                transform=lambda x: build_person(
                    x.get('name') or '',
                    personID=analyze_imdbid(x.get('link'))
                )
            )
        ),
        Rule(
            key='top/bottom rank',
            extractor=Path(
                '//li[@class="ipl-inline-list__item"]//a[starts-with(@href, "/chart/")]/text()'
            )
        ),
        Rule(
            key='original air date',
            extractor=Path('//span[@imdbpy="airdate"]/text()')
        ),
        Rule(
            key='series years',
            extractor=Path(
                '//div[@id="tn15title"]//span[starts-with(text(), "TV series")]/text()',
                transform=lambda x: x.replace('TV series', '').strip()
            )
        ),
        Rule(
            key='season/episode',
            extractor=Path(
                '//div[@class="titlereference-overview-season-episode-section"]/ul//text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='number of episodes',
            extractor=Path(
                '//a[starts-with(text(), "All Episodes")]/text()',
                transform=lambda x: int(x.replace('All Episodes', '').strip()[1:-1])
            )
        ),
        Rule(
            key='episode number',
            extractor=Path(
                '//div[@id="tn15epnav"]/text()',
                transform=lambda x: int(re.sub(r'[^a-z0-9 ]', '',
                                               x.lower()).strip().split()[0]))
        ),
        Rule(
            key='previous episode',
            extractor=Path(
                '//span[@class="titlereference-overview-episodes-links"]'
                '//a[contains(text(), "Previous")]/@href',
                transform=analyze_imdbid
            )
        ),
        Rule(
            key='next episode',
            extractor=Path(
                '//span[@class="titlereference-overview-episodes-links"]'
                '//a[contains(text(), "Next")]/@href',
                transform=analyze_imdbid
            )
        ),
        Rule(
            key='number of seasons',
            extractor=Path(
                '//span[@class="titlereference-overview-years-links"]/../a[1]/text()',
                transform=int
            )
        ),
        Rule(
            key='tv series link',
            extractor=Path('//a[starts-with(text(), "All Episodes")]/@href')
        ),
        Rule(
            key='akas',
            extractor=Path(
                foreach='//i[@class="transl"]',
                path='./text()',
                transform=lambda x: x.replace('  ', ' ')
                                     .rstrip('-')
                                     .replace('" - ', '"::', 1)
                                     .strip('"')
                                     .replace('  ', ' ')
            )
        ),
        Rule(
            key='production status',
            extractor=Path(
                '//td[starts-with(text(), "Status:")]/../td[2]/text()',
                transform=lambda x: x.strip().split('|')[0].strip().lower()
            )
        ),
        Rule(
            key='production status updated',
            extractor=Path(
                '//td[starts-with(text(), "Status Updated:")]/'
                '..//td[2]/text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='production comments',
            extractor=Path(
                '//td[starts-with(text(), "Comments:")]/'
                '..//td[2]/text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='production note',
            extractor=Path(
                '//td[starts-with(text(), "Note:")]/'
                '..//td[2]/text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='companies',
            extractor=Rules(
                foreach="//ul[@class='simpleList']",
                rules=[
                    Rule(
                        key=Path('preceding-sibling::header[1]/div/h4/text()', transform=transformers.lower),
                        extractor=Rules(
                            foreach='./li',
                            rules=[
                                Rule(
                                    key='name',
                                    extractor=Path('./a//text()')
                                ),
                                Rule(
                                    key='comp-link',
                                    extractor=Path('./a/@href')
                                ),
                                Rule(
                                    key='notes',
                                    extractor=Path('./text()')
                                )
                            ],
                            transform=lambda x: Company(
                                name=x.get('name') or '',
                                accessSystem='http',
                                companyID=analyze_imdbid(x.get('comp-link')),
                                notes=(x.get('notes') or '').strip()
                            )
                        )
                    )
                ]
            )
        ),
        Rule(
            key='rating',
            extractor=Path('(//span[@class="ipl-rating-star__rating"])[1]/text()')
        ),
        Rule(
            key='votes',
            extractor=Path('//span[@class="ipl-rating-star__total-votes"][1]/text()')
        ),
        Rule(
            key='cover url',
            extractor=Path('//img[@alt="Poster"]/@src')
        ),
        Rule(
            key='imdbID',
            extractor=Path('//meta[@property="pageId"]/@content',
                           transform=lambda x: (x or '').replace('tt', ''))
        ),
        Rule(
            key='videos',
            extractor=Path(foreach='//div[@class="mediastrip_big"]//a',
                           path='./@href', transform=lambda x: 'http://www.imdb.com' + x)
        )
    ]

    preprocessors = [
        ('/releaseinfo">', '"><span imdbpy="airdate">'),
        (re.compile(r'(<b class="blackcatheader">.+?</b>)', re.I), r'</div><div>\1'),
        ('<small>Full cast and crew for<br>', ''),
        ('<td> </td>', '<td>...</td>'),
        (re.compile(r'<span class="tv-extra">TV mini-series(\s+.*?)</span>', re.I),
         r'<span class="tv-extra">TV series\1</span> (mini)'),
        (_reRolesMovie, _manageRoles)
    ]

    def preprocess_dom(self, dom):
        # Handle series information.
        xpath = self.xpath(dom, "//b[text()='Series Crew']")
        if xpath:
            b = xpath[-1]  # In doubt, take the last one.
            for a in self.xpath(b, "./following::h5/a[@class='glossary']"):
                name = a.get('name')
                if name:
                    a.set('name', 'series %s' % name)
        # Remove links to IMDbPro.
        preprocessors.remove(dom, '//span[@class="pro-link"]')
        # Remove some 'more' links (keep others, like the one around
        # the number of votes).
        preprocessors.remove(dom, '//a[@class="tn15more"][starts-with(@href, "/title/")]')
        # Remove the "rest of list" in cast.
        preprocessors.remove(dom, '//td[@colspan="4"]/..')
        return dom

    re_space = re.compile(r'\s+')
    re_airdate = re.compile(r'(.*)\s*\(season (\d+), episode (\d+)\)', re.I)

    def postprocess_data(self, data):
        # Convert section names.
        for sect in list(data.keys()):
            if sect in _SECT_CONV:
                data[_SECT_CONV[sect]] = data[sect]
                del data[sect]
        # Filter out fake values.
        for key in data:
            value = data[key]
            if isinstance(value, list) and value:
                if isinstance(value[0], Person):
                    data[key] = [x for x in value if x.personID is not None]
                if isinstance(value[0], _Container):
                    for obj in data[key]:
                        obj.accessSystem = self._as
                        obj.modFunct = self._modFunct
        for key in ['title']:
            if (key in data) and isinstance(data[key], dict):
                subdata = data[key]
                del data[key]
                data.update(subdata)
        if not data.get('original title'):
            if 'original title title-year' in data:
                data['original title'] = data['original title title-year']
                del data['original title title-year']
        elif 'original title title-year' in data:
            del data['original title title-year']
        misc_sections = data.get('misc sections')
        if misc_sections is not None:
            for section in misc_sections:
                # skip sections with their own parsers
                if 'cast' in section.keys():
                    continue
                data.update(section)
            del data['misc sections']
        if 'akas' in data or 'other akas' in data:
            akas = data.get('akas') or []
            other_akas = data.get('other akas') or []
            akas += other_akas
            nakas = []
            for aka in akas:
                aka = aka.strip()
                if not aka:
                    continue
                if aka.endswith('" -'):
                    aka = aka[:-3].rstrip()
                nakas.append(aka)
            if 'akas' in data:
                del data['akas']
            if 'other akas' in data:
                del data['other akas']
            if nakas:
                data['akas'] = nakas
        if 'runtimes' in data:
            data['runtimes'] = [x.replace(' min', '')
                                for x in data['runtimes']]
        if 'number of seasons' in data:
            data['seasons'] = [str(i) for i in range(1, data['number of seasons'] + 1)]
        if 'season/episode' in data:
            tokens = data['season/episode'].split('Episode')
            try:
                data['season'] = int(tokens[0].split('Season')[1])
            except Exception:
                data['season'] = 'unknown'
            try:
                data['episode'] = int(tokens[1])
            except Exception:
                data['episode'] = 'unknown'
            del data['season/episode']
        for k in ('writer', 'director'):
            t_k = 'thin %s' % k
            if t_k not in data:
                continue
            if k not in data:
                data[k] = data[t_k]
            del data[t_k]
        if 'top/bottom rank' in data:
            tbVal = data['top/bottom rank'].lower()
            if tbVal.startswith('top'):
                tbKey = 'top 250 rank'
                tbVal = _toInt(tbVal, [('top rated movies: #', '')])
            else:
                tbKey = 'bottom 100 rank'
                tbVal = _toInt(tbVal, [('bottom rated movies: #', '')])
            if tbVal:
                data[tbKey] = tbVal
            del data['top/bottom rank']
        if 'year' in data and data['year'] == '????':
            del data['year']
        if 'tv series link' in data:
            if 'tv series title' in data:
                data['episode of'] = Movie(title=data['tv series title'],
                                           movieID=analyze_imdbid(data['tv series link']),
                                           accessSystem=self._as,
                                           modFunct=self._modFunct)
                data['episode of']['kind'] = 'tv series'
                del data['tv series title']
            del data['tv series link']
        if 'rating' in data:
            try:
                data['rating'] = float(data['rating'].replace('/10', '').replace(',', '.'))
            except (TypeError, ValueError):
                pass
            if data['rating'] == 0:
                del data['rating']
        if 'votes' in data:
            try:
                votes = data['votes'].replace('(', '').replace(')', '').replace(',', '').replace('votes', '')
                data['votes'] = int(votes)
            except (TypeError, ValueError):
                pass
        companies = data.get('companies')
        if companies:
            for section in companies:
                for key, value in section.items():
                    if key in data:
                        key = '%s companies' % key
                    data.update({key: value})
            del data['companies']
        if 'box office' in data:
            data['box office'] = dict(data['box office'])
        alt_kind = data.get('alternative kind')
        if alt_kind is not None:
            data['kind'] = alt_kind
        return data


def _process_plotsummary(x):
    """Process a plot (contributed by Rdian06)."""
    xauthor = x.get('author')
    xplot = x.get('plot', '').strip()
    if xauthor:
        xplot += '::%s' % xauthor
    return xplot


class DOMHTMLPlotParser(DOMParserBase):
    """Parser for the "plot summary" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a 'plot' key, containing a list
    of string with the structure: 'summary::summary_author <author@email>'.

    Example::

        pparser = HTMLPlotParser()
        result = pparser.parse(plot_summary_html_string)
    """
    _defGetRefs = True

    # Notice that recently IMDb started to put the email of the
    # author only in the link, that we're not collecting, here.
    rules = [
        Rule(
            key='plot',
            extractor=Rules(
                foreach='//div[@data-testid="sub-section-summaries"]//li',
                rules=[
                    Rule(
                        key='plot',
                        extractor=Path('.//text()')
                    ),
                ],
                transform=_process_plotsummary
            )
        ),
        Rule(
            key='synopsis',
            extractor=Path(
                foreach='//div[@data-testid="sub-section-synopsis"]//li',
                path='.//text()'
            )
        )
    ]

    def preprocess_dom(self, dom):
        preprocessors.remove(dom, '//li[@id="no-summary-content"]')
        return dom

    def postprocess_data(self, data):
        if 'synopsis' in data and data['synopsis'][0] and 'a Synopsis for this title' in data['synopsis'][0]:
            del data['synopsis']
        return data


def _process_award(x):
    award = {}
    _award = x.get('award')
    if _award is not None:
        _award = _award.strip()
    award['award'] = _award
    if not award['award']:
        return {}
    award['year'] = x.get('year').strip()
    if award['year'] and award['year'].isdigit():
        award['year'] = int(award['year'])
    award['result'] = x.get('result').strip()
    category = x.get('category').strip()
    if category:
        award['category'] = category
    received_with = x.get('with')
    if received_with is not None:
        award['with'] = received_with.strip()
    notes = x.get('notes')
    if notes is not None:
        notes = notes.strip().split('\n', 2)[0]
        notes = re_space.sub(' ', notes)
        if notes:
            award['notes'] = notes
    award['anchor'] = x.get('anchor')
    return award


class DOMHTMLAwardsParser(DOMParserBase):
    """Parser for the "awards" page of a given person or movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        awparser = HTMLAwardsParser()
        result = awparser.parse(awards_html_string)
    """
    subject = 'title'
    _containsObjects = True

    rules = [
        Rule(
            key='awards',
            extractor=Rules(
                foreach='//*[@id="main"]/div[1]/div/table//tr',
                rules=[
                    Rule(
                        key='year',
                        extractor=Path('normalize-space(./ancestor::table/preceding-sibling::*[1]/a/text())')
                    ),
                    Rule(
                        key='result',
                        extractor=Path('./td[1]/b/text()')
                    ),
                    Rule(
                        key='award',
                        extractor=Path('./td[1]/span/text()')
                    ),
                    Rule(
                        key='category',
                        extractor=Path('normalize-space(./ancestor::table/preceding-sibling::*[1]/text())')
                    ),
                    Rule(
                        key='notes',
                        extractor=Path('./td[2]/text()')
                    ),
                    Rule(
                        key='anchor',
                        extractor=Path('.//text()')
                    )
                ],
                transform=_process_award
            )
        ),
        Rule(
            key='recipients',
            extractor=Rules(
                foreach='//*[@id="main"]/div[1]/div/table//tr/td[2]/a',
                rules=[
                    Rule(
                        key='name',
                        extractor=Path('./text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('./@href')
                    ),
                    Rule(
                        key='anchor',
                        extractor=Path('./ancestor::tr//text()')
                    )
                ]
            )
        )
    ]

    preprocessors = [
        (re.compile('(<tr><td[^>]*>.*?</td></tr>\n\n</table>)', re.I),
         r'\1</table>'),
        (re.compile('(<tr><td[^>]*>\n\n<big>.*?</big></td></tr>)', re.I),
         r'</table><table class="_imdbpy">\1'),
        (re.compile('(<table[^>]*>\n\n)</table>(<table)', re.I), r'\1\2'),
        (re.compile('(<small>.*?)<br>(.*?</small)', re.I), r'\1 \2'),
        (re.compile('(</tr>\n\n)(<td)', re.I), r'\1<tr>\2')
    ]

    def preprocess_dom(self, dom):
        """Repeat td elements according to their rowspan attributes
        in subsequent tr elements.
        """
        cols = self.xpath(dom, "//td[@rowspan]")
        for col in cols:
            span = int(col.get('rowspan'))
            del col.attrib['rowspan']
            position = len(self.xpath(col, "./preceding-sibling::td"))
            row = col.getparent()
            for tr in self.xpath(row, "./following-sibling::tr")[:span - 1]:
                # if not cloned, child will be moved to new parent
                clone = self.clone(col)
                tr.insert(position, clone)
        return dom

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        nd = []
        for award in data['awards']:
            matches = [p for p in data.get('recipients', [])
                       if 'nm' in p.get('link') and award.get('anchor') == p.get('anchor')]
            if self.subject == 'title':
                recipients = [
                    Person(name=recipient['name'],
                           personID=analyze_imdbid(recipient['link']))
                    for recipient in matches
                ]
                award['to'] = recipients
            elif self.subject == 'name':
                recipients = [
                    Movie(title=recipient['name'],
                          movieID=analyze_imdbid(recipient['link']))
                    for recipient in matches
                ]
                award['for'] = recipients
            nd.append(award)
            if 'anchor' in award:
                del award['anchor']
        return {'awards': nd}


class DOMHTMLTaglinesParser(DOMParserBase):
    """Parser for the "taglines" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        tparser = DOMHTMLTaglinesParser()
        result = tparser.parse(taglines_html_string)
    """
    rules = [
        Rule(
            key='taglines',
            extractor=Path(
                foreach='//div[@class="ipc-html-content-inner-div"]',
                path='.//text()'
            )
        )
    ]

    def postprocess_data(self, data):
        if 'taglines' in data:
            data['taglines'] = [tagline.strip() for tagline in data['taglines']]
        return data


class DOMHTMLKeywordsParser(DOMParserBase):
    """Parser for the "keywords" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        kwparser = DOMHTMLKeywordsParser()
        result = kwparser.parse(keywords_html_string)
    """
    rules = [
        Rule(
            key='relevant keywords',
            extractor=Rules(
                foreach='//ul[contains(@class, "ipc-metadata-list")]//li[contains(@class, "ipc-metadata-list-summary-item")]',
                rules=[
                    Rule(
                        key='keyword',
                        extractor=Path('.//a[1]//text()')
                    ),
                    Rule(
                        key='votes_str',
                        extractor=Path('.//span[contains(@class, "ipc-voting__label__count--up")]/text()')
                    )
                ],
                transform=lambda x: {
                    'keyword': (x.get('keyword') or '').strip().lower(),
                    'keyword_dash': (x.get('keyword') or '').strip().lower().replace(' ', '-'),
                    'votes_str': (x.get('votes_str') or '').strip().lower()
                }
            )
        )
    ]

    def postprocess_data(self, data):
        if 'relevant keywords' in data:
            rk = []
            for x in data['relevant keywords']:
                if 'votes_str' in x:
                    if 'is this relevant?' in x['votes_str']:
                        x['votes_for'] = 0
                        x['total_votes'] = 0
                    else:
                        try:
                            x['votes_for'] = int(x['votes_str'].split('of')[0].strip())
                            x['total_votes'] = int(re.sub(r"\D", "", x['votes_str'].split('of')[1]).strip())
                        except Exception:
                            x['votes_for'] = 0
                            x['total_votes'] = 0
                    rk.append(x)
            data['relevant keywords'] = rk
        if 'relevant keywords' in data and len(data['relevant keywords']) > 0:
            keywords = [k['keyword_dash'] for k in data['relevant keywords'] if k.get('keyword')]
            data['keywords'] = keywords
        return data


class DOMHTMLAlternateVersionsParser(DOMParserBase):
    """Parser for the "alternate versions" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        avparser = DOMHTMLAlternateVersionsParser()
        result = avparser.parse(alternateversions_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(
            key='alternate versions',
            extractor=Path(
                foreach='//ul[@class="trivia"]/li',
                path='.//text()',
                transform=transformers.strip
            )
        )
    ]


class DOMHTMLTriviaParser(DOMParserBase):
    """Parser for the "trivia" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        tparser = DOMHTMLTriviaParser()
        result = tparser.parse(trivia_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(key="trivia", extractor=Path(foreach='//div[@class="ipc-html-content-inner-div"]', path='.//text()'))
    ]


class DOMHTMLSoundtrackParser(DOMParserBase):
    """Parser for the "soundtrack" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        stparser = DOMHTMLSoundtrackParser()
        result = stparser.parse(soundtrack_html_string)
    """
    _defGetRefs = True

    preprocessors = [('<br />', '\n'), ('<br>', '\n')]

    rules = [
        Rule(
            key='soundtrack',
            extractor=Path(
                foreach='//div[@class="list"]//div',
                path='.//text()',
                transform=transformers.strip
            )
        )
    ]

    def postprocess_data(self, data):
        if 'soundtrack' in data:
            nd = []
            for x in data['soundtrack']:
                ds = x.split('\n')
                title = ds[0]
                if title[0] == '"' and title[-1] == '"':
                    title = title[1:-1]
                nds = []
                newData = {}
                for t in ds[1:]:
                    if ' with ' in t or ' by ' in t or ' from ' in t \
                            or ' of ' in t or t.startswith('From '):
                        nds.append(t)
                    else:
                        if nds:
                            nds[-1] += t
                        else:
                            nds.append(t)
                newData[title] = {}
                for t in nds:
                    skip = False
                    for sep in ('From ',):
                        if t.startswith(sep):
                            fdix = len(sep)
                            kind = t[:fdix].rstrip().lower()
                            info = t[fdix:].lstrip()
                            newData[title][kind] = info
                            skip = True
                    if not skip:
                        for sep in ' with ', ' by ', ' from ', ' of ':
                            fdix = t.find(sep)
                            if fdix != -1:
                                fdix = fdix + len(sep)
                                kind = t[:fdix].rstrip().lower()
                                info = t[fdix:].lstrip()
                                newData[title][kind] = info
                                break
                nd.append(newData)
            data['soundtrack'] = nd
        return data


class DOMHTMLCrazyCreditsParser(DOMParserBase):
    """Parser for the "crazy credits" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        ccparser = DOMHTMLCrazyCreditsParser()
        result = ccparser.parse(crazycredits_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(
            key='crazy credits',
            extractor=Path(
                foreach='//ul/li/tt',
                path='.//text()',
                transform=lambda x: x.replace('\n', ' ').replace('  ', ' ')
            )
        )
    ]


class DOMHTMLGoofsParser(DOMParserBase):
    """Parser for the "goofs" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server. The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        gparser = DOMHTMLGoofsParser()
        result = gparser.parse(goofs_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(
            key='goofs',
            extractor=Path(
                foreach='.//div[contains(@class, "ipc-html-content-inner-div")]',
                path='./text()',
                transform=lambda x: x.strip()
            )
        )
    ]

    def postprocess_data(self, data):
        goofs = data.get('goofs', [])
        if not goofs:
            return {}
        # Clean and structure the goofs data
        processed_goofs = [goof for goof in goofs if goof.strip()]
        return {'goofs': processed_goofs}


class DOMHTMLQuotesParser(DOMParserBase):
    """Parser for the "memorable quotes" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        qparser = DOMHTMLQuotesParser()
        result = qparser.parse(quotes_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(
            key='quotes',
            extractor=Path(
                foreach='//div[@class="ipc-html-content-inner-div"]',
                path='.//text()',
                transform=lambda x: x.strip()
            )
        )
    ]

    def preprocess_dom(self, dom):
        preprocessors.remove(dom, '//div[@class="did-you-know-actions"]')
        return dom

    def postprocess_data(self, data):
        quotes = data.get('quotes', [])
        if not quotes:
            return {}
        # IMDb now separates quotes by double newlines, so split accordingly
        processed_quotes = []
        for q in quotes:
            # Split by double newlines, then by single newlines for lines in a quote
            blocks = [block.strip() for block in q.split('\n\n') if block.strip()]
            for block in blocks:
                lines = [line.strip() for line in block.split('\n') if line.strip()]
                if lines:
                    processed_quotes.append(lines)
        return {'quotes': processed_quotes}


class DOMHTMLReleaseinfoParser(DOMParserBase):
    """Parser for the "release dates" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        rdparser = DOMHTMLReleaseinfoParser()
        result = rdparser.parse(releaseinfo_html_string)
    """
    rules = [
        Rule(
            key='release dates',
            extractor=Rules(
                foreach='//div[@data-testid="sub-section-releases"]/ul/li',
                rules=[
                    Rule(
                        key='country',
                        extractor=Path('./a[contains(@href, "/calendar")]/text()', transform=lambda x: x.strip())
                    ),
                    Rule(
                        key='date',
                        extractor=Path('./div/ul/li/span[1]/text()', transform=lambda x: x.strip())
                    ),
                    Rule(
                        key='notes',
                        extractor=Path('./div/ul/li/span[2]/text()', transform=lambda x: x.strip())
                    ),
                    Rule(
                        key='country_code',
                        extractor=Path('./a[contains(@href, "/calendar")]/@href',
                                       transform=lambda x: x.split('region=')[1].split('&')[0].strip().upper() if 'region=' in x else '')
                    )
                ]
            )
        ),
        Rule(
            key='akas',
            extractor=Rules(
                foreach='//div[@data-testid="sub-section-akas"]/ul/li',
                rules=[
                    Rule(
                        key='title',
                        extractor=Path('.//ul//li/span[contains(@class, "ipc-metadata-list-item__list-content-item")][1]/text()', transform=lambda x: x.strip())
                    ),
                    Rule(
                        key='countries',
                        extractor=Path('./span/text()', transform=lambda x: x.strip())
                    )
                ]
            )
        )
    ]

    preprocessors = []

    def postprocess_data(self, data):
        if not ('release dates' in data or 'akas' in data):
            return data

        releases = data.get('release dates') or []
        processed_releases = []
        raw_releases = []
        for item in releases:
            country = item.get('country')
            date = item.get('date')
            if not (country and date):
                continue

            info = f"{country}::{date}"
            notes = item.get('notes')
            if notes:
                item['notes'] = notes.replace('\n', '').strip()
                info += f"::{item['notes']}"

            processed_releases.append(info)
            raw_item = {
                'country': country,
                'date': date,
                'country_code': item.get('country_code', ''),
            }
            if notes:
                raw_item['notes'] = item['notes']
            raw_releases.append(raw_item)

        if raw_releases:
            data['raw release dates'] = raw_releases
        if processed_releases:
            data['release dates'] = processed_releases
        elif 'release dates' in data:
            del data['release dates']

        akas = data.get('akas') or []
        processed_akas = []
        raw_akas = []
        for item in akas:
            title = item.get('title')
            if not title:
                continue

            countries_str = item.get('countries')
            raw_item = {'title': title}
            if countries_str:
                raw_item['countries'] = countries_str
                countries = [c.strip() for c in countries_str.split(',') if c.strip()]
                for country in countries:
                    processed_akas.append(f"{title} ({country})")
            else:
                processed_akas.append(title)
            raw_akas.append(raw_item)

        if raw_akas:
            if 'raw release dates' in data:
                country_map = {rd['country']: rd['country_code'] for rd in data['raw release dates'] if rd.get('country_code')}
                for aka_item in raw_akas:
                    if 'countries' in aka_item:
                        first_country = aka_item['countries'].split(',')[0].strip()
                        if first_country in country_map:
                            aka_item['country_code'] = country_map[first_country]

            data['raw akas'] = raw_akas

        if processed_akas:
            data['akas'] = data['akas from release info'] = processed_akas
        elif 'akas' in data:
            del data['akas']

        return data


class DOMHTMLRatingsParser(DOMParserBase):
    """Parser for the "user ratings" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.
    """
    # Updated for new IMDb ratings page layout (2024)
    rules = [
        Rule(
            key='aggregate rating',
            extractor=Path(
                '//div[@data-testid="rating-button__aggregate-rating__score"]/span[1]/text()',
                transform=lambda x: float(x) if x else None
            )
        ),
        Rule(
            key='aggregate votes',
            extractor=Path(
                '//div[@data-testid="rating-button__aggregate-rating__score"]/following-sibling::div[1]/text()',
                transform=lambda x: int(x.replace('M', '000000').replace('K', '000').replace('.', '').replace(',', '').strip()) if x else None
            )
        ),
        Rule(
            key='user rating',
            extractor=Path(
                '//div[@data-testid="rating-button__user-rating__score"]/span[1]/text()',
                transform=lambda x: int(x) if x else None
            )
        ),
        Rule(
            key='unweighted mean',
            extractor=Path(
                '//p[@data-testid="calculations-label"]/text()',
                transform=lambda x: float(x.split()[0]) if x and x.split() else None
            )
        )
    ]

    def postprocess_data(self, data):
        nd = {}
        if data.get('aggregate rating'):
            nd['rating'] = data['aggregate rating']
        if data.get('aggregate votes'):
            nd['votes'] = data['aggregate votes']
        if data.get('user rating'):
            nd['user_rating'] = data['user rating']
        if data.get('unweighted mean'):
            nd['arithmetic mean'] = data['unweighted mean']
        return nd


def _normalize_href(href):
    if (href is not None) and (not href.lower().startswith('http://')):
        if href.startswith('/'):
            href = href[1:]
        # TODO: imdbURL_base may be set by the user!
        href = '%s%s' % (imdbURL_base, href)
    return href


class DOMHTMLCriticReviewsParser(DOMParserBase):
    """Parser for the "critic reviews" pages of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        crparser = DOMHTMLCriticReviewsParser()
        result = crparser.parse(criticreviews_html_string)
    """
    kind = 'critic reviews'

    rules = [
        Rule(
            key='metascore',
            extractor=Path('//*[@data-testid="critic-reviews-title"]/div/text()',
                           transform=lambda x: int(x.strip()))
        ),
        Rule(
            key='metacritic url',
            extractor=Path('//*[@data-testid="critic-reviews-title"]/div[2]/div[2]/a/@href')
        )
    ]


class DOMHTMLReviewsParser(DOMParserBase):
    """Parser for the "reviews" pages of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        rparser = DOMHTMLReviewsParser()
        result = rparser.parse(reviews_html_string)
    """
    rules = [
        Rule(
            key='reviews',
            extractor=Rules(
                foreach='//div[@class="review-container"]',
                rules=[
                    Rule(
                        key='text',
                        extractor=Path('.//div[@class="text show-more__control"]//text()')
                    ),
                    Rule(
                        key='helpful',
                        extractor=Path('.//div[@class="actions text-muted"]//text()[1]')
                    ),
                    Rule(
                        key='title',
                        extractor=Path('.//a[@class="title"]//text()')
                    ),
                    Rule(
                        key='author',
                        extractor=Path('.//span[@class="display-name-link"]/a/@href')
                    ),
                    Rule(
                        key='date',
                        extractor=Path('.//span[@class="review-date"]//text()')
                    ),
                    Rule(
                        key='rating',
                        extractor=Path('.//span[@class="point-scale"]/preceding-sibling::span[1]/text()')
                    )
                ],
                transform=lambda x: ({
                    'content': x.get('text', '').replace('\n', ' ').replace('  ', ' ').strip(),
                    'helpful': [int(s) for s in x.get('helpful', '').split() if s.isdigit()],
                    'title': x.get('title', '').strip(),
                    'author': analyze_imdbid(x.get('author')),
                    'date': x.get('date', '').strip(),
                    'rating': x.get('rating', '').strip()
                })
            )
        )
    ]

    preprocessors = [('<br>', '<br>\n')]

    def postprocess_data(self, data):
        for review in data.get('reviews', []):
            if review.get('rating'):
                if isinstance(review['rating'], str):
                    review['rating'] = int(review['rating'])
                elif len(review['rating']) == 2:  # May be legacy code.
                    review['rating'] = int(review['rating'][0])
                else:
                    review['rating'] = None
            else:
                review['rating'] = None

            if review.get('helpful') and len(review['helpful']) == 2:
                review['not_helpful'] = review['helpful'][1] - review['helpful'][0]
                review['helpful'] = review['helpful'][0]
            else:
                review['helpful'] = 0
                review['not_helpful'] = 0

            review['author'] = "ur%s" % review['author']

        return data


class DOMHTMLFullCreditsParser(DOMParserBase):
    """Parser for the "full credits" (series cast section) page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        fcparser = DOMHTMLFullCreditsParser()
        result = fcparser.parse(fullcredits_html_string)
    """
    kind = 'full credits'

    rules = [
        Rule(
            key='cast',
            extractor=Rules(
                foreach='//table[@class="cast_list"]//tr[@class="odd" or @class="even"]',
                rules=[
                    Rule(
                        key='person',
                        extractor=Path('.//text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('./td[2]/a/@href')
                    ),
                    Rule(
                        key='roleID',
                        extractor=Path('./td[4]//div[@class="_imdbpyrole"]/@roleid')
                    ),
                    Rule(
                        key='headshot',
                        extractor=Path('./td[@class="primary_photo"]/a/img/@loadlate')
                    )
                ],
                transform=lambda x: build_person(
                    x.get('person', ''),
                    personID=analyze_imdbid(x.get('link')),
                    roleID=(x.get('roleID', '')).split('/'),
                    headshot=(x.get('headshot', ''))
                )
            )
        ),
        # parser for misc sections like 'casting department', 'stunts', ...
        Rule(
            key='misc sections',
            extractor=Rules(
                foreach='//h4[contains(@class, "dataHeaderWithBorder")]',
                rules=[
                    Rule(
                        key=Path('./@name', transform=clean_section_name),
                        extractor=Rules(
                            foreach='./following-sibling::table[1]//tr',
                            rules=[
                                Rule(
                                    key='person',
                                    extractor=Path('.//text()')
                                ),
                                Rule(
                                    key='link',
                                    extractor=Path('./td[1]/a[@href]/@href')
                                )
                            ],
                            transform=lambda x: build_person(
                                x.get('person') or '',
                                personID=analyze_imdbid(x.get('link'))
                            )
                        )
                    )
                ]
            )
        ),
    ]

    preprocessors = [
        (_reRolesMovie, _manageRoles)
    ]

    def postprocess_data(self, data):
        # Convert section names.
        clean_cast = []
        for person in data.get('cast', []):
            if person.personID and person.get('name'):
                clean_cast.append(person)
        if clean_cast:
            data['cast'] = clean_cast
        misc_sections = data.get('misc sections')
        if misc_sections is not None:
            for section in misc_sections:
                for sectName, sectData in section.items():
                    # skip sections with their own parsers
                    if sectName in ('cast',):
                        continue
                    newName = _SECT_CONV.get(sectName, sectName)
                    if sectData:
                        data[newName] = sectData
            del data['misc sections']
        return data


class DOMHTMLOfficialsitesParser(DOMParserBase):
    """Parser for the "official sites", "external reviews"
    "miscellaneous links", "sound clips", "video clips" and
    "photographs" pages of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        osparser = DOMHTMLOfficialsitesParser()
        result = osparser.parse(officialsites_html_string)
    """
    rules = [
        Rule(
            foreach='//div[contains(@class, "ipc-page-grid__item")]/section[contains(@class, "ipc-page-section--base")]',  # noqa: E501
            key=Path(
                './/h3//text()',
                transform=lambda x: x.strip().lower()
            ),
            extractor=Rules(
                foreach='.//ul[1]//li//a[1]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('./@href')
                    ),
                    Rule(
                        key='info',
                        extractor=Path('.//text()')
                    )
                ],
                transform=lambda x: (
                    x.get('info', '').strip(),
                    unquote(x.get('link'))
                )
            )
        )
    ]


class DOMHTMLConnectionsParser(DOMParserBase):
    """Parser for the "connections" pages of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        osparser = DOMHTMLOfficialsitesParser()
        result = osparser.parse(officialsites_html_string)
    """
    rules = [
        Rule(
            foreach='//div[contains(@class, "ipc-page-grid__item")]/section[contains(@class, "ipc-page-section--base")]',  # noqa: E501
            key=Path(
                './div[1]//h3//text()',
                transform=lambda x: (x or '').strip().lower()
            ),
            extractor=Rules(
                foreach='./div[2]//ul[1]//li',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('./div[1]//p//a/@href')
                    ),
                    Rule(
                        key='info',
                        extractor=Path('./div[1]//p//text()')
                    )
                ],
                transform=lambda x: (
                    x.get('info', '').strip(),
                    unquote(_normalize_href(x.get('link', '')))
                )
            )
        )
    ]

    def postprocess_data(self, data):
        connections = {}
        for k, v in data.items():
            k = k.strip()
            if not (k and v):
                continue
            movies = []
            for title, link in v:
                title = title.strip().replace('\n', '')
                movieID = analyze_imdbid(link)
                if not (title and movieID):
                    continue
                movie = Movie(title=title, movieID=movieID,
                              accessSystem=self._as, modFunct=self._modFunct)
                movies.append(movie)
            if movies:
                connections[k] = movies
        return {'connections': connections}


class DOMHTMLLocationsParser(DOMParserBase):
    """Parser for the "locations" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        lparser = DOMHTMLLocationsParser()
        result = lparser.parse(locations_html_string)
    """
    rules = [
        Rule(
            key='locations',
            extractor=Rules(
                foreach='//dt',
                rules=[
                    Rule(
                        key='place',
                        extractor=Path('.//text()')
                    ),
                    Rule(
                        key='note',
                        extractor=Path('./following-sibling::dd[1]//text()')
                    )
                ],
                transform=lambda x: ('%s::%s' % (x['place'].strip(),
                                                 (x['note'] or '').strip())).strip(':')
            )
        )
    ]


class DOMHTMLTechParser(DOMParserBase):
    """Parser for the technical specifications page of a given movie.
    Extracts technical specs from the new IMDb layout using robust XPath rules.
    """
    kind = 'tech'
    rules = [
        Rule(
            key='technical specs',
            extractor=Rules(
                foreach='//ul[contains(@class, "ipc-metadata-list")]/li[contains(@class, "ipc-metadata-list__item")]',
                rules=[
                    Rule(
                        key='label',
                        extractor=Path('.//span[contains(@class, "ipc-metadata-list-item__label")]/text()', transform=lambda x: x.strip().lower())
                    ),
                    Rule(
                        key='values',
                        extractor=Path(
                            foreach='.//ul[contains(@class, "ipc-inline-list")]/li',
                            path='.//text()',
                            transform=lambda x: x.strip()
                        )
                    ),
                    Rule(
                        key='single_value',
                        extractor=Path('.//div[contains(@class, "ipc-metadata-list-item__content-container")]/span[1]/text()', transform=lambda x: x.strip())
                    )
                ]
            )
        )
    ]

    preprocessors = [
        (re.compile('ipc-metadata-list-item__list-content-item--subText">', re.I),
         'ipc-metadata-list-item__list-content-item--subtext">::')
    ]

    def postprocess_data(self, data):
        specs = data.get('technical specs', [])
        result = {}
        for item in specs:
            label = item.get('label')
            values = item.get('values')
            single_value = item.get('single_value')
            if label:
                if values and isinstance(values, list) and any(values):
                    # Filter out empty strings
                    values = [v for v in values if v.strip()]
                    if len(values) == 1:
                        result[label] = values[0]
                    elif len(values) > 1:
                        result[label] = values
                elif single_value:
                    result[label] = single_value
        return {self.kind: result}


class DOMHTMLNewsParser(DOMParserBase):
    """Parser for the "news" page of a given movie or person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        nwparser = DOMHTMLNewsParser()
        result = nwparser.parse(news_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(
            key='news',
            extractor=Rules(
                foreach='//h2',
                rules=[
                    Rule(
                        key='title',
                        extractor=Path('./text()')
                    ),
                    Rule(
                        key='fromdate',
                        extractor=Path('./following-sibling::p[1]/small//text()')
                    ),
                    Rule(
                        key='body',
                        extractor=Path('../following-sibling::p[2]//text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('../..//a[text()="Permalink"]/@href')
                    ),
                    Rule(
                        key='fulllink',
                        extractor=Path('../..//a[starts-with(text(), "See full article at")]/@href')
                    )
                ],
                transform=lambda x: {
                    'title': x.get('title').strip(),
                    'date': x.get('fromdate').split('|')[0].strip(),
                    'from': x.get('fromdate').split('|')[1].replace('From ', '').strip(),
                    'body': (x.get('body') or '').strip(),
                    'link': _normalize_href(x.get('link')),
                    'full article link': _normalize_href(x.get('fulllink'))
                }
            )
        )
    ]

    preprocessors = [
        (re.compile('(<a name=[^>]+><h2>)', re.I), r'<div class="_imdbpy">\1'),
        (re.compile('(<hr/>)', re.I), r'</div>\1'),
        (re.compile('<p></p>', re.I), r'')
    ]

    def postprocess_data(self, data):
        if 'news' not in data:
            return {}
        for news in data['news']:
            if 'full article link' in news:
                if news['full article link'] is None:
                    del news['full article link']
        return data


def _parse_review(x):
    result = {}
    title = x.get('title').strip()
    if title[-1] == ':':
        title = title[:-1]
    result['title'] = title
    result['link'] = _normalize_href(x.get('link'))
    kind = x.get('kind').strip()
    if kind[-1] == ':':
        kind = kind[:-1]
    result['review kind'] = kind
    text = x.get('review').replace('\n\n', '||').replace('\n', ' ').split('||')
    review = '\n'.join(text)
    if x.get('author') is not None:
        author = x.get('author').strip()
        review = review.split(author)[0].strip()
        result['review author'] = author[2:]
    if x.get('item') is not None:
        item = x.get('item').strip()
        review = review[len(item):].strip()
        review = "%s: %s" % (item, review)
    result['review'] = review
    return result


MONTH_NUMS = {m: "%02d" % (n + 1)
              for n, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


class DOMHTMLSeasonEpisodesParser(DOMParserBase):
    """Parser for the "episode list" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        sparser = DOMHTMLSeasonEpisodesParser()
        result = sparser.parse(episodes_html_string)
    """

    rules = [
        Rule(
            key='series link',
            extractor=Path('.//div[@data-testid="poster"]//a/@href')
        ),
        Rule(
            key='series title',
            extractor=Path('//h2[@data-testid="subtitle"]/text()')
        ),
        Rule(
            key='_seasons',
            extractor=Path(
                foreach='//a[@data-testid="tab-season-entry"]',
                path='./text()'
            )
        ),
        Rule(
            key='_current_season',
            extractor=Path('//a[@data-testid="tab-season-entry"][contains(@class, "ipc-tab--active")]/text()')
        ),
        Rule(
            key='episodes',
            extractor=Rules(
                foreach='//h4',
                rules=[
                    Rule(
                        key=Path('.//a//text()'),
                        extractor=Rules(
                            rules=[
                                Rule(
                                    key='link',
                                    extractor=Path('.//a/@href')
                                ),
                                Rule(
                                    key='original air date',
                                    extractor=Path('following-sibling::span/text()')
                                ),
                                Rule(
                                    key='rating',
                                    extractor=Path('../..//span[contains(@class, "ratingGroup--imdb-rating")]/text()')
                                ),
                                Rule(
                                    key='votes',
                                    extractor=Path('../..//span[contains(@class, "ipc-rating-star--voteCount")]/text()')
                                ),
                                Rule(
                                    key='plot',
                                    extractor=Path('../..//div[@role="presentation"]//text()')
                                )
                            ]
                        )
                    )
                ]
            )
        )
    ]

    def postprocess_data(self, data):
        series_id = analyze_imdbid(data.get('series link'))
        series_title = data.get('series title', '').strip()
        selected_season = data.get('_current_season', 'unknown season').strip()
        if not (series_id and series_title):
            return {}
        series = Movie(title=series_title, movieID=str(series_id),
                       accessSystem=self._as, modFunct=self._modFunct)
        if series.get('kind') == 'movie':
            series['kind'] = 'tv series'
        try:
            selected_season = int(selected_season)
        except ValueError:
            pass
        nd = {selected_season: {}}
        if 'episode -1' in data:
            counter = 1
            for episode in data['episode -1']:
                while 'episode %d' % counter in data:
                    counter += 1
                k = 'episode %d' % counter
                data[k] = [episode]
            del data['episode -1']
        episodes = data.get('episodes', [])
        for seq, ep in enumerate(episodes):
            if not ep:
                continue
            episode_nr_title, episode = list(ep.items())[0]
            nr_title_tokens = episode_nr_title.split(" ∙ ")
            if len(nr_title_tokens) == 2:
                episode_seq, episode_title = nr_title_tokens
                episode_nr = episode_seq.split(".")[1][1:]
            else:
                episode_nr, episode_title = seq + 1, nr_title_tokens[0]
            try:
                episode_nr = int(episode_nr)
            except ValueError:
                pass
            episode_id = analyze_imdbid(episode.get('link', ''))
            episode_air_date = episode.get('original air date', '').strip()
            episode_plot = episode.get('plot', '')
            episode_rating = episode.get('rating', '')
            episode_votes = episode.get('votes', '')[2:-1]  # remove ()
            if not (episode_nr is not None and episode_id and episode_title):
                continue
            ep_obj = Movie(movieID=episode_id, title=episode_title,
                           accessSystem=self._as, modFunct=self._modFunct)
            ep_obj['kind'] = 'episode'
            ep_obj['episode of'] = series
            ep_obj['season'] = selected_season
            ep_obj['episode'] = episode_nr
            if episode_rating:
                try:
                    ep_obj['rating'] = float(episode_rating)
                except Exception:
                    pass
            if episode_votes:
                try:
                    if episode_votes[-1] == "K":
                        ep_votes = int(float(episode_votes[:-1]) * 1000)
                    elif episode_votes[-1] == "M":
                        ep_votes = int(float(episode_votes[:-1]) * 1000000)
                    else:
                        ep_votes = int(episode_votes)
                    ep_obj['votes'] = ep_votes
                except Exception:
                    pass
            if episode_air_date:
                if episode_air_date[-4:].isdigit():
                    year = episode_air_date[-4:]
                    if episode_air_date.startswith(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
                        ep_month, ep_day = episode_air_date[5:].split(",")[0].split(" ")
                        episode_air_date = year + "-" + MONTH_NUMS[ep_month] + "-" + "%02d" % int(ep_day)
                    ep_obj['original air date'] = episode_air_date
                    ep_obj['year'] = int(year)
            if episode_plot:
                ep_obj['plot'] = episode_plot
            nd[selected_season][episode_nr] = ep_obj
        _seasons = data.get('_seasons') or []
        for idx, season in enumerate(_seasons):
            try:
                _seasons[idx] = int(season)
            except ValueError:
                pass
        return {'episodes': nd, '_seasons': _seasons, '_current_season': selected_season}


def _build_episode(x):
    """Create a Movie object for a given series' episode."""
    episode_id = analyze_imdbid(x.get('link'))
    episode_title = x.get('title')
    e = Movie(movieID=episode_id, title=episode_title)
    e['kind'] = 'episode'
    oad = x.get('oad')
    if oad:
        e['original air date'] = oad.strip()
    year = x.get('year')
    if year is not None:
        year = year[5:]
        if year == 'unknown':
            year = '????'
        if year and year.isdigit():
            year = int(year)
        e['year'] = year
    else:
        if oad and oad[-4:].isdigit():
            e['year'] = int(oad[-4:])
    epinfo = x.get('episode')
    if epinfo is not None:
        season, episode = epinfo.split(':')[0].split(',')
        e['season'] = int(season[7:])
        e['episode'] = int(episode[8:])
    else:
        e['season'] = 'unknown'
        e['episode'] = 'unknown'
    plot = x.get('plot')
    if plot:
        e['plot'] = plot.strip()
    return e


class DOMHTMLEpisodesParser(DOMParserBase):
    """Parser for the "episode list" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        eparser = DOMHTMLEpisodesParser()
        result = eparser.parse(episodes_html_string)
    """
    kind = 'episodes list'
    _episodes_path = "..//h4"
    _oad_path = "./following-sibling::span/strong[1]/text()"

    def _init(self):
        self.rules = [
            Rule(
                key='series title',
                extractor=Path('//title/text()')
            ),
            Rule(
                key='series movieID',
                extractor=Path(
                    './/h1/a[@class="main"]/@href',
                    transform=analyze_imdbid
                )
            ),
            Rule(
                key='episodes',
                extractor=Rules(
                    foreach='//div[@class="_imdbpy"]/h3',
                    rules=[
                        Rule(
                            key='./a/@name',
                            extractor=Rules(
                                foreach=self._episodes_path,
                                rules=[
                                    Rule(
                                        key='link',
                                        extractor=Path('./a/@href')
                                    ),
                                    Rule(
                                        key='title',
                                        extractor=Path('./a/text()')
                                    ),
                                    Rule(
                                        key='year',
                                        extractor=Path('./preceding-sibling::a[1]/@name')
                                    ),
                                    Rule(
                                        key='episode',
                                        extractor=Path('./text()[1]')
                                    ),
                                    Rule(
                                        key='oad',
                                        extractor=Path(self._oad_path)
                                    ),
                                    Rule(
                                        key='plot',
                                        extractor=Path('./following-sibling::text()[1]')
                                    )
                                ],
                                transform=_build_episode
                            )
                        )
                    ]
                )
            )
        ]

    preprocessors = [
        (re.compile('(<hr/>\n)(<h3>)', re.I), r'</div>\1<div class="_imdbpy">\2'),
        (re.compile('(</p>\n\n)</div>', re.I), r'\1'),
        (re.compile('<h3>(.*?)</h3>', re.I), r'<h4>\1</h4>'),
        (_reRolesMovie, _manageRoles),
        (re.compile('(<br/> <br/>\n)(<hr/>)', re.I), r'\1</div>\2')
    ]

    def postprocess_data(self, data):
        # A bit extreme?
        if 'series title' not in data:
            return {}
        if 'series movieID' not in data:
            return {}
        stitle = data['series title'].replace('- Episode list', '')
        stitle = stitle.replace('- Episodes list', '')
        stitle = stitle.replace('- Episode cast', '')
        stitle = stitle.replace('- Episodes cast', '')
        stitle = stitle.strip()
        if not stitle:
            return {}
        seriesID = data['series movieID']
        if seriesID is None:
            return {}
        series = Movie(title=stitle, movieID=str(seriesID),
                       accessSystem=self._as, modFunct=self._modFunct)
        nd = {}
        for key in list(data.keys()):
            if key.startswith('filter-season-') or key.startswith('season-'):
                season_key = key.replace('filter-season-', '').replace('season-', '')
                try:
                    season_key = int(season_key)
                except ValueError:
                    pass
                nd[season_key] = {}
                ep_counter = 1
                for episode in data[key]:
                    if not episode:
                        continue
                    episode_key = episode.get('episode')
                    if episode_key is None:
                        continue
                    if not isinstance(episode_key, int):
                        episode_key = ep_counter
                        ep_counter += 1
                    cast_key = 'Season %s, Episode %s:' % (season_key, episode_key)
                    if cast_key in data:
                        cast = data[cast_key]
                        for i in range(len(cast)):
                            cast[i].billingPos = i + 1
                        episode['cast'] = cast
                    episode['episode of'] = series
                    nd[season_key][episode_key] = episode
        if len(nd) == 0:
            return {}
        return {'episodes': nd}


class DOMHTMLFaqsParser(DOMParserBase):
    """Parser for the "FAQ" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        fparser = DOMHTMLFaqsParser()
        result = fparser.parse(faqs_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(
            key='faqs',
            extractor=Rules(
                foreach='//div[@class="section"]',
                rules=[
                    Rule(
                        key='question',
                        extractor=Path('./h3/a/span/text()')
                    ),
                    Rule(
                        key='answer',
                        extractor=Path('../following-sibling::div[1]//text()')
                    )
                ],
                transform=lambda x: '%s::%s' % (
                    x.get('question').strip(),
                    '\n\n'.join(x.get('answer').replace('\n\n', '\n').strip().split('||'))
                )
            )
        )
    ]

    preprocessors = [
        (re.compile('<br/><br/>', re.I), r'||'),
        (re.compile('<h4>(.*?)</h4>\n', re.I), r'||\1--'),
        (re.compile('<span class="spoiler"><span>(.*?)</span></span>', re.I),
         r'[spoiler]\1[/spoiler]')
    ]


class DOMHTMLAiringParser(DOMParserBase):
    """Parser for the "airing" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        aparser = DOMHTMLAiringParser()
        result = aparser.parse(airing_html_string)
    """
    _containsObjects = True

    rules = [
        Rule(
            key='series title',
            extractor=Path(
                '//title/text()',
                transform=lambda x: x.replace(' - TV schedule', '')
            )
        ),
        Rule(
            key='series id',
            extractor=Path('//h1/a[@href]/@href')
        ),
        Rule(
            key='tv airings',
            extractor=Rules(
                foreach='//tr[@class]',
                rules=[
                    Rule(
                        key='date',
                        extractor=Path('./td[1]//text()')
                    ),
                    Rule(
                        key='time',
                        extractor=Path('./td[2]//text()')
                    ),
                    Rule(
                        key='channel',
                        extractor=Path('./td[3]//text()')
                    ),
                    Rule(
                        key='link',
                        extractor=Path('./td[4]/a[1]/@href')
                    ),
                    Rule(
                        key='title',
                        extractor=Path('./td[4]//text()')
                    ),
                    Rule(
                        key='season',
                        extractor=Path('./td[5]//text()')
                    )
                ],
                transform=lambda x: {
                    'date': x.get('date'),
                    'time': x.get('time'),
                    'channel': x.get('channel').strip(),
                    'link': x.get('link'),
                    'title': x.get('title'),
                    'season': (x.get('season') or '').strip()
                }
            )
        )
    ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        seriesTitle = data.get('series title') or ''
        seriesID = analyze_imdbid(data.get('series id'))
        if seriesID and 'airing' in data:
            for airing in data['airing']:
                title = airing.get('title', '').strip()
                if not title:
                    epsTitle = seriesTitle
                    if seriesID is None:
                        continue
                    epsID = seriesID
                else:
                    epsTitle = '%s {%s}' % (data['series title'],
                                            airing['title'])
                    epsID = analyze_imdbid(airing['link'])
                e = Movie(title=epsTitle, movieID=epsID)
                airing['episode'] = e
                del airing['link']
                del airing['title']
                if not airing['season']:
                    del airing['season']
        if 'series title' in data:
            del data['series title']
        if 'series id' in data:
            del data['series id']
        if 'airing' in data:
            data['airing'] = [_f for _f in data['airing'] if _f]
        if 'airing' not in data or not data['airing']:
            return {}
        return data


class DOMHTMLParentsGuideParser(DOMParserBase):
    """Parser for the "parents guide" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        pgparser = HTMLParentsGuideParser()
        result = pgparser.parse(parentsguide_html_string)
    """
    rules = [
        Rule(
            key='mpaa',
            extractor=Path(
                '//tr[@id="mpaa-rating"]/td[2]//text()'
            )
        ),
        Rule(
            key='certificates',
            extractor=Rules(
                foreach='//tr[@id="certifications-list"]//li',
                rules=[
                    Rule(
                        key='full',
                        extractor=Path('./a//text()')
                    ),
                    Rule(
                        key='country_code',
                        extractor=Path('./a/@href')
                    ),
                    Rule(
                        key='note',
                        extractor=Path('./text()')
                    ),

                ],
                transform=lambda x: {
                    'country_code': x.get('country_code').split('certificates=')[1].split(':')[0].strip(),
                    'country': x.get('full').split(':')[0].strip(),
                    'certificate': x.get('full').split(':')[1].strip(),
                    'note': x.get('note').strip(),
                    'full': x.get('full').strip(),
                }
            )
        ),
        Rule(
            key='advisories',
            extractor=Rules(
                foreach='//section[starts-with(@id, "advisory-")]',
                rules=[
                    Rule(
                        key='section',
                        extractor=Path('./@id')
                    ),
                    Rule(
                        key='items',
                        extractor=Rules(
                            foreach='.//li',
                            rules=[
                                Rule(
                                    key='item',
                                    extractor=Path('./text()')
                                )
                            ],
                            transform=lambda x: x.get('item').strip()
                        )
                    )
                ]
            )
        ),
        Rule(
            key='advisory votes',
            extractor=Rules(
                foreach='//section[starts-with(@id, "advisory-")][not(contains(@id, "advisory-spoiler"))]',
                rules=[
                    Rule(key='section',
                         extractor=Path('./@id'),
                         ),
                    Rule(key='status',
                         extractor=Path('.//li[1]//div[contains(@class, "ipl-swapper__content-primary")]//span/text()')
                         ),
                    Rule(key='votes',
                         extractor=Path(
                             foreach='.//li[1]//span[contains(@class, "ipl-vote-button__details")]',
                             path='./text()',
                             transform=lambda x: int(x.replace(',', ''))
                         )
                         )
                ]
            )
        )
    ]

    def postprocess_data(self, data):
        if 'advisories' in data:
            for advisory in data['advisories']:
                sect = advisory.get('section', '').replace('-', ' ')
                items = [x for x in advisory.get('items', []) if x]
                if sect and items:
                    data[sect] = items
            del data['advisories']

        if 'advisory votes' in data:
            advisory_votes = {}
            for vote in data['advisory votes']:
                if 'status' not in vote or 'votes' not in vote:
                    continue
                advisory_votes[vote['section'][9:]] = {
                    'votes': {
                        'None': vote['votes'][0],
                        'Mild': vote['votes'][1],
                        'Moderate': vote['votes'][2],
                        'Severe': vote['votes'][3],
                    },
                    'status': vote['status'],
                }
            data['advisory votes'] = advisory_votes

        return data


_OBJECTS = {
    'movie_parser': ((DOMHTMLMovieParser,), None),
    'full_credits_parser': ((DOMHTMLFullCreditsParser,), None),
    'plot_parser': ((DOMHTMLPlotParser,), None),
    'movie_awards_parser': ((DOMHTMLAwardsParser,), None),
    'taglines_parser': ((DOMHTMLTaglinesParser,), None),
    'keywords_parser': ((DOMHTMLKeywordsParser,), None),
    'crazycredits_parser': ((DOMHTMLCrazyCreditsParser,), None),
    'goofs_parser': ((DOMHTMLGoofsParser,), None),
    'alternateversions_parser': ((DOMHTMLAlternateVersionsParser,), None),
    'trivia_parser': ((DOMHTMLTriviaParser,), None),
    'soundtrack_parser': ((DOMHTMLSoundtrackParser,), None),
    'quotes_parser': ((DOMHTMLQuotesParser,), None),
    'releasedates_parser': ((DOMHTMLReleaseinfoParser,), None),
    'ratings_parser': ((DOMHTMLRatingsParser,), None),
    'criticrev_parser': ((DOMHTMLCriticReviewsParser,), {'kind': 'critic reviews'}),
    'reviews_parser': ((DOMHTMLReviewsParser,), {'kind': 'reviews'}),
    'externalsites_parser': ((DOMHTMLOfficialsitesParser,), None),
    'officialsites_parser': ((DOMHTMLOfficialsitesParser,), None),
    'externalrev_parser': ((DOMHTMLOfficialsitesParser,), None),
    'misclinks_parser': ((DOMHTMLOfficialsitesParser,), None),
    'soundclips_parser': ((DOMHTMLOfficialsitesParser,), None),
    'videoclips_parser': ((DOMHTMLOfficialsitesParser,), None),
    'photosites_parser': ((DOMHTMLOfficialsitesParser,), None),
    'connections_parser': ((DOMHTMLConnectionsParser,), None),
    'tech_parser': ((DOMHTMLTechParser,), None),
    'locations_parser': ((DOMHTMLLocationsParser,), None),
    'news_parser': ((DOMHTMLNewsParser,), None),
    'episodes_parser': ((DOMHTMLEpisodesParser,), None),
    'season_episodes_parser': ((DOMHTMLSeasonEpisodesParser,), None),
    'movie_faqs_parser': ((DOMHTMLFaqsParser,), None),
    'airing_parser': ((DOMHTMLAiringParser,), None),
    'parentsguide_parser': ((DOMHTMLParentsGuideParser,), None)
}
