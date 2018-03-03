"""
parser.http.movieParser module (imdb package).

This module provides the classes (and the instances), used to parse the
IMDb pages on the www.imdb.com server about a movie.
E.g., for Brian De Palma's "The Untouchables", the referred
pages would be:
    combined details:   http://www.imdb.com/title/tt0094226/reference
    plot summary:       http://www.imdb.com/title/tt0094226/plotsummary
    ...and so on...

Copyright 2004-2018 Davide Alberani <da@erlug.linux.it>
          2008-2018 H. Turgut Uyar <uyar@tekir.org>

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

import functools
import re
import urllib.error
import urllib.parse
import urllib.request

from imdb import imdbURL_base
from imdb.Company import Company
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import _Container, KIND_MAP

from .utils import Attribute, DOMParserBase, Extractor, analyze_imdbid, build_person


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
    'art directors': 'art direction',
    'assistant directors': 'assistant director',
    'set decorators': 'set decoration',
    'visual effects department': 'visual effects',
    'miscellaneous': 'miscellaneous crew',
    'make up department': 'make up',
    'plot summary': 'plot outline',
    'cinematographers': 'cinematographer',
    'camera department': 'camera and electrical department',
    'costume designers': 'costume designer',
    'production designers': 'production design',
    'production managers': 'production manager',
    'music original': 'original music',
    'casting directors': 'casting director',
    'other companies': 'miscellaneous companies',
    'producers': 'producer',
    'special effects by': 'special effects department',
    'special effects': 'special effects companies'
}


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


def _replaceBR(mo):
    """Replaces <br> tags with '::' (useful for some akas)"""
    txt = mo.group(0)
    return txt.replace('<br>', '::')


_reAkas = re.compile(r'<h5>also known as:</h5>.*?</div>', re.I | re.M | re.S)


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


def analyze_og_title(og_title):
    data = {}
    match = _re_og_title.match(og_title)
    if match:
        data['title'] = match.group(1)

        if match.group(3):
            data['year'] = int(match.group(3))

        kind = match.group(2) or match.group(6)
        if kind is None:
            kind = 'movie'
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


class DOMHTMLMovieParser(DOMParserBase):
    """Parser for the "combined details" (and if instance.mdparse is
    True also for the "main details") page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        mparser = DOMHTMLMovieParser()
        result = mparser.parse(combined_details_html_string)
    """
    _containsObjects = True

    extractors = [
        Extractor(
            label='title',
            path="//meta[@property='og:title']",
            attrs=Attribute(
                key='title',
                path="@content",
                postprocess=analyze_og_title
            )
        ),

        # parser for misc sections like 'casting department', 'stunts', ...
        Extractor(
            label='glossarysections',
            group="//h4[contains(@class, 'ipl-header__content')]",
            group_key="./@name",
            group_key_normalize=lambda x: x.replace('_', ' '),
            path="../../following-sibling::table[1]//tr",
            attrs=Attribute(
                key=None,
                multi=True,
                path={
                    'person': ".//text()",
                    'link': "./td[1]/a[@href]/@href"
                },
                postprocess=lambda x: build_person(
                    x.get('person') or '',
                    personID=analyze_imdbid(x.get('link'))
                )
            )
        ),

        Extractor(
            label='cast',
            path="//table[@class='cast_list']//tr",
            attrs=Attribute(
                key="cast",
                multi=True,
                path={
                    'person': ".//text()",
                    'link': "td[2]/a/@href",
                    'roleID': "td[4]//div[@class='_imdbpyrole']/@roleid"
                },
                postprocess=lambda x: build_person(
                    x.get('person') or '',
                    personID=analyze_imdbid(x.get('link')),
                    roleID=(x.get('roleID') or '').split('/'))
            )
        ),

        Extractor(
            label='myrating',
            path="//span[@id='voteuser']",
            attrs=Attribute(
                key='myrating',
                path=".//text()"
            )
        ),

        Extractor(
            label='plot summary',
            path=".//td[starts-with(text(), 'Plot')]/..//p",
            attrs=Attribute(
                key='plot summary',
                path='./text()',
                postprocess=lambda x: x.strip().rstrip('|').rstrip()
            )
        ),

        Extractor(
            label='genres',
            path="//td[starts-with(text(), 'Genre')]/..//li/a",
            attrs=Attribute(
                key="genres",
                multi=True,
                path="./text()"
            )
        ),

        Extractor(
            label='runtimes',
            path="//td[starts-with(text(), 'Runtime')]/..//li",
            attrs=Attribute(
                key='runtimes',
                path="./text()",
                multi=True,
                postprocess=lambda x: x.strip().replace(' min', '')
            )
        ),

        Extractor(
            label='countries',
            path="//td[starts-with(text(), 'Countr')]/..//li/a",
            attrs=Attribute(
                key='countries',
                path="./text()",
                multi=True
            )
        ),

        Extractor(
            label='country codes',
            path="//td[starts-with(text(), 'Countr')]/..//li/a",
            attrs=Attribute(
                key='country codes',
                path="./@href",
                multi=True,
                postprocess=lambda x: x.split('/')[2].strip().lower()
            )
        ),

        Extractor(
            label='language',
            path="//td[starts-with(text(), 'Language')]/..//li/a",
            attrs=Attribute(
                key='language',
                path="./text()",
                multi=True
            )
        ),

        Extractor(
            label='language codes',
            path="//td[starts-with(text(), 'Language')]/..//li/a",
            attrs=Attribute(
                key='language codes',
                path="./@href",
                multi=True,
                postprocess=lambda x: x.split('/')[2].strip()
            )
        ),

        Extractor(
            label='color info',
            path="//td[starts-with(text(), 'Color')]/..//li/a",
            attrs=Attribute(
                key='color info',
                path="./text()",
                multi=True,
                postprocess=lambda x: x.replace(' (', '::(')
            )
        ),

        Extractor(
            label='aspect ratio',
            path="//td[starts-with(text(), 'Aspect')]/..",
            attrs=Attribute(
                key='aspect ratio',
                path=".//li/text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='sound mix',
            path="//td[starts-with(text(), 'Sound Mix')]/..//li/a",
            attrs=Attribute(
                key='sound mix',
                path="./text()",
                multi=True,
                postprocess=lambda x: x.replace(' (', '::(')
            )
        ),

        Extractor(
            label='certificates',
            path=".//td[starts-with(text(), 'Certificat')]/..",
            attrs=Attribute(
                key='certificates',
                path=".//text()",
                postprocess=analyze_certificates
            )
        ),

        Extractor(
            label='h5sections',
            path="//section[contains(@class, 'listo')]",
            attrs=[
                # Collects akas not encosed in <i> tags.
                Attribute(
                    key='other akas',
                    path=".//td[starts-with(text(), 'Also Known As')]/..//ul//text()",
                    postprocess=makeSplitter(
                        sep='::', origNotesSep='" - ', newNotesSep='::', strip='"'
                    )
                )
            ]
        ),

        Extractor(
            label='creator',
            path="//td[starts-with(text(), 'Creator')]/..//a",
            attrs=Attribute(
                key='creator',
                multi=True,
                path={
                    'name': "./text()",
                    'link': "./@href"
                },
                postprocess=lambda x: build_person(
                    x.get('name') or '',
                    personID=analyze_imdbid(x.get('link'))
                )
            )
        ),

        Extractor(
            label='thin writer',
            path="//div[starts-with(normalize-space(text()), 'Writer')]/ul/li[1]/a",
            attrs=Attribute(
                key='thin writer',
                multi=True,
                path={
                    'name': "./text()",
                    'link': "./@href"
                },
                postprocess=lambda x: build_person(
                    x.get('name') or '',
                    personID=analyze_imdbid(x.get('link'))
                )
            )
        ),

        Extractor(
            label='thin director',
            path="//div[starts-with(normalize-space(text()), 'Director')]/ul/li[1]/a",
            attrs=Attribute(
                key='thin director',
                multi=True,
                path={
                    'name': "./text()",
                    'link': "./@href"
                },
                postprocess=lambda x: build_person(
                    x.get('name') or '',
                    personID=analyze_imdbid(x.get('link'))
                )
            )
        ),

        Extractor(
            label='top 250/bottom 100',
            path="//li[@class='ipl-inline-list__item']//a[starts-with(@href, '/chart/')]",
            attrs=Attribute(
                key='top/bottom rank',
                path="./text()"
            )
        ),

        Extractor(
            label='original air date',
            path="//span[@imdbpy='airdate']",
            attrs=Attribute(
                key='original air date',
                path="./text()"
            )
        ),

        Extractor(
            label='series years',
            path="//div[@id='tn15title']//span[starts-with(text(), 'TV series')]",
            attrs=Attribute(
                key='series years',
                path="./text()",
                postprocess=lambda x: x.replace('TV series', '').strip()
            )
        ),

        Extractor(
            label='season/episode',
            path="//div[@class='titlereference-overview-season-episode-section']/ul",
            attrs=Attribute(
                key='season/episode',
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='number of episodes',
            path="//a[starts-with(text(), 'All Episodes')]",
            attrs=Attribute(
                key='number of episodes',
                path="./text()",
                postprocess=lambda x: int(x.replace('All Episodes', '').strip()[1:-1])
            )
        ),

        Extractor(
            label='episode number',
            path=".//div[@id='tn15epnav']",
            attrs=Attribute(
                key='episode number',
                path="./text()",
                postprocess=lambda x: int(re.sub(r'[^a-z0-9 ]', '', x.lower())
                                          .strip()
                                          .split()[0])
            )
        ),

        Extractor(
            label='previous episode',
            path=".//span[@class='titlereference-overview-episodes-links']//a[contains(text(), 'Previous')]",
            attrs=Attribute(
                key='previous episode',
                path="./@href",
                postprocess=lambda x: analyze_imdbid(x)
            )
        ),

        Extractor(
            label='next episode',
            path=".//span[@class='titlereference-overview-episodes-links']//a[contains(text(), 'Next')]",
            attrs=Attribute(
                key='next episode',
                path="./@href",
                postprocess=lambda x: analyze_imdbid(x)
            )
        ),

        Extractor(
            label='number of seasons',
            path=".//span[@class='titlereference-overview-years-links']/../a[1]",
            attrs=Attribute(
                key='number of seasons',
                path="./text()",
                postprocess=lambda x: int(x)
            )
        ),

        Extractor(
            label='tv series link',
            path=".//a[starts-with(text(), 'All Episodes')]",
            attrs=Attribute(
                key='tv series link',
                path="./@href"
            )
        ),

        Extractor(
            label='akas',
            path="//i[@class='transl']",
            attrs=Attribute(
                key='akas',
                multi=True,
                path='text()',
                postprocess=lambda x: x
                    .replace('  ', ' ')
                    .rstrip('-')
                    .replace('" - ', '"::', 1)
                    .strip('"')
                    .replace('  ', ' ')
            )
        ),

        Extractor(
            label='production notes/status',
            path="//td[starts-with(text(), 'Status:')]/..//div[@class='info-content']",
            attrs=Attribute(
                key='production status',
                path=".//text()",
                postprocess=lambda x: x.strip().split('|')[0].strip().lower()
            )
        ),

        Extractor(
            label='production notes/status updated',
            path="//td[starts-with(text(), 'Status Updated:')]/..//div[@class='info-content']",
            attrs=Attribute(
                key='production status updated',
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='production notes/comments',
            path="//td[starts-with(text(), 'Comments:')]/..//div[@class='info-content']",
            attrs=Attribute(
                key='production comments',
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='production notes/note',
            path="//td[starts-with(text(), 'Note:')]/..//div[@class='info-content']",
            attrs=Attribute(
                key='production note',
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        ),

        Extractor(
            label='blackcatheader',
            group="//b[@class='blackcatheader']",
            group_key="./text()",
            group_key_normalize=lambda x: x.lower(),
            path="../ul/li",
            attrs=Attribute(
                key=None,
                multi=True,
                path={
                    'name': "./a//text()",
                    'comp-link': "./a/@href",
                    'notes': "./text()"
                },
                postprocess=lambda x: Company(name=x.get('name') or '',
                                              companyID=analyze_imdbid(x.get('comp-link')),
                                              notes=(x.get('notes') or '').strip())
            )
        ),

        Extractor(
            label='rating',
            path="(//span[@class='ipl-rating-star__rating'])[1]",
            attrs=Attribute(
                key='rating',
                path="./text()"
            )
        ),

        Extractor(
            label='votes',
            path="//span[@class='ipl-rating-star__total-votes'][1]",
            attrs=Attribute(
                key='votes',
                path="./text()"
            )
        ),

        Extractor(
            label='cover url',
            path="//img[@alt='Poster']",
            attrs=Attribute(
                key='cover url',
                path="@src"
            )
        )
    ]

    preprocessors = [
        ('/releaseinfo">', '"><span imdbpy="airdate">'),
        (re.compile(r'(<b class="blackcatheader">.+?</b>)', re.I), r'</div><div>\1'),
        ('<small>Full cast and crew for<br>', ''),
        ('<td> </td>', '<td>...</td>'),
        (re.compile(r'<span class="tv-extra">TV mini-series(\s+.*?)</span>', re.I),
         r'<span class="tv-extra">TV series\1</span> (mini)'),
        (_reRolesMovie, _manageRoles),
        (_reAkas, _replaceBR)
    ]

    def preprocess_dom(self, dom):
        # Handle series information.
        xpath = self.xpath(dom, "//b[text()='Series Crew']")
        if xpath:
            b = xpath[-1]   # In doubt, take the last one.
            for a in self.xpath(b, "./following::h5/a[@class='glossary']"):
                name = a.get('name')
                if name:
                    a.set('name', 'series %s' % name)
        # Remove links to IMDbPro.
        for proLink in self.xpath(dom, "//span[@class='pro-link']"):
            proLink.drop_tree()
        # Remove some 'more' links (keep others, like the one around
        # the number of votes).
        for tn15more in self.xpath(dom,
                                   "//a[@class='tn15more'][starts-with(@href, '/title/')]"):
            tn15more.drop_tree()
        return dom

    re_space = re.compile(r'\s+')
    re_airdate = re.compile(r'(.*)\s*\(season (\d+), episode (\d+)\)', re.I)

    def postprocess_data(self, data):
        # Convert section names.
        for sect in list(data.keys()):
            if sect in _SECT_CONV:
                data[_SECT_CONV[sect]] = data[sect]
                del data[sect]
                sect = _SECT_CONV[sect]
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
        if 'akas' in data or 'other akas' in data:
            akas = data.get('akas') or []
            other_akas = data.get('other akas') or []
            akas += other_akas
            nakas = []
            for aka in akas:
                aka = aka.strip()
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
            # data['number of seasons'] = seasons[-1] if seasons else len(data['seasons'])
        if 'season/episode' in data:
            tokens = data['season/episode'].split('Episode')
            try:
                data['season'] = int(tokens[0].split('Season')[1])
            except:
                data['season'] = 'unknown'
            try:
                data['episode'] = int(tokens[1])
            except:
                data['episode'] = 'unknown'
            del data['season/episode']
        # if 'original air date' in data:
        #     oid = self.re_space.sub(' ', data['original air date']).strip()
        #     data['original air date'] = oid
        #     aid = self.re_airdate.findall(oid)
        #     if aid and len(aid[0]) == 3:
        #         date, season, episode = aid[0]
        #         date = date.strip()
        #         try:
        #             season = int(season)
        #         except ValueError:
        #             pass
        #         try:
        #             episode = int(episode)
        #         except ValueError:
        #             pass
        #         if date and date != '????':
        #             data['original air date'] = date
        #         else:
        #             del data['original air date']
        #         # Handle also "episode 0".
        #         if season or isinstance(season, int):
        #             data['season'] = season
        #         if episode or isinstance(season, int):
        #             data['episode'] = episode
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
                data['rating'] = float(data['rating'].replace('/10', ''))
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

    Example:
        pparser = HTMLPlotParser()
        result = pparser.parse(plot_summary_html_string)
    """
    _defGetRefs = True

    # Notice that recently IMDb started to put the email of the
    # author only in the link, that we're not collecting, here.
    extractors = [
        Extractor(
            label='plot',
            path="//ul[@id='plot-summaries-content']/li",
            attrs=Attribute(
                key='plot',
                multi=True,
                path={
                    'plot': "./p//text()",
                    'author': ".//div[@class='author-container']//a/text()"
                },
                postprocess=_process_plotsummary
            )
        ),
        Extractor(
            label='synopsis',
            path="//ul[@id='plot-synopsis-content']",
            attrs=Attribute(
                key='synopsis',
                multi=True,
                path=".//li//text()"
            )
        )
    ]

    def preprocess_dom(self, dom):
        for no_summary in self.xpath(dom, "//li[@id='no-summary-content']"):
            no_summary.drop_tree()
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
        notes = notes.strip()
        if notes:
            award['notes'] = notes
    award['anchor'] = x.get('anchor')
    return award


