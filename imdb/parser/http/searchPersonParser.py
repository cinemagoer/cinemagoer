"""
parser.http.searchPersonParser module (imdb package).

This module provides the HTMLSearchPersonParser class (and the
search_person_parser instance), used to parse the results of a search
for a given person.
E.g., when searching for the name "Mel Gibson", the parsed page would be:
    http://akas.imdb.com/find?q=Mel+Gibson&nm=on&mx=20

Copyright 2004-2007 Davide Alberani <da@erlug.linux.it>

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
class BasicPersonParser(ParserBase):
    """Simply get the name of a person and the imdbID.

    It's used by the HTMLSearchPersonParser class to return a result
    for a direct match (when a search on IMDb results in a single
    person, the web server sends directly the person page.
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
        # XXX: Since July 2004, IMDb has removed the "pageflicker",
        #      so we've to gather the imdbID from the "IMDb message board"
        #      link.
        if href.startswith('/name/nm') and \
                href.find('/board') != -1:
            rpid = self.re_imdbID.findall(href)
            if rpid and self._name:
                n = self._name.strip()
                if n.find('IMDb Name') != -1 and n.find('Search') != -1:
                    return
                pid = str(rpid[-1])
                d = analyze_name(n, canonical=1)
                res = [(pid, d)]
                self.reset()
                self._result = res

    def end_a(self): pass

    def _handle_data(self, data):
        if self._in_title:
            self._name += data


class HTMLSearchPersonParser(ParserBase):
    """Parse the html page that the IMDb web server shows when the
    "new search system" is used.
    """
    def _reset(self):
        """Reset the parser."""
        self._begin_list = 0
        self._results = []
        self._in_title = 0
        self._in_list = 0
        self._current_imdbID = u''
        self._is_name = 0
        self._name = u''
        self._no_more = 0
        self._stop = 0

    def parse(self, cont, results=None, **kwds):
        self.maxres = results
        return ParserBase.parse(self, cont)

    def get_data(self):
        """Return a list of tuples (imdbID, {name_dict})."""
        return self._results

    def start_title(self, attrs):
        self._in_title = 1

    def end_title(self):
        self._in_title = 0

    def start_ol(self, attrs):
        self._in_list = 1

    def end_ol(self):
        self._in_list = 0

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if href and href.lower().startswith('/name'):
            nr = self.re_imdbID.findall(href[6:])
            if not nr: return
            self._current_imdbID = str(nr[0])
            self._is_name = 1

    def end_a(self): pass

    def start_small(self, attrs):
        self._no_more = 1

    def end_small(self): pass

    def start_li(self, attrs): pass

    def end_li(self):
        if self._in_list and self._is_name and self._current_imdbID \
                and self._name:
            res = {}
            d = analyze_name(self._name.strip(), canonical=1)
            res.update(d)
            self._results.append((self._current_imdbID.strip(), d))
            if self.maxres is not None and self.maxres <= len(self._results):
                self._stop = 1
            self._name = u''
            self._current_imdbID = u''
            self._is_name = 0
            self._in_name = 0
        self._no_more = 0

    def _handle_data(self, data):
        if self._stop:
            res = self._results
            self.reset()
            self._results = res
            return
        sldata = data.strip().lower()
        if self._in_title:
            dls = data.strip().lower()
            if not dls.startswith('imdb name'):
                # A direct hit!
                rawdata = self.rawdata
                self.reset()
                bpp = BasicPersonParser()
                self._results = bpp.parse(rawdata)['data']
        elif self._in_list and self._is_name and not self._no_more:
            self._name += data
        elif sldata.find('exact match') != -1 or \
                sldata.find('partial match') != -1 or \
                sldata.find('approx match') != -1 or \
                sldata.find('approximate match') != -1 or \
                sldata.find('popular names') != -1:
            self._begin_list = 1


# The used object.
search_person_parser = HTMLSearchPersonParser()


