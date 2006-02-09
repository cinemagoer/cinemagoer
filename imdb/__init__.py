"""
imdb package.

This package can be used to retrieve information about a movie or
a person from the IMDb database.
It can fetch data through different media (e.g.: the IMDb web pages,
a local installation, a SQL database, etc.)

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

__all__ = ['IMDb', 'IMDbError', 'Movie', 'Person']

import types, sys

from imdb import Movie, Person
from imdb._exceptions import IMDbError, IMDbDataAccessError
_utype = type(u'') # XXX: I know this is a bad habit...


# URLs of the main pages for movies and persons.
imdbURL_movie_main = 'http://akas.imdb.com/title/tt%s/'
imdbURL_person_main = 'http://akas.imdb.com/name/nm%s/'


def IMDb(accessSystem='http', *arguments, **keywords):
    """Return an instance of the appropriate class.
    The accessSystem parameter is used to specify the kind of
    the preferred access system.
    """
    if accessSystem in ('http', 'web', 'html'):
        from parser.http import IMDbHTTPAccessSystem
        return IMDbHTTPAccessSystem(*arguments, **keywords)
    elif accessSystem in ('httpThin', 'webThin', 'htmlThin'):
        from parser.http import IMDbHTTPAccessSystem
        return IMDbHTTPAccessSystem(isThin=1, *arguments, **keywords)
    elif accessSystem in ('mobile',):
        from parser.mobile import IMDbMobileAccessSystem
        return IMDbMobileAccessSystem(*arguments, **keywords)
    elif accessSystem in ('local', 'files'):
        try:
            from parser.local import IMDbLocalAccessSystem
        except ImportError:
            raise IMDbError, 'the local access system is not installed'
        return IMDbLocalAccessSystem(*arguments, **keywords)
    elif accessSystem in ('sql', 'db', 'database'):
        try:
            from parser.sql import IMDbSqlAccessSystem
        except ImportError:
            raise IMDbError, 'the sql access system is not installed'
        return IMDbSqlAccessSystem(*arguments, **keywords)
    else:
        raise IMDbError, 'unknown kind of data access system: "%s"' \
                            % accessSystem


# XXX: I'm not sure this is a good guess.
#      I suppose that an argument of the IMDb function can be used to
#      set a default encoding for the output, and then Movie and Person
#      objects can use this default encoding, returning strings.
#      Anyway, passing unicode strings to search_movie() and search_person()
#      methods is always safer.
encoding = sys.stdin.encoding or sys.getdefaultencoding()

class IMDbBase:
    """The base class used to search for a movie/person and to get a
    Movie/Person object.
    
    This class cannot directly fetch data of any kind and so you
    have to search the "real" code into a subclass.
    """

    # The name of the preferred access system (MUST be overridden
    # in the subclasses).
    accessSystem = 'UNKNOWN'

    def __init__(self, defaultModFunct=None, *arguments, **keywords):
        """Initialize the access system.
        If specified, defaultModFunct is the function used by
        default by the Person and Movie objects, when accessing
        their text fields.
        """
        # The function used to output the strings that need modification (the
        # ones containing references to movie titles and person names).
        self._defModFunct = defaultModFunct
        
    def _normalize_movieID(self, movieID):
        """Normalize the given movieID."""
        # By default, do nothing.
        return movieID
    
    def _normalize_personID(self, personID):
        """Normalize the given personID."""
        # By default, do nothing.
        return personID

    def _get_real_movieID(self, movieID):
        """Handle title aliases."""
        # By default, do nothing.
        return movieID

    def _get_real_personID(self, personID):
        """Handle name aliases."""
        # By default, do nothing.
        return personID

    def _get_infoset(self, prefname):
        """Return methods with the name starting with prefname."""
        infoset = []
        excludes = ('%sinfoset' % prefname,)
        preflen = len(prefname)
        for name in dir(self.__class__):
            if name.startswith(prefname) and name not in excludes:
                member = getattr(self.__class__, name)
                if type(member) is types.MethodType:
                    infoset.append(name[preflen:].replace('_', ' '))
        return infoset

    def get_movie_infoset(self):
        """Return the list of info set available for movies."""
        return self._get_infoset('get_movie_')

    def get_person_infoset(self):
        """Return the list of info set available for persons."""
        return self._get_infoset('get_person_')

    def get_movie(self, movieID, info=Movie.Movie.default_info, modFunct=None):
        """Return a Movie object for the given movieID.

        The movieID is something used to univocally identify a movie;
        it can be the imdbID used by the IMDb web server, a file
        pointer, a line number in a file, an ID in a database, etc.

        info is the list of sets of information to retrieve.

        If specified, modFunct will be the function used by the Movie
        object when accessing its text fields (like 'plot').
        """
        movieID = self._normalize_movieID(movieID)
        movieID = self._get_real_movieID(movieID)
        movie = Movie.Movie(movieID=movieID, accessSystem=self.accessSystem)
        modFunct = modFunct or self._defModFunct
        if modFunct is not None:
            movie.set_mod_funct(modFunct)
        self.update(movie, info)
        return movie

    def _search_movie(self, title, results):
        """Return a list of tuples (movieID, {movieData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError, 'override this method'

    def search_movie(self, title, results=20):
        """Return a list of Movie objects for a query for the given title.
        The results argument is the maximum number of results to return.
        """
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 20
        # XXX: I suppose it will be much safer if the user provides
        #      an unicode string... this is just a guess.
        if type(title) is not _utype:
            title = unicode(title, encoding, 'replace')
        res = self._search_movie(title, results)
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res][:results]

    def get_person(self, personID, info=Person.Person.default_info,
                    modFunct=None):
        """Return a Person object for the given personID.
        
        The personID is something used to univocally identify a person;
        it can be the imdbID used by the IMDb web server, a file
        pointer, a line number in a file, an ID in a database, etc.

        info is the list of sets of information to retrieve.
        
        If specified, modFunct will be the function used by the Person
        object when accessing its text fields (like 'plot').
        """
        personID = self._normalize_personID(personID)
        personID = self._get_real_personID(personID)
        person = Person.Person(personID=personID,
                                accessSystem=self.accessSystem)
        modFunct = modFunct or self._defModFunct
        if modFunct is not None:
            person.set_mod_funct(modFunct)
        self.update(person, info)
        return person

    def _search_person(self, name, results):
        """Return a list of tuples (personID, {personData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError, 'override this method'

    def search_person(self, name, results=20):
        """Return a list of Person objects for a query for the given name.

        The results argument is the maximum number of results to return.
        """
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 20
        if type(name) is not _utype:
            name = unicode(name, encoding, 'replace')
        res = self._search_person(name, results)
        return [Person.Person(personID=self._get_real_personID(pi),
                data=pd, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for pi, pd in res][:results]

    def new_movie(self, *arguments, **keywords):
        """Return a Movie object."""
        # XXX: not really useful...
        if keywords.has_key('title'):
            if type(keywords['title']) is not _utype:
                keywords['title'] = unicode(keywords['title'],
                                            encoding, 'replace')
        elif len(arguments) > 1:
            if type(arguments[1]) is not _utype:
                arguments[1] = unicode(arguments[1], encoding, 'replace')
        return Movie.Movie(accessSystem=self.accessSystem,
                            *arguments, **keywords)

    def new_person(self, *arguments, **keywords):
        """Return a Person object."""
        # XXX: not really useful...
        if keywords.has_key('name'):
            if type(keywords['name']) is not _utype:
                keywords['name'] = unicode(keywords['name'],
                                            encoding, 'replace')
        elif len(arguments) > 1:
            if type(arguments[1]) is not _utype:
                arguments[1] = unicode(arguments[1], encoding, 'replace')
        return Person.Person(accessSystem=self.accessSystem,
                                *arguments, **keywords)

    def update(self, mop, info=None, override=0):
        """Given a Movie or Person object with only partial information,
        retrieve the required set of information.

        info is the list of sets of information to retrieve.

        If override is set, the information are retrieved and updated
        even if they're already in the object.
        """
        # XXX: should this be a method of the Movie and Person classes?
        #      NO!  What for Movie and Person instances created by
        #      external functions?
        mopID = None
        prefix = ''
        if isinstance(mop, Movie.Movie):
            mopID = mop.movieID
            prefix = 'movie'
        elif isinstance(mop, Person.Person):
            mopID = mop.personID
            prefix = 'person'
        else:
            raise IMDbError, 'object ' + repr(mop) + \
                        ' is not a Movie or Person instance'
        if mopID is None:
            raise IMDbDataAccessError, \
                    'the supplied object has null movieID or personID'
        if mop.accessSystem == self.accessSystem:
            as = self
        else:
            as = IMDb(mop.accessSystem)
        if info is None:
            info = mop.default_info
        elif info == 'all':
            if isinstance(mop, Movie.Movie):
                info = self.get_movie_infoset()
            else:
                info = self.get_person_infoset()
        if type(info) not in (types.TupleType, types.ListType):
            info = (info,)
        res = {}
        for i in info:
            if i in mop.current_info and not override: continue
            try:
                method = getattr(as, 'get_%s_%s' %
                                    (prefix, i.replace(' ', '_')))
            except AttributeError:
                raise IMDbDataAccessError, 'unknown information set "%s"' % i
            ret = method(mopID)
            if ret.has_key('info sets'):
                for ri in ret['info sets']:
                    mop.add_to_current_info(ri)
            else:
                mop.add_to_current_info(i)
            if ret.has_key('data'):
                res.update(ret['data'])
            if ret.has_key('titlesRefs'):
                mop.update_titlesRefs(ret['titlesRefs'])
            if ret.has_key('namesRefs'):
                mop.update_namesRefs(ret['namesRefs'])
        mop.set_data(res, override=0)

    def get_imdbMovieID(self, movieID):
        """Translate a movieID in an imdbID (the ID used by the IMDb
        web server; must be overridden by the subclass.
        """
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError, 'override this method'

    def get_imdbPersonID(self, personID):
        """Translate a personID in a imdbID (the ID used by the IMDb
        web server; must be overridden by the subclass.
        """
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError, 'override this method'

    def get_imdbID(self, mop):
        """Return the imdbID for the given Movie or Person object."""
        imdbID = None
        if mop.accessSystem == self.accessSystem:
            as = self
        else:
            as = IMDb(mop.accessSystem)
        if isinstance(mop, Movie.Movie):
            imdbID = as.get_imdbMovieID(mop.movieID)
        elif isinstance(mop, Person.Person):
            imdbID = as.get_imdbPersonID(mop.personID)
        else:
            raise IMDbError, 'object ' + repr(mop) + \
                        ' is not a Movie or Person instance'
        return imdbID

    def get_imdbURL(self, mop):
        """Return the main IMDb URL for the given Movie or Person object."""
        url = ''
        if mop.accessSystem == self.accessSystem:
            as = self
        else:
            as = IMDb(mop.accessSystem)
        if isinstance(mop, Movie.Movie):
            if mop.movieID is None: return None
            imdbID = as.get_imdbMovieID(mop.movieID)
            if imdbID is None: return ''
            url = imdbURL_movie_main % imdbID
        elif isinstance(mop, Person.Person):
            if mop.personID is None: return None
            imdbID = as.get_imdbPersonID(mop.personID)
            if imdbID is None: return ''
            url = imdbURL_person_main % imdbID
        else:
            raise IMDbError, 'object ' + repr(mop) + \
                        ' is not a Movie or Person instance'
        return url

    def get_special_methods(self):
        """Return the special methods defined by the subclass."""
        sm_dict = {}
        base_methods = []
        for name in dir(IMDbBase):
            member = getattr(IMDbBase, name)
            if type(member) is types.MethodType:
                base_methods.append(name)
        for name in dir(self.__class__):
            if name.startswith('_') or name in base_methods or \
                    name.startswith('get_movie_') or \
                    name.startswith('get_person_'):
                continue
            member = getattr(self.__class__, name)
            if type(member) is types.MethodType:
                sm_dict.update({name: member.__doc__})
        return sm_dict


