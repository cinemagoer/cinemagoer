"""
parser.http.characterParser module (imdb package).

This module provides the classes (and the instances), used to parse
the IMDb pages on the akas.imdb.com server about a character.
E.g., for "Jesse James" the referred pages would be:
    main details:   http://www.imdb.com/character/ch0000001/
    biography:      http://www.imdb.com/character/ch0000001/bio
    ...and so on...

Copyright 2007-2008 Davide Alberani <da@erlug.linux.it>

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

from utils import ParserBase
from imdb.Movie import Movie

class HTMLCharacterBioParser(ParserBase):
    """Parser for the "biography" page of a given character.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        bparser = HTMLCharacterBioParser()
        result = bparser.parse(character_biography_html_string)
    """
    _defGetRefs = True

    def _reset(self):
        self._bios = []
        self._intro = u''
        self._in_wiki_cont = False
        self._in_h4 = False
        self._cur_bio = u''
        self._title = u''
        self._in_table = False

    def get_data(self):
        res = {}
        if self._bios: res['biography'] = self._bios
        if self._intro: res['introduction'] = self._intro
        if not res: return {}
        return res

    def start_div(self, attrs):
        if not self._in_content: return
        cls = self.get_attr_value(attrs, 'class')
        if not cls: return
        clss = cls.strip().lower()
        if clss == 'display':
            style = self.get_attr_value(attrs, 'style')
            if not style:
                self._in_wiki_cont = True
            else:
                self._in_wiki_cont = False
                self._add_item()

    def start_h4(self, attrs):
        if not self._in_wiki_cont: return
        self._in_h4 = True
        self._add_item()

    def end_h4(self):
        if not self._in_wiki_cont: return
        self._in_h4 = False

    def _add_item(self):
        self._title = self._title.strip()
        self._cur_bio = self._cur_bio.strip()
        if not (self._title and self._cur_bio):
            if self._cur_bio and not self._title:
                self._intro = self._cur_bio
            self._title = u''
            self._cur_bio = u''
            return
        self._bios.append('%s::%s' % (self._title, self._cur_bio))
        self._title = u''
        self._cur_bio = u''

    def start_table(self, attrs):
        if not self._in_wiki_cont: return
        self._in_table = True

    def end_table(self):
        if not self._in_wiki_cont: return
        self._in_table = False

    def do_br(self, attrs):
        if not self._in_wiki_cont: return
        if self._in_table: return
        self._cur_bio += '\n'

    def _handle_data(self, data):
        if not self._in_wiki_cont: return
        if self._in_h4:
            self._title += data
        elif not self._in_table:
            self._cur_bio += data.replace('\n', ' ')


class HTMLCharacterQuotesParser(ParserBase):
    """Parser for the "quotes" page of a given character.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        qparser = HTMLCharacterQuotesParser()
        result = qparser.parse(character_quotes_html_string)
    """
    _defGetRefs = True

    def _reset(self):
        """Reset the parser."""
        self._tot_quotes = {}
        self._quotes = [u'']
        self._cur_title = u''
        self._cur_titleID = None
        self._in_quote = False
        self._in_title = False
        self._seen_br = False

    def get_data(self):
        """Return the dictionary."""
        if not self._tot_quotes: return {}
        return {'quotes': self._tot_quotes}

    def start_a(self, attrs):
        if not self._in_quote: return
        if not self._in_title: return
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        curid = self.re_imdbID.findall(href)
        if curid:
            self._cur_titleID = curid[-1]

    def end_a(self): pass

    def start_h5(self, attrs):
        if not self._in_content: return
        self._add_items()
        self._in_title = True
        self._cur_title = u''
        self._cur_titleID = None
        self._in_quote = True

    def end_h5(self):
        self._in_title = False

    def _add_items(self):
        self._quotes = [x.replace(':: ', '::').replace(' ::', '::').rstrip(':')
                        for x in self._quotes]
        self._quotes = [x.replace('   ', ' ').replace('  ', ' ').strip()
                        for x in self._quotes]
        self._quotes = filter(None, self._quotes)
        if not (self._cur_title and self._cur_titleID and self._quotes):
            self._quotes = [u'']
            return
        movie = Movie(title=self._cur_title, movieID=self._cur_titleID,
                        accessSystem=self._as, modFunct=self._modFunct)
        self._tot_quotes[movie] = self._quotes[:]
        self._quotes = [u'']

    def do_br(self, attrs):
        if not self._in_quote: return
        clear = self.get_attr_value(attrs, 'clear')
        if clear and clear.lower() == 'both':
            self._add_items()
            self._in_quote = False
        if self._seen_br:
            self._quotes.append(u'')
            self._seen_br = False
        else:
            self._quotes[-1] = self._quotes[-1].rstrip()
            if not self._quotes[-1].endswith('::'):
                self._quotes[-1] += '::'
        self._seen_br = True

    def _handle_data(self, data):
        if not self._in_quote: return
        self._seen_br = False
        if self._in_title:
            self._cur_title += data
        else:
            self._quotes[-1] += data


from personParser import HTMLMaindetailsParser
from personParser import HTMLSeriesParser

_OBJECTS = {
    'character_main_parser': (HTMLMaindetailsParser, {'kind': 'character'}),
    'character_series_parser': (HTMLSeriesParser, None),
    'character_bio_parser': (HTMLCharacterBioParser, None),
    'character_quotes_parser': (HTMLCharacterQuotesParser, None)
}