class DOMHTMLAwardsParser(DOMParserBase):
    """Parser for the "awards" page of a given person or movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        awparser = HTMLAwardsParser()
        result = awparser.parse(awards_html_string)
    """
    subject = 'title'
    _containsObjects = True

    extractors = [
        Extractor(
            label='awards',
            group="//table//big",
            group_key="./a",
            path="./ancestor::tr[1]/following-sibling::tr/td[last()][not(@colspan)]",
            attrs=Attribute(
                key=None,
                multi=True,
                path={
                    'year': "../td[1]/a/text()",
                    'result': "../td[2]/b/text()",
                    'award': "../td[3]/text()",
                    'category': "./text()[1]",
                    # FIXME: takes only the first co-recipient
                    'with': "./small[starts-with(text(), 'Shared with:')]/"
                            "following-sibling::a[1]/text()",
                    'notes': "./small[last()]//text()",
                    'anchor': ".//text()"
                },
                postprocess=_process_award
            )
        ),

        Extractor(
            label='recipients',
            group="//table//big",
            group_key="./a",
            path="./ancestor::tr[1]/following-sibling::tr"
                 "/td[last()]/small[1]/preceding-sibling::a",
            attrs=Attribute(
                key=None,
                multi=True,
                path={
                    'name': "./text()",
                    'link': "./@href",
                    'anchor': "..//text()"
                }
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
        for key in list(data.keys()):
            dom = self.get_dom(key)
            assigner = self.xpath(dom, "//a/text()")[0]
            for entry in data[key]:
                if 'name' not in entry:
                    if not entry:
                        continue
                    # this is an award, not a recipient
                    entry['assigner'] = assigner.strip()
                    # find the recipients
                    matches = [p for p in data[key]
                               if 'name' in p and (entry['anchor'] == p['anchor'])]
                    if self.subject == 'title':
                        recipients = [
                            Person(name=recipient['name'],
                                   personID=analyze_imdbid(recipient['link']))
                            for recipient in matches
                        ]
                        entry['to'] = recipients
                    elif self.subject == 'name':
                        recipients = [
                            Movie(title=recipient['name'],
                                  movieID=analyze_imdbid(recipient['link']))
                            for recipient in matches
                        ]
                        entry['for'] = recipients
                    nd.append(entry)
                del entry['anchor']
        return {'awards': nd}


class DOMHTMLTaglinesParser(DOMParserBase):
    """Parser for the "taglines" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = DOMHTMLTaglinesParser()
        result = tparser.parse(taglines_html_string)
    """
    extractors = [
        Extractor(
            label='taglines',
            path="//div[@id='taglines_content']/div",
            attrs=Attribute(
                key='taglines',
                multi=True,
                path=".//text()"
            )
        )
    ]

    def preprocess_dom(self, dom):
        for node in self.xpath(dom, "//div[@id='taglines_content']/div[@class='header']"):
            node.drop_tree()
        for node in self.xpath(dom, "//div[@id='taglines_content']/div[@id='no_content']"):
            node.drop_tree()
        return dom

    def postprocess_data(self, data):
        if 'taglines' in data:
            data['taglines'] = [tagline.strip() for tagline in data['taglines']]
        return data


class DOMHTMLKeywordsParser(DOMParserBase):
    """Parser for the "keywords" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        kwparser = DOMHTMLKeywordsParser()
        result = kwparser.parse(keywords_html_string)
    """
    extractors = [
        Extractor(
            label='keywords',
            path="//a[starts-with(@href, '/keyword/')]",
            attrs=Attribute(
                key='keywords',
                path="./text()", multi=True,
                postprocess=lambda x: x.lower().replace(' ', '-')
            )
        )
    ]


class DOMHTMLAlternateVersionsParser(DOMParserBase):
    """Parser for the "alternate versions" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        avparser = HTMLAlternateVersionsParser()
        result = avparser.parse(alternateversions_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='alternate versions',
            path="//ul[@class='trivia']/li",
            attrs=Attribute(
                key='alternate versions',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.strip()
            )
        )
    ]


class DOMHTMLTriviaParser(DOMParserBase):
    """Parser for the "trivia" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        avparser = HTMLAlternateVersionsParser()
        result = avparser.parse(alternateversions_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='alternate versions',
            path="//div[@class='sodatext']",
            attrs=Attribute(
                key='trivia',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.strip())
        )
    ]

    def preprocess_dom(self, dom):
        # Remove "link this quote" links.
        for qLink in self.xpath(dom, "//span[@class='linksoda']"):
            qLink.drop_tree()
        return dom


class DOMHTMLSoundtrackParser(DOMParserBase):
    _defGetRefs = True
    preprocessors = [('<br />', '\n'), ('<br>', '\n')]
    extractors = [
        Extractor(
            label='soundtrack',
            path="//div[@class='list']//div",
            attrs=Attribute(
                key='soundtrack',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.strip()
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
                for l in ds[1:]:
                    if ' with ' in l or ' by ' in l or ' from ' in l \
                            or ' of ' in l or l.startswith('From '):
                        nds.append(l)
                    else:
                        if nds:
                            nds[-1] += l
                        else:
                            nds.append(l)
                newData[title] = {}
                for l in nds:
                    skip = False
                    for sep in ('From ',):
                        if l.startswith(sep):
                            fdix = len(sep)
                            kind = l[:fdix].rstrip().lower()
                            info = l[fdix:].lstrip()
                            newData[title][kind] = info
                            skip = True
                    if not skip:
                        for sep in ' with ', ' by ', ' from ', ' of ':
                            fdix = l.find(sep)
                            if fdix != -1:
                                fdix = fdix + len(sep)
                                kind = l[:fdix].rstrip().lower()
                                info = l[fdix:].lstrip()
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

    Example:
        ccparser = DOMHTMLCrazyCreditsParser()
        result = ccparser.parse(crazycredits_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='crazy credits',
            path="//ul/li/tt",
            attrs=Attribute(
                key='crazy credits',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.replace('\n', ' ').replace('  ', ' ')
            )
        )
    ]


def _process_goof(x):
    if x['spoiler_category']:
        return x['spoiler_category'].strip() + ': SPOILER: ' + x['text'].strip()
    else:
        return x['category'].strip() + ': ' + x['text'].strip()


class DOMHTMLGoofsParser(DOMParserBase):
    """Parser for the "goofs" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = DOMHTMLGoofsParser()
        result = gparser.parse(goofs_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='goofs',
            path="//div[@class='soda odd']",
            attrs=Attribute(
                key='goofs',
                multi=True,
                path={
                    'text': "./text()",
                    'category': './preceding-sibling::h4[1]/text()',
                    'spoiler_category': './h4/text()'
                },
                postprocess=_process_goof
            )
        )
    ]


class DOMHTMLQuotesParser(DOMParserBase):
    """Parser for the "memorable quotes" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        qparser = DOMHTMLQuotesParser()
        result = qparser.parse(quotes_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='quotes_odd',
            path="//div[@class='quote soda odd']",
            attrs=Attribute(
                key='quotes_odd',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x
                    .strip()
                    .replace(' \n', '::')
                    .replace('::\n', '::')
                    .replace('\n', ' ')
            )
        ),

        Extractor(
            label='quotes_even',
            path="//div[@class='quote soda even']",
            attrs=Attribute(
                key='quotes_even',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x
                    .strip()
                    .replace(' \n', '::')
                    .replace('::\n', '::')
                    .replace('\n', ' ')
            )
        )
    ]

    preprocessors = [
        (re.compile('<a href="#" class="hidesoda hidden">Hide options</a><br>', re.I), '')
    ]

    def preprocess_dom(self, dom):
        # Remove "link this quote" links.
        for qLink in self.xpath(dom, "//span[@class='linksoda']"):
            qLink.drop_tree()
        for qLink in self.xpath(dom, "//div[@class='sharesoda_pre']"):
            qLink.drop_tree()
        return dom

    def postprocess_data(self, data):
        quotes = data.get('quotes_odd', []) + data.get('quotes_even', [])
        if not quotes:
            return {}
        quotes = [q.split('::') for q in quotes]
        return {'quotes': quotes}


class DOMHTMLReleaseinfoParser(DOMParserBase):
    """Parser for the "release dates" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rdparser = DOMHTMLReleaseinfoParser()
        result = rdparser.parse(releaseinfo_html_string)
    """
    extractors = [
        Extractor(
            label='release dates',
            path="//table[@id='release_dates']//tr",
            attrs=Attribute(
                key='release dates',
                multi=True,
                path={
                    'country': ".//td[1]//text()",
                    'date': ".//td[2]//text()",
                    'notes': ".//td[3]//text()"
                }
            )
        ),

        Extractor(
            label='akas',
            path="//table[@id='akas']//tr",
            attrs=Attribute(
                key='akas',
                multi=True,
                path={
                    'title': "./td[1]/text()",
                    'countries': "./td[2]/text()"}
            )
        )
    ]

    preprocessors = [
        (re.compile('(<h5><a name="?akas"?.*</table>)', re.I | re.M | re.S),
         r'<div class="_imdbpy_akas">\1</div>')
    ]

    def postprocess_data(self, data):
        if not ('release dates' in data or 'akas' in data):
            return data
        releases = data.get('release dates') or []
        rl = []
        for i in releases:
            country = i.get('country')
            date = i.get('date')
            if not (country and date):
                continue
            country = country.strip()
            date = date.strip()
            if not (country and date):
                continue
            notes = i['notes']
            info = '%s::%s' % (country, date)
            if notes:
                info += notes
            rl.append(info)
        if releases:
            del data['release dates']
        if rl:
            data['release dates'] = rl
        akas = data.get('akas') or []
        nakas = []
        for aka in akas:
            title = (aka.get('title') or '').strip()
            if not title:
                continue
            countries = (aka.get('countries') or '').split(',')
            if not countries:
                nakas.append(title)
            else:
                for country in countries:
                    nakas.append('%s::%s' % (title, country.strip()))
        if akas:
            del data['akas']
        if nakas:
            data['akas from release info'] = nakas
        return data


class DOMHTMLRatingsParser(DOMParserBase):
    """Parser for the "user ratings" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rparser = DOMHTMLRatingsParser()
        result = rparser.parse(userratings_html_string)
    """
    re_means = re.compile('mean\s*=\s*([0-9]\.[0-9])\s*median\s*=\s*([0-9])', re.I)

    extractors = [
        Extractor(
            label='number of votes',
            path="//th[@class='firstTableCoulmn']/../../tr",
            attrs=[
                Attribute(
                    key='votes',
                    multi=True,
                    path={
                        'ordinal': "td[1]/div//text()",
                        'votes': "td[3]/div/div//text()"
                    }
                )
            ]
        ),

        Extractor(
            label='mean and median',
            path="//div[starts-with(normalize-space(text()), 'Arithmetic mean')]",
            attrs=Attribute(
                key='mean and median',
                path="normalize-space(text())"
            )
        ),

        Extractor(
            label='demographics',
            path="//div[@class='smallcell']",
            attrs=Attribute(
                key='demographics',
                multi=True,
                path={
                    'link': "a/@href",
                    'rating': "..//div[@class='bigcell']//text()",
                    'votes': "a/text()"
                }
            )
        )
    ]

    def postprocess_data(self, data):
        nd = {}
        demographics = data.get('demographics')
        if demographics:
            dem = {}
            for dem_data in demographics:
                link = (dem_data.get('link') or '').strip()
                votes = (dem_data.get('votes') or '').strip()
                rating = (dem_data.get('rating') or '').strip()
                if not (link and votes and rating):
                    continue
                eq_idx = link.rfind('=')
                if eq_idx == -1:
                    continue
                info = link[eq_idx + 1:].replace('_', ' ')
                try:
                    votes = int(votes.replace(',', ''))
                except Exception:
                    continue
                try:
                    rating = float(rating)
                except Exception:
                    continue
                dem[info] = {'votes': votes, 'rating': rating}
            nd['demographics'] = dem
        votes = data.get('votes', [])
        if votes:
            nd['number of votes'] = {}
            for v_info in votes:
                ordinal = v_info.get('ordinal')
                nr_votes = v_info.get('votes')
                if not (ordinal and nr_votes):
                    continue
                try:
                    ordinal = int(ordinal)
                except Exception:
                    continue
                try:
                    nr_votes = int(nr_votes.replace(',', ''))
                except Exception:
                    continue
                nd['number of votes'][ordinal] = nr_votes
        mean = data.get('mean and median', '')
        if mean:
            means = self.re_means.findall(mean)
            if means and len(means[0]) == 2:
                am, med = means[0]
                try:
                    am = float(am)
                except (ValueError, OverflowError):
                    pass
                if isinstance(am, float):
                    nd['arithmetic mean'] = am
                try:
                    med = int(med)
                except (ValueError, OverflowError):
                    pass
                if isinstance(med, int):
                    nd['median'] = med
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

    Example:
        osparser = DOMHTMLCriticReviewsParser()
        result = osparser.parse(officialsites_html_string)
    """
    kind = 'critic reviews'

    extractors = [
        Extractor(
            label='metascore',
            path="//div[@class='metascore_wrap']/div/span",
            attrs=Attribute(
                key='metascore',
                path=".//text()"
            )
        ),

        Extractor(
            label='metacritic url',
            path="//div[@class='article']/div[@class='see-more']/a",
            attrs=Attribute(
                key='metacritic url',
                path="./@href"
            )
        )
    ]


class DOMHTMLReviewsParser(DOMParserBase):
    """Parser for the "reviews" pages of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        osparser = DOMHTMLReviewsParser()
        result = osparser.parse(officialsites_html_string)
    """
    kind = 'reviews'

    extractors = [
        Extractor(
            label='review',
            path="//div[@class='review-container']",
            attrs=Attribute(
                key='self.kind',
                multi=True,
                path={
                    'text': ".//div[@class='text']//text()",
                    'helpful': ".//div[@class='text-muted']/text()[1]",
                    'title': ".//div[@class='title']//text()",
                    'author': ".//span[@class='display-name-link']/a/@href",
                    'date': ".//span[@class='review-date']//text()",
                    'rating': ".//span[@class='point-scale']/preceding-sibling::span[1]/text()"
                },
                postprocess=lambda x: ({
                    'content': (x['text'] or '').replace("\n", " ").replace('  ', ' ').strip(),
                    'helpful': [int(s) for s in (x.get('helpful') or '').split() if s.isdigit()],
                    'title': (x.get('title') or '').strip(),
                    'author': analyze_imdbid(x.get('author')),
                    'date': (x.get('date') or '').strip(),
                    'rating': (x.get('rating') or '').strip()
                })
            )
        )
    ]

    preprocessors = [('<br>', '<br>\n')]

    def postprocess_data(self, data):
        for review in data.get('reviews', []):
            if review.get('rating') and len(review['rating']) == 2:
                review['rating'] = int(review['rating'][0])
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

    Example:
        osparser = DOMHTMLFullCreditsParser()
        result = osparser.parse(officialsites_html_string)
    """
    kind = 'full credits'

    extractors = [
        Extractor(
            label='cast',
            path="//table[@class='cast_list']//tr[@class='odd' or @class='even']",
            attrs=Attribute(
                key="cast",
                multi=True,
                path={
                    'person': ".//text()",
                    'link': "td[2]/a/@href",
                    'roleID': "td[4]//div[@class='_imdbpyrole']/@roleid"
                },
                postprocess=lambda x: build_person(
                    x.get('person') or '',
                    personID=analyze_imdbid(x.get('link')),
                    roleID=(x.get('roleID') or '').split('/')
                )
            )
        ),
    ]

    preprocessors = [
        (_reRolesMovie, _manageRoles)
    ]


class DOMHTMLOfficialsitesParser(DOMParserBase):
    """Parser for the "official sites", "external reviews"
    "miscellaneous links", "sound clips", "video clips" and
    "photographs" pages of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        osparser = DOMHTMLOfficialsitesParser()
        result = osparser.parse(officialsites_html_string)
    """
    extractors = [
        Extractor(
            label='site',
            group="//h4[@class='li_group']",
            group_key="./text()",
            group_key_normalize=lambda x: x.strip().lower(),
            path="./following::ul[1]/li/a",
            attrs=Attribute(
                key=None,
                multi=True,
                path={
                    'link': "./@href",
                    'info': "./text()"
                },
                postprocess=lambda x: (
                    x.get('info').strip(),
                    urllib.parse.unquote(_normalize_href(x.get('link')))
                )
            )
        )
    ]


class DOMHTMLConnectionParser(DOMParserBase):
    """Parser for the "connections" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        connparser = DOMHTMLConnectionParser()
        result = connparser.parse(connections_html_string)
    """
    _containsObjects = True

    extractors = [
        Extractor(
            label='connection',
            group="//div[@class='_imdbpy']",
            group_key="./h5/text()",
            group_key_normalize=lambda x: x.lower(),
            path="./a",
            attrs=Attribute(
                key=None,
                path={
                    'title': "./text()",
                    'movieID': "./@href"
                },
                multi=True
            )
        )
    ]

    preprocessors = [
        ('<h5>', '</div><div class="_imdbpy"><h5>'),
        # To get the movie's year.
        ('</a> (', ' ('),
        ('\n<br/>', '</a>'),
        ('<br/> - ', '::')
    ]

    def postprocess_data(self, data):
        for key in list(data.keys()):
            nl = []
            for v in data[key]:
                title = v['title']
                ts = title.split('::', 1)
                title = ts[0].strip()
                notes = ''
                if len(ts) == 2:
                    notes = ts[1].strip()
                m = Movie(title=title, movieID=analyze_imdbid(v['movieID']),
                          accessSystem=self._as, notes=notes, modFunct=self._modFunct)
                nl.append(m)
            data[key] = nl
        if not data:
            return {}
        return {'connections': data}


class DOMHTMLLocationsParser(DOMParserBase):
    """Parser for the "locations" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        lparser = DOMHTMLLocationsParser()
        result = lparser.parse(locations_html_string)
    """
    extractors = [
        Extractor(
            label='locations',
            path="//dt",
            attrs=Attribute(
                key='locations',
                multi=True,
                path={
                    'place': ".//text()",
                    'note': "./following-sibling::dd[1]//text()"
                },
                postprocess=lambda x: (
                    '%s::%s' % (
                        x['place'].strip(),
                        (x['note'] or '').strip()
                    )
                ).strip(':')
            )
        )
    ]


class DOMHTMLTechParser(DOMParserBase):
    """Parser for the "technical", "publicity" (for people) and "contacts" (for people)
    pages of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = HTMLTechParser()
        result = tparser.parse(technical_html_string)
    """
    kind = 'tech'
    re_space = re.compile(r'\s+')

    extractors = [
        Extractor(
            label='tech',
            group="//table//tr/td[@class='label']",
            group_key="./text()",
            group_key_normalize=lambda x: x.lower().strip(),
            path=".",
            attrs=Attribute(
                key=None,
                path="..//td[2]//text()",
                postprocess=lambda x: [t.strip() for t in x.split(':::') if t.strip()]
            )
        )
    ]

    preprocessors = [
        (re.compile('(<h5>.*?</h5>)', re.I), r'</div>\1<div class="_imdbpy">'),
        (re.compile('((<br/>|</p>|</table>))\n?<br/>(?!<a)', re.I), r'\1</div>'),
        # the ones below are for the publicity parser
        (re.compile('<p>(.*?)</p>', re.I), r'\1<br/>'),
        (re.compile('(</td><td valign="top">)', re.I), r'\1::'),
        (re.compile('(</tr><tr>)', re.I), r'\n\1'),
        (re.compile('<span class="ghost">\|</span>', re.I), r':::'),
        (re.compile('<br/?>', re.I), r':::')
        # this is for splitting individual entries
    ]

    def postprocess_data(self, data):
        for key in data:
            data[key] = [x for x in data[key] if x != '|']
            data[key] = [self.re_space.sub(' ', x).strip() for x in data[key]]
            data[key] = [_f for _f in data[key] if _f]
        if self.kind == 'contacts' and data:
            data = {self.kind: data}
        else:
            if self.kind == 'publicity':
                if 'biography (print)' in data:
                    data['biography-print'] = data['biography (print)']
                    del data['biography (print)']
            # Tech info.
            for key in list(data.keys()):
                if key.startswith('film negative format'):
                    data['film negative format'] = data[key]
                    del data[key]
                elif key.startswith('film length'):
                    data['film length'] = data[key]
                    del data[key]
        return data


class DOMHTMLNewsParser(DOMParserBase):
    """Parser for the "news" page of a given movie or person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        nwparser = DOMHTMLNewsParser()
        result = nwparser.parse(news_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='news',
            path="//h2",
            attrs=Attribute(
                key='news',
                multi=True,
                path={
                    'title': "./text()",
                    'fromdate': "../following-sibling::p[1]/small//text()",
                    # FIXME: sometimes (see The Matrix (1999)) <p> is found
                    #        inside news text.
                    'body': "../following-sibling::p[2]//text()",
                    'link': "../..//a[text()='Permalink']/@href",
                    'fulllink': "../..//a[starts-with(text(), 'See full article at')]/@href"
                },
                postprocess=lambda x: {
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


class DOMHTMLSeasonEpisodesParser(DOMParserBase):
    """Parser for the "episode list" page of a given movie.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = DOMHTMLSeasonEpisodesParser()
        result = sparser.parse(episodes_html_string)
    """

    extractors = [
        Extractor(
            label='series link',
            path="//div[@class='parent']",
            attrs=[
                Attribute(
                    key='series link',
                    path=".//a/@href"
                )
            ]
        ),

        Extractor(
            label='series title',
            path="//head/meta[@property='og:title']",
            attrs=[
                Attribute(
                    key='series title',
                    path="./@content"
                )
            ]
        ),

        Extractor(
            label='seasons list',
            path="//select[@id='bySeason']//option",
            attrs=[
                Attribute(
                    key='_seasons',
                    multi=True,
                    path="./@value"
                )
            ]
        ),

        Extractor(
            label='selected season',
            path="//select[@id='bySeason']//option[@selected]",
            attrs=[
                Attribute(
                    key='_current_season',
                    path='./@value'
                )
            ]
        ),

        Extractor(
            label='episodes',
            path=".",
            group="//div[@class='info']",
            group_key=".//meta/@content",
            group_key_normalize=lambda x: 'episode %s' % x,
            attrs=[
                Attribute(
                    key=None,
                    multi=True,
                    path={
                        "link": ".//strong//a[@href][1]/@href",
                        "original air date": ".//div[@class='airdate']/text()",
                        "title": ".//strong//text()",
                        "rating": ".//div[@class='ipl-rating-star '][1]" +
                                    "/span[@class='ipl-rating-star__rating'][1]/text()",
                        "votes": ".//div[contains(@class, 'ipl-rating-star')][1]" +
                                    "/span[@class='ipl-rating-star__total-votes'][1]/text()",
                        "plot": ".//div[@class='item_description']//text()"
                    }
                )
            ]
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
        for episode_nr, episode in data.items():
            if not (episode and episode[0] and
                    episode_nr.startswith('episode ')):
                continue
            episode = episode[0]
            episode_nr = episode_nr[8:].rstrip()
            try:
                episode_nr = int(episode_nr)
            except ValueError:
                pass
            episode_id = analyze_imdbid(episode.get('link' ''))
            episode_air_date = episode.get('original air date', '').strip()
            episode_title = episode.get('title', '').strip()
            episode_plot = episode.get('plot', '')
            episode_rating = episode.get('rating', '')
            episode_votes = episode.get('votes', '')
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
                except:
                    pass
            if episode_votes:
                try:
                    ep_obj['votes'] = int(episode_votes.replace(',', '')
                                          .replace('.', '').replace('(', '').replace(')', ''))
                except:
                    pass
            if episode_air_date:
                ep_obj['original air date'] = episode_air_date
                if episode_air_date[-4:].isdigit():
                    ep_obj['year'] = episode_air_date[-4:]
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

    Example:
        eparser = DOMHTMLEpisodesParser()
        result = eparser.parse(episodes_html_string)
    """
    # XXX: no more used for the list of episodes parser,
    #      but only for the episodes cast parser (see below).
    _containsObjects = True

    kind = 'episodes list'
    _episodes_path = "..//h4"
    _oad_path = "./following-sibling::span/strong[1]/text()"

    def _init(self):
        self.extractors = [
            Extractor(
                label='series',
                path="//html",
                attrs=[
                    Attribute(
                        key='series title',
                        path=".//title/text()"
                    ),
                    Attribute(
                        key='series movieID',
                        path=".//h1/a[@class='main']/@href",
                        postprocess=analyze_imdbid
                    )
                ]
            ),
            Extractor(
                label='episodes',
                group="//div[@class='_imdbpy']/h3",
                group_key="./a/@name",
                path=self._episodes_path,
                attrs=Attribute(
                    key=None,
                    multi=True,
                    path={
                        'link': "./a/@href",
                        'title': "./a/text()",
                        'year': "./preceding-sibling::a[1]/@name",
                        'episode': "./text()[1]",
                        'oad': self._oad_path,
                        'plot': "./following-sibling::text()[1]"
                    },
                    postprocess=_build_episode
                )
            )
        ]

        if self.kind == 'episodes cast':
            self.extractors += [
                Extractor(
                    label='cast',
                    group="//h4",
                    group_key="./text()[1]",
                    group_key_normalize=lambda x: x.strip(),
                    path="./following-sibling::table[1]//td[@class='nm']",
                    attrs=Attribute(
                        key=None,
                        multi=True,
                        path={
                            'person': "..//text()",
                            'link': "./a/@href",
                            'roleID': "../td[4]//div[@class='_imdbpyrole']/@roleid"
                        },
                        postprocess=lambda x: build_person(
                            x.get('person') or '',
                            personID=analyze_imdbid(x.get('link')),
                            roleID=(x.get('roleID') or '').split('/'),
                            accessSystem=self._as,
                            modFunct=self._modFunct
                        )
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

    Example:
        fparser = DOMHTMLFaqsParser()
        result = fparser.parse(faqs_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(
            label='faqs',
            path="//div[@class='section']",
            attrs=Attribute(
                key='faqs',
                multi=True,
                path={
                    'question': "./h3/a/span/text()",
                    'answer': "../following-sibling::div[1]//text()"
                },
                postprocess=lambda x: '%s::%s' % (
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

    Example:
        aparser = DOMHTMLAiringParser()
        result = aparser.parse(airing_html_string)
    """
    _containsObjects = True

    extractors = [
        Extractor(
            label='series title',
            path="//title",
            attrs=Attribute(
                key='series title',
                path="./text()",
                postprocess=lambda x: x.replace(' - TV schedule', '')
            )
        ),

        Extractor(
            label='series id',
            path="//h1/a[@href]",
            attrs=Attribute(
                key='series id',
                path="./@href"
            )
        ),

        Extractor(
            label='tv airings',
            path="//tr[@class]",
            attrs=Attribute(
                key='airing',
                multi=True,
                path={
                    'date': "./td[1]//text()",
                    'time': "./td[2]//text()",
                    'channel': "./td[3]//text()",
                    'link': "./td[4]/a[1]/@href",
                    'title': "./td[4]//text()",
                    'season': "./td[5]//text()",
                },
                postprocess=lambda x: {
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

    Example:
        pgparser = HTMLParentsGuideParser()
        result = pgparser.parse(parentsguide_html_string)
    """
    extractors = [
        Extractor(
            label='parents guide',
            group="//div[@class='section']",
            group_key="./h3/a/span/text()",
            group_key_normalize=lambda x: x.lower(),
            path="../following-sibling::div[1]/p",
            attrs=Attribute(
                key=None,
                path=".//text()",
                postprocess=lambda x: [
                    t.strip().replace('\n', ' ') for t in x.split('||') if t.strip()
                ]
            )
        )
    ]

    preprocessors = [
        (re.compile('<br/><br/>', re.I), r'||')
    ]

    def postprocess_data(self, data):
        data2 = {}
        for key in data:
            if data[key]:
                data2[key] = data[key]
        if not data2:
            return {}
        return {'parents guide': data2}


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
    'connections_parser': ((DOMHTMLConnectionParser,), None),
    'tech_parser': ((DOMHTMLTechParser,), None),
    'locations_parser': ((DOMHTMLLocationsParser,), None),
    'news_parser': ((DOMHTMLNewsParser,), None),
    'episodes_parser': ((DOMHTMLEpisodesParser,), None),
    'season_episodes_parser': ((DOMHTMLSeasonEpisodesParser,), None),
    'movie_faqs_parser': ((DOMHTMLFaqsParser,), None),
    'airing_parser': ((DOMHTMLAiringParser,), None),
    'parentsguide_parser': ((DOMHTMLParentsGuideParser,), None)
}
