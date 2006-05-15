"""
parser.http.searchMovieParser module (imdb package).

This module provides the HTMLSearchMovieParser class (and the
search_movie_parser instance), used to parse the results of a search
for a given title.
E.g., for when searching for the title "the passion", the parsed
page would be:
    http://akas.imdb.com/find?q=the+passion&tt=on&mx=20

Copyright 2004-2006 Davide Alberani <da@erlug.linux.it>

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
from imdb.Movie import Movie


class BasicMovieParser(ParserBase):
    """Simply get the title of a movie and the imdbID.

    It's used by the HTMLSearchMovieParser class to return a result
    for a direct match (when a search on IMDb results in a single
    movie, the web server sends directly the movie page."""
    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._result = {}
        self._movieID = None
        self._reading_page_title = 0
        self._page_title = ''
        self._inbch = 0
        self._in_series_title = 0
        self._in_series_info = 0
        self.__seriesID = None
        self._series_title = u''
        self._series_info = u''

    def get_data(self):
        """Return a list with a single tuple ('movieID', {title_dict})
        where movieID is the imdbID.
        """
        if self._result and self._movieID:
            return [(self._movieID, self._result)]
        return self._result

    def start_title(self, attrs):
        self._reading_page_title = 1

    def end_title(self):
        self._reading_page_title = 0
        self._result = analyze_title(self._page_title, canonical=1)

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
                imdbID = str(nr[0])
                self._movieID = imdbID

    def end_input(self): pass

    def start_b(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.lower() == 'ch':
            self._inbch = 1

    def end_b(self):
        if self._inbch: self._inbch = 0

    def start_a(self, attrs):
        if self._in_series_title:
            href = self.get_attr_value(attrs, 'href')
            if not href: return
            ids = self.re_imdbID.findall(href)
            if ids:
                self.__seriesID = ids[-1]

    def end_a(self): pass

    def do_br(self, attrs):
        if self._in_series_title:
            self._in_series_title = 0
            st = self._series_title.strip()
            if st and self.__seriesID:
                d_title = analyze_title(st, canonical=1)
                m = Movie(movieID=str(self.__seriesID), data=d_title,
                            accessSystem='http')
                self._result['kind'] = 'episode'
                self._result['episode of'] = m
            self._series_title = u''
        elif self._in_series_info:
            self._in_series_info = 0
            si = ' '.join([x for x in self._series_info.split() if x])
            if si:
                aid = self.re_airdate.findall(si)
                if aid and len(aid[0]) == 3:
                    date, season, episode = aid[0]
                    date = date.strip()
                    try: season = int(season)
                    except: pass
                    try: episode = int(episode)
                    except: pass
                    if date and date != '????':
                        self._result['original air date'] = date
                    # Handle also "episode 0".
                    if season or type(season) is type(0):
                        self._result['season'] = season
                    if episode or type(season) is type(0):
                        self._result['episode'] = episode
            self._series_info = ''

    def _handle_data(self, data):
        if self._reading_page_title:
            self._page_title += data
        elif self._in_series_title:
            self._series_title += data
        elif self._in_series_info:
            self._series_info += data
        elif self._inbch:
            sldata = data.strip().lower()
            if sldata.startswith('tv series:'):
                self._in_series_title = 1
            elif sldata.startswith('original air date'):
                self._in_series_info = 1


class HTMLSearchMovieParser(ParserBase):
    """Parse the html page that the IMDb web server shows when the
    "new search system" is used."""
    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._results = []
        self._begin_list = 0
        self._is_title = 0
        self._reading_page_title = 0
        self._current_imdbID = ''
        self._current_title = ''
        self._no_more = 0
        self._stop = 0

    def parse(self, cont, results=None):
        self.maxres = results
        return ParserBase.parse(self, cont)

    def get_data(self):
        """Return a list of ('imdbID', {title_dict}) tuples."""
        return self._results

    def start_title(self, attrs):
        self._reading_page_title = 1

    def end_title(self):
        self._reading_page_title = 0

    def start_ol(self, attrs):
        self._begin_list = 1

    def end_ol(self):
        self._begin_list = 0
        self._is_title = 0
        self._current_title = ''
        self._current_imdbID = ''

    def start_a(self, attrs):
        link = self.get_attr_value(attrs, 'href')
        # The next data is a movie title; now store the imdbID.
        if link and link.lower().startswith('/title'):
            nr = self.re_imdbID.findall(link[6:])
            if not nr: return
            self._current_imdbID = str(nr[0])
            self._is_title = 1

    def end_a(self): pass

    def start_small(self, attrs):
        self._no_more = 1

    def end_small(self): pass

    def start_li(self, attrs): pass

    def end_li(self):
        if self._begin_list and self._is_title and self._current_imdbID:
            # We should have got the title.
            title = self._current_title.strip()
            tup = (self._current_imdbID, analyze_title(title, canonical=1))
            self._results.append(tup)
            if self.maxres is not None and self.maxres <= len(self._results):
                self._stop = 1
        self._current_title = ''
        self._current_imdbID = ''
        self._is_title = 0
        self._no_more = 0

    def _handle_data(self, data):
        if self._stop:
            res = self._results
            self.reset()
            self._results = res
            return
        if self._begin_list and self._is_title and not self._no_more:
            self._current_title += data
        elif self._reading_page_title:
            dls = data.strip().lower()
            if not dls.startswith('imdb title'):
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
                self._results = bmp.parse(rawdata)['data']
        else:
            # XXX: we have to check the plain text part of the HTML
            #      to know when the list of title begins.
            data = data.strip().lower()
            if data.find('exact match') != -1 or \
                    data.find('partial match') != -1 or \
                    data.find('approx match') != -1 or \
                    data.find('approximate match') != -1 or \
                    data.find('popular titles') != -1:
                self._begin_list = 1


# The used object.
search_movie_parser = HTMLSearchMovieParser()


