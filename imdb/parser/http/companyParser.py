"""
parser.http.companyParser module (imdb package).

This module provides the classes (and the instances), used to parse
the IMDb pages on the akas.imdb.com server about a company.
E.g., for "Columbia Pictures [us]" the referred page would be:
    main details:   http://akas.imdb.com/company/co0071509/

Copyright 2008 Davide Alberani <da@erlug.linux.it>
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

import re
from utils import ParserBase, build_movie
from utils import Attribute, Extractor, DOMParserBase, analyze_imdbid

from imdb.utils import analyze_company_name


class CompanyParser(ParserBase):
    """Parser for the main page of a given company.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        cparser = CompanyParser()
        result = cparser.parse(company_html_string)
    """
    def _reset(self):
        self._in_title = False
        self._seen_a_in_b = False
        self._in_b = False
        self._in_li = False
        self._in_filmogr = False
        self._in_section_name = False
        self._data = {}
        self._title = u''
        self._section = u''
        self._cur_item = u''
        self._last_movieid = None

    def get_data(self):
        self._title = self._title.strip()
        if self._title:
            self._data.update(analyze_company_name(self._title))
        return self._data

    def start_title(self, attrs):
        self._in_title = True

    def end_title(self):
        self._in_title = False

    def start_b(self, attrs):
        self._in_b = True
        self._seen_a_in_b = False
        self._section = u''
        self._last_movieid = None

    def end_b(self):
        self._in_b = False
        if self._seen_a_in_b:
            self._seen_a_in_b = False
            self._section = self._section.strip().lower()
            if not self._section.endswith('- filmography'):
                self._section = u''
                return
            self._section = self._section[:-13].rstrip()
            if not self._section: return
            self._section = self._section.replace('company', 'companies')
            self._section = self._section.replace('other', 'miscellaneous')
            self._section = self._section.replace('distributor', 'distributors')

    def start_a(self, attrs):
        if self._in_b:
            self._seen_a_in_b = True
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        if '/title/tt' not in href: return
        mid = self.re_imdbID.findall(href)
        if not mid: return
        self._last_movieid = mid[-1]

    def end_a(self): pass

    def start_li(self, attrs):
        self._in_li = True

    def end_li(self):
        self._cur_item = self._cur_item.strip()
        if self._section and self._in_li and self._last_movieid \
                and self._cur_item:
            self._in_li = False
            kwds = {'movieID': self._last_movieid, 'modFunct': self._modFunct,
                    'accessSystem': self._as, '_parsingCompany': True}
            movie = build_movie(self._cur_item, **kwds)
            if movie:
                self._data.setdefault(self._section, []).append(movie)
        self._cur_item = u''
        self._last_movieid = None

    def _handle_data(self, data):
        if self._in_title:
            self._title += data
            return
        if self._in_b and self._seen_a_in_b:
            self._section += data
        elif self._section and self._in_li:
            self._cur_item += data


class DOMCompanyParser(DOMParserBase):
    """Parser for the main page of a given company.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        cparser = DOMCompanyParser()
        result = cparser.parse(company_html_string)
    """
    _containsObjects = True

    extractors = [
            Extractor(label='name',
                        path="//title",
                        attrs=Attribute(key='name',
                            path="./text()",
                        postprocess=lambda x: \
                                analyze_company_name(x, stripNotes=True))),

            Extractor(label='filmography',
                        group="//b/a[@name]",
                        group_key="./text()",
                        group_key_normalize=lambda x: x.lower(),
                        path="../following-sibling::ol[1]/li",
                        attrs=Attribute(key=None,
                            multi=True,
                            path={
                                'link': "./a[1]/@href",
                                'title': "./a[1]/text()",
                                'year': "./text()[1]"
                                },
                            postprocess=lambda x:
                                build_movie(u'%s %s' % \
                                (x.get('title'), x.get('year').strip()),
                                movieID=analyze_imdbid(x.get('link') or u''),
                                _parsingCompany=True))),
            ]

    preprocessors = [
        (re.compile('(<b><a name=)', re.I), r'</p>\1')
        ]

    def postprocess_data(self, data):
        for key in data.keys():
            new_key = key.replace('company', 'companies')
            new_key = new_key.replace('other', 'miscellaneous')
            new_key = new_key.replace('distributor', 'distributors')
            if new_key != key:
                data[new_key] = data[key]
                del data[key]
        return data


_OBJECTS = {
    'company_main_parser': ((DOMCompanyParser, CompanyParser), None)
}

