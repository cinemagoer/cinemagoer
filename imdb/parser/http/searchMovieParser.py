"""
parser.http.searchMovieParser module (imdb package).

This module provides the HTMLSearchMovieParser class (and the
search_movie_parser instance), used to parse the results of a search
for a given title.
E.g., for when searching for the title "the passion", the parsed
page would be:
    http://akas.imdb.com/find?q=the+passion&more=tt

Copyright 2004, 2005 Davide Alberani <da@erlug.linux.it>

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

from imdb.utils import analyze_title
from utils import ParserBase


class BasicMovieParser(ParserBase):
    """Simply get the title of a movie and the imdbID.
    
    It's used by the HTMLSearchMovieParser class to return a result
    for a direct match (when a search on IMDb results in a single
    movie, the web server sends directly the movie page.
    """
    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self.__result = []
        self.__reading_page_title = 0
        self.__page_title = ''

    def get_data(self):
        """Return a list with a single tuple ('movieID', {title_dict})
        where movieID is the imdbID.
        """
        return self.__result

    def start_title(self, attrs):
        self.__reading_page_title = 1

    def end_title(self):
        self.__reading_page_title = 0

    def start_input(self, attrs):
        # XXX: read the movieID from the "send this page to a friend" form.
        t = self.get_attr_value(attrs, 'type')
        if t and t.strip().lower() == 'hidden':
            n = self.get_attr_value(attrs, 'name')
            if n: n = n.strip().lower()
            if n in ('arg', 'auto'):
                val = self.get_attr_value(attrs, 'value') or ''
                # XXX: use re_imdbIDonly because in the input field
                #      the movieID is not preceded by 'tt'.
                if n == 'arg': nr = self.re_imdbIDonly.findall(val)
                else: nr = self.re_imdbID.findall(val)
                if not nr: return
                imdbID = nr[0]
                title = self.__page_title.strip()
                if imdbID and title:
                    res = [(imdbID, analyze_title(title, canonical=1))]
                    self.reset()
                    self.__result = res
            
    def end_input(self): pass

    def _handle_data(self, data):
        if self.__reading_page_title:
            self.__page_title += data


class HTMLSearchMovieParser(ParserBase):
    """Parse the html page that the IMDb web server shows when the
    "new search system" is used.
    """
    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self.__results = []
        self.__begin_list = 0
        self.__is_title = 0
        self.__reading_page_title = 0
        self.__current_imdbID = ''
        self.__current_title = ''
        self.__no_more = 0
        self.__stop = 0
    
    def parse(self, cont, results=None):
        self.maxres = results
        return ParserBase.parse(self, cont)

    def get_data(self):
        """Return a list of ('imdbID', {title_dict}) tuples."""
        return self.__results

    def start_title(self, attrs):
        self.__reading_page_title = 1

    def end_title(self):
        self.__reading_page_title = 0

    def start_ol(self, attrs):
        self.__begin_list = 1

    def end_ol(self):
        self.__begin_list = 0
        self.__is_title = 0
        self.__current_title = ''
        self.__current_imdbID = ''

    def start_a(self, attrs):
        link = self.get_attr_value(attrs, 'href')
        # The next data is a movie title; now store the imdbID.
        if link and link.lower().startswith('/title'):
            nr = self.re_imdbID.findall(link[6:])
            if not nr: return
            self.__current_imdbID = nr[0]
            self.__is_title = 1

    def end_a(self): pass

    def start_small(self, attrs):
        self.__no_more = 1

    def end_small(self): pass

    def start_li(self, attrs): pass

    def end_li(self):
        if self.__begin_list and self.__is_title and self.__current_imdbID:
            # We should have got the title.
            title = self.__current_title.strip()
            tup = (self.__current_imdbID, analyze_title(title, canonical=1))
            self.__results.append(tup)
            if self.maxres is not None and self.maxres <= len(self.__results):
                self.__stop = 1
        self.__current_title = ''
        self.__current_imdbID = ''
        self.__is_title = 0
        self.__no_more = 0

    def _handle_data(self, data):
        if self.__stop:
            res = self.__results
            self.reset()
            self.__results = res
            return
        if self.__begin_list and self.__is_title and not self.__no_more:
            self.__current_title += data
        elif self.__reading_page_title:
            if data.lower().find('imdb title search') == -1:
                # XXX: a direct result!
                #      Interrupt parsing, and retrieve data using a
                #      BasicMovieParser object.
                rawdata = self.rawdata
                # XXX: it' would be much better to move this code to
                #      the end_title() method, but it would raise an
                #       exception...
                self.reset()
                # Get imdbID and title directly from the "main details" page.
                bmp = BasicMovieParser()
                self.__results = bmp.parse(rawdata)['data']
        else:
            # XXX: we have to check the plain text part of the HTML
            #      to know when the list of title begins.
            data = data.strip().lower()
            if data.find('exact match') != -1 or \
                    data.find('partial match') != -1 or \
                    data.find('approx match') != -1 or \
                    data.find('approximate match') != -1 or \
                    data.find('popular titles') != -1:
                self.__begin_list = 1


# The used object.
search_movie_parser = HTMLSearchMovieParser()


