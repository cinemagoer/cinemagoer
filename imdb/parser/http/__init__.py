"""
parser.http package (imdb package).

This package provides the IMDbHTTPAccessSystem class used to access
IMDb's data through the web interface.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "http" or "web"
or "html" (this is the default).

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

import urllib

from imdb import IMDbBase
from imdb._exceptions import IMDbDataAccessError
from movieParser import movie_parser, plot_parser, movie_awards_parser, \
                        taglines_parser, keywords_parser, \
                        alternateversions_parser, crazycredits_parser, \
                        goofs_parser, trivia_parser, quotes_parser, \
                        releasedates_parser, ratings_parser, \
                        officialsites_parser, connections_parser, \
                        tech_parser, locations_parser, soundtrack_parser, \
                        dvd_parser
from searchMovieParser import search_movie_parser
from personParser import maindetails_parser, bio_parser, \
                        otherworks_parser, person_awards_parser, \
                        person_officialsites_parser
from searchPersonParser import search_person_parser


# Misc URLs
imdbURL_movie = 'http://akas.imdb.com/title/tt%s/'
imdbURL_person = 'http://akas.imdb.com/name/nm%s/'
imdbURL_search = 'http://akas.imdb.com/find?%s'


class IMDbURLopener(urllib.FancyURLopener):
    """Fetch web pages and handle errors."""
    def __init__(self, *args, **kwargs):
        urllib.FancyURLopener.__init__(self, *args, **kwargs)
        # XXX: IMDb's web server doesn't like urllib-based programs,
        #      so lets fake to be Mozilla.
        #      Wow!  I'm shocked by my total lack of ethic! <g>
        self.addheaders = [('User-agent', 'Mozilla/5.0')]

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        raise IMDbDataAccessError, {'url': 'http:%s' % url,
                                    'errcode': errcode,
                                    'errmsg': errmsg,
                                    'headers': headers,
                                    'proxy': self.proxies.get('http', '')}
    def open_unknown(self, fullurl, data=None):
        raise IMDbDataAccessError, {'fullurl': fullurl,
                                    'data': str(data),
                                    'proxy': self.proxies.get('http', '')}
    def open_unknown_proxy(self, proxy, fullurl, data=None):
        raise IMDbDataAccessError, {'proxy': str(proxy),
                                    'fullurl': fullurl,
                                    'data': str(data)}


class IMDbHTTPAccessSystem(IMDbBase):
    """The class used to access IMDb's data through the web."""

    accessSystem = 'http'

    urlOpener = IMDbURLopener()

    def _normalize_movieID(self, movieID):
        """Normalize the given movieID."""
        return str(movieID).zfill(7)

    def _normalize_personID(self, personID):
        """Normalize the given personID."""
        return str(personID).zfill(7)

    def get_imdbMovieID(self, movieID):
        """Translate a movieID in an imdbID; in this implementation
        the movieID _is_ the imdbID.
        """
        return movieID

    def get_imdbPersonID(self, personID):
        """Translate a personID in an imdbID; in this implementation
        the personID _is_ the imdbID.
        """
        return personID

    def set_proxy(self, proxy):
        """Set the web proxy to use.
        
        It should be a string like 'http://localhost:8080/'; if the
        string is empty, no proxy will be used.
        If set, the value of the environment variable HTTP_PROXY is
        automatically used.
        """
        if not proxy:
            if self.urlOpener.proxies.has_key('http'):
                del self.urlOpener.proxies['http']
        else:
            if not proxy.lower().startswith('http://'):
                proxy = 'http://%s' % proxy
            self.urlOpener.proxies['http'] = proxy

    def get_proxy(self):
        """Return the used proxy or an empty string."""
        return self.urlOpener.proxies.get('http', '')

    def _retrieve(self, url):
        """Retrieve the given URL."""
        try:
            uopener = self.urlOpener.open(url)
            content = uopener.read()
            uopener.close()
            self.urlOpener.close()
        except IOError, e:
            raise IMDbDataAccessError, {'errcode': e.errno,
                                        'errmsg': str(e.strerror),
                                        'url': url,
                                        'proxy': self.get_proxy()}
        return content

    def _search_movie(self, title, results):
        # The URL of the query.
        params = urllib.urlencode({'more': 'tt', 'q': title})
        cont = self._retrieve(imdbURL_search % params)
        return search_movie_parser.parse(cont)['data']

    def get_movie_main(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'combined')
        return movie_parser.parse(cont)

    def get_movie_plot(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'plotsummary')
        return plot_parser.parse(cont)

    def get_movie_awards(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'awards')
        return movie_awards_parser.parse(cont)

    def get_movie_taglines(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'taglines')
        return taglines_parser.parse(cont)

    def get_movie_keywords(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'keywords')
        return taglines_parser.parse(cont)

    def get_movie_alternate_versions(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'alternateversions')
        return alternateversions_parser.parse(cont)

    def get_movie_crazy_credits(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'crazycredits')
        return crazycredits_parser.parse(cont)

    def get_movie_goofs(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'goofs')
        return goofs_parser.parse(cont)

    def get_movie_quotes(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'quotes')
        return quotes_parser.parse(cont)

    def get_movie_release_dates(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'releaseinfo')
        return releasedates_parser.parse(cont)

    def get_movie_vote_details(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'ratings')
        return ratings_parser.parse(cont)

    def get_movie_official_sites(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'officialsites')
        return officialsites_parser.parse(cont)

    def get_movie_trivia(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'trivia')
        return trivia_parser.parse(cont)

    def get_movie_connections(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'movieconnections')
        return connections_parser.parse(cont)

    def get_movie_technical(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'technical')
        return tech_parser.parse(cont)

    def get_movie_business(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'business')
        return tech_parser.parse(cont)

    def get_movie_literature(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'literature')
        return tech_parser.parse(cont)

    def get_movie_locations(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'locations')
        return locations_parser.parse(cont)
    
    def get_movie_soundtrack(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'soundtrack')
        return soundtrack_parser.parse(cont)

    def get_movie_dvd(self, movieID):
        cont = self._retrieve(imdbURL_movie % movieID + 'dvd')
        return dvd_parser.parse(cont)
    
    def _search_person(self, name, results):
        # The URL of the query.
        params = urllib.urlencode({'more': 'nm', 'q': name})
        cont = self._retrieve(imdbURL_search % params)
        return search_person_parser.parse(cont)['data']

    def get_person_main(self, personID):
        cont = self._retrieve(imdbURL_person % personID + 'maindetails')
        ret = maindetails_parser.parse(cont)
        ret['info sets'] = ('main', 'filmography')
        return ret

    def get_person_filmography(self, personID):
        return self.get_person_main(personID)

    def get_person_biography(self, personID):
        cont = self._retrieve(imdbURL_person % personID + 'bio')
        return bio_parser.parse(cont)

    def get_person_awards(self, personID):
        cont = self._retrieve(imdbURL_person % personID + 'awards')
        return person_awards_parser.parse(cont)

    def get_person_other_works(self, personID):
        cont = self._retrieve(imdbURL_person % personID + 'otherworks')
        return otherworks_parser.parse(cont)

    def get_person_official_sites(self, personID):
        cont = self._retrieve(imdbURL_person % personID + 'officialsites')
        return person_officialsites_parser.parse(cont)


