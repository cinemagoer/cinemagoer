"""
parser.http.searchMovieParser module (imdb package).

This module provides the HTMLSearchMovieParser class (and the
search_movie_parser instance), used to parse the results of a search
for a given title.
E.g., for when searching for the title "the passion", the parsed
page would be:
    http://akas.imdb.com/find?q=the+passion&tt=on&mx=20

Copyright 2004-2008 Davide Alberani <da@erlug.linux.it>

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

from imdb.utils import analyze_title, analyze_name, analyze_company_name
from utils import ParserBase
from imdb.Movie import Movie


class BasicMovieParser(ParserBase):
    """Simply get the title of a movie and the imdbID.

    It's used by the HTMLSearchMovieParser class to return a result
    for a direct match (when a search on IMDb results in a single
    movie, the web server sends directly the movie page."""
    def _reset(self):
        """Reset the parser."""
        self._result = {}
        self._movieID = None
        self._reading_page_title = 0
        self._page_title = u''
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
        t = self._page_title.strip()
        if t.find('IMDb Title') != -1 and t.find('Search') != -1: return
        self._result = analyze_title(t, canonical=1)

    def start_input(self, attrs):
        # XXX: read the movieID from the "send this page to a friend" form.
        t = self.get_attr_value(attrs, 'type')
        if t and t.strip().lower() == 'hidden':
            n = self.get_attr_value(attrs, 'name')
            if n: n = n.strip().lower()
            if n in ('arg', 'auto'):
                val = self.get_attr_value(attrs, 'value') or u''
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
                            accessSystem=self._as, modFunct=self._modFunct)
                self._result['kind'] = u'episode'
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
            self._series_info = u''

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


def _dontChange(s, *args, **kwds):
    """Return the name (useful for characters objects)."""
    return {'name': s}

def _analyze_company_name(n, *args, **kwds):
    """analyze_company_name doesn't accept the 'canonical' paramter."""
    return analyze_company_name(n, stripNotes=True)


class HTMLSearchMovieParser(ParserBase):
    """Parse the html page that the IMDb web server shows when the
    "new search system" is used, for both movies and persons."""
    # Customizations for movie, person and character parsers.
    _k = {
        'movie':
            {'analyze_f': analyze_title,
            'link': '/title',
            'in title': 'imdb title'},

        'person':
            {'analyze_f': analyze_name,
            'link': '/name',
            'in title': 'imdb name'},

        'character':
            {'analyze_f': _dontChange,
            'link': '/character',
            'in title': 'imdb search'},

        'company':
            {'analyze_f': _analyze_company_name,
            'link': '/company',
            'in title': 'imdb company search'}
    }

    def _init(self):
        """Initialize the parser."""
        self.kind = 'movie'
        self._basic_parser = BasicMovieParser

    def _reset(self):
        """Reset the parser."""
        self._results = []
        self._is_title = False
        self._reading_page_title = False
        self._current_imdbID = u''
        self._current_ton = u''
        self._no_more = False
        self._stop = False
        self._in_table = False
        self._col_nr = 0

    def parse(self, cont, results=None, **kwds):
        self.maxres = results
        return ParserBase.parse(self, cont)

    def get_data(self):
        """Return a list of ('imdbID', {title_dict/name_dict}) tuples."""
        return self._results

    def start_title(self, attrs):
        self._reading_page_title = True

    def end_title(self):
        self._reading_page_title = False

    def start_table(self, attrs):
        self._in_table = True

    def end_table(self):
        self._in_table = False

    def start_tr(self, attrs):
        if not self._in_table: return
        self._col_nr = 0
        self._no_more = False

    def end_tr(self): pass

    def start_td(self, attrs):
        if not self._in_table: return
        self._col_nr += 1
        self._is_title = False
        self._current_imdbID = None

    def do_img(self, attrs):
        # Skips mini-posters in the results (they are there, if
        # we don't use the IMDbPYweb's account, performing the search).
        if not self._in_table: return
        #if self.kind == 'character': return
        #src = self.get_attr_value(attrs, 'src')
        #if src and not src.lower().endswith('/b.gif'):
        #    if self._col_nr == 1:
        #        self._col_nr = 0

    def end_td(self):
        if self._in_table and self._is_title and self._current_imdbID and \
                self._col_nr == 3:
            # We should have got the title/name.
            title = self._current_ton.strip()
            if not title:
                self._current_ton = u''
                self._current_imdbID = u''
                self._is_title = False
                self._no_more = 0
                return
            tup = (self._current_imdbID,
                    self._k[self.kind]['analyze_f'](title, canonical=1))
            self._results.append(tup)
            if self.maxres is not None and self.maxres <= len(self._results):
                self._stop = True
        self._current_ton = u''
        self._current_imdbID = u''
        self._is_title = False
        self._no_more = 0

    def start_a(self, attrs):
        # Prevent tv series to get the (wrong) movieID from the
        # last episode, sometimes listed in the <td>...</td> tag
        # along with the series' title.
        if self._current_imdbID: return
        if not self._in_table and self._col_nr == 3: return
        link = self.get_attr_value(attrs, 'href')
        # The next data is a movie title/person name; now store the imdbID.
        if link and link.lower().startswith(self._k[self.kind]['link']):
            nr = self.re_imdbID.findall(link[6:])
            if not nr: return
            self._current_imdbID = str(nr[0])
            self._is_title = True

    def end_a(self): pass

    def start_small(self, attrs):
        self._no_more = True

    def end_small(self): pass

    def do_br(self, attrs):
        if not self.kind == 'character':
            if self._col_nr > 3:
                self._no_more = True

    def _handle_data(self, data):
        if self._stop:
            res = self._results
            self.reset()
            self._results = res
            return
        if self._in_table and self._col_nr == 3 and not self._no_more:
            self._current_ton += data
        elif self._reading_page_title:
            dls = data.strip().lower().replace('  ', ' ')
            if not dls.startswith(self._k[self.kind]['in title']):
                # XXX: a direct result!
                #      Interrupt parsing, and retrieve data using a
                #      BasicMovieParser/BasicPersonParser object.
                rawdata = self.rawdata
                # XXX: it' would be much better to move this code to
                #      the end_title() method, but it would raise an
                #       exception...
                self.reset()
                # Get imdbID and title directly from the "main details" page.
                bmp = self._basic_parser()
                self._results = bmp.parse(rawdata)['data']


_OBJECTS = {
        'search_movie_parser': (HTMLSearchMovieParser, None)
}

