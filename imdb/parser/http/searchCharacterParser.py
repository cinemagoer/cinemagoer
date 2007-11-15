"""
parser.http.searchCharacterParser module (imdb package).

This module provides the HTMLSearchCharacterParser class (and the
search_character_parser instance), used to parse the results of a search
for a given character.
E.g., when searching for the name "Jesse James", the parsed page would be:
    http://akas.imdb.com/find?s=Characters;mx=20;q=Jesse+James

Copyright 2007 Davide Alberani <da@erlug.linux.it>

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

from imdb.utils import analyze_name
from utils import ParserBase


# XXX: not sure it's still useful, with the new search system.
#      Anyway, it's used by the local access system, to get the imdbID.
class BasicCharacterParser(ParserBase):
    """Simply get the name of a character and the imdbID.

    It's used by the HTMLSearchCharacterParser class to return a result
    for a direct match (when a search on IMDb results in a single
    character, the web server sends directly the character page.
    """
    def _reset(self):
        """Reset the parser."""
        self._in_title = 0
        self._name = u''
        self._result = []

    def get_data(self):
        """Return a list with a single tuple (imdb, {title_dict})."""
        return self._result

    def start_title(self, attrs):
        self._in_title = 1

    def end_title(self):
        self._in_title = 0

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        href = href.lower()
        if '/character/ch' in href and href.endswith('bio'):
            rpid = self.re_imdbID.findall(href)
            if rpid and self._name:
                n = self._name.replace('(Character)', '').strip()
                pid = str(rpid[-1])
                d = analyze_name(n, canonical=0)
                res = [(pid, d)]
                self.reset()
                self._result = res

    def end_a(self): pass

    def _handle_data(self, data):
        if self._in_title:
            self._name += data


from searchMovieParser import HTMLSearchMovieParser as HTMLSearchCharacterParser

_OBJECTS = {
        'search_character_parser': (HTMLSearchCharacterParser,
                {'kind': 'character', '_basic_parser': BasicCharacterParser})
}

