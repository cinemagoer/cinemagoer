"""
Movie module (imdb package).

This module provides the Movie class, used to store information about
a given movie.

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

import types
from copy import deepcopy
from utils import analyze_title, build_title, modifyStrings, modClearRefs, \
                    modNull, normalizeTitle


class Movie:
    """A Movie.
    
    A Movie object emulates (most of) the dictionary interface.

    Every information about a movie can be accessed as:
        movieObject['information']
    to get a list of the kind of information stored in a
    Movie object, use the keys() method; some useful aliases
    are defined (as "plot summary" for the "plot" key); see the
    keys_alias dictionary.
    """
    # The default sets of information retrieved.
    default_info = ('main', 'plot')

    # Aliases for some not-so-intuitive keys.
    keys_alias = {
                'user rating':  'rating',
                'plot summary': 'plot',
                'plot summaries': 'plot',
                'directed by':  'director',
                'writing credits': 'writer',
                'produced by':  'producer',
                'original music by':    'composer',
                'original music':    'composer',
                'non-original music by':    'composer',
                'non-original music':    'composer',
                'music':    'composer',
                'cinematography by':    'cinematographer',
                'cinematography':   'cinematographer',
                'film editing by':  'editor',
                'film editing': 'editor',
                'editing':  'editor',
                'actors':   'cast',
                'actresses':    'cast',
                'casting by':   'casting director',
                'casting':  'casting director',
                'art direction by': 'art director',
                'art direction': 'art director',
                'set decoration by':    'set decorator',
                'set decoration':   'set decorator',
                'costume design by':    'costume designer',
                'costume design':    'costume designer',
                'makeup department':    'make up',
                'makeup':    'make up',
                'make-up':    'make up',
                'production management':    'production manager',
                'second unit director or assistant director':
                                                'assistant director',
                'second unit director':   'assistant director',
                'sound department': 'sound crew',
                'special effects by':   'special effects',
                'visual effects by':    'visual effects',
                'stunts':   'stunt performer',
                'other crew':   'crewmembers',
                'misc crew':   'crewmembers',
                'miscellaneous crew':   'crewmembers',
                'other companies':  'miscellaneous companies',
                'misc companies': 'miscellaneous companies',
                'aka':  'akas',
                'also known as':    'akas',
                'country':  'countries',
                'runtime':  'runtimes',
                'lang': 'languages',
                'language': 'languages',
                'certificate':  'certificates',
                'certifications':   'certificates',
                'certification':    'certificates',
                'miscellaneous links':  'misc links',
                'miscellaneous':    'misc links',
                'soundclips':   'sound clips',
                'videoclips':   'video clips',
                'photographs':  'photo sites',
                'amazon review': 'amazon reviews'}

    def __init__(self, movieID=None, title='', myTitle='',
                    myID=None, movieData={}, currentRole='', notes='',
                    accessSystem=None, titlesRefs={}, namesRefs={},
                    modFunct=modClearRefs):
        """Initialize a Movie object.
        
        *movieID* -- the unique identifier for the movie.
        *title* -- the title of the Movie, if not in the movieData dictionary.
        *myTitle* -- your personal title for the movie.
        *myID* -- your personal identifier for the movie.
        *movieData* -- a dictionary used to initialize the object.
        *currentRole* -- a string representing the current role or duty
                        of a person in this movie.
        *notes* -- notes for the person referred in the currentRole
                    attribute; e.g.: '(voice)'.
        *accessSystem* -- a string representing the data access system used.
        *titlesRefs* -- a dictionary with references to movies.
        *namesRefs* -- a dictionary with references to persons.
        *modFunct* -- function called returning text fields.
        """
        self.reset()
        self.accessSystem = accessSystem
        self.set_data(movieData, override=1)
        self.update_titlesRefs(titlesRefs)
        self.update_namesRefs(namesRefs)
        if title and not movieData.has_key('title'):
            self.set_title(title)
        self.movieID = movieID
        self.myTitle = myTitle
        self.myID = myID
        self.currentRole = currentRole
        self.notes = notes
        self.set_mod_funct(modFunct)

    def get_current_info(self):
        """Return the current set of information retrieved."""
        return self.current_info

    def set_current_info(self, ci):
        """Set the current set of information retrieved."""
        self.current_info = ci

    def add_to_current_info(self, val):
        """Add a set of information to the current list."""
        if val not in self.current_info:
            self.current_info.append(val)

    def has_current_info(self, val):
        """Return true if the given set of information is in the list."""
        return val in self.current_info
    
    def set_mod_funct(self, modFunct):
        """Set the fuction used to modify the strings."""
        if modFunct is None: modFunct = modClearRefs
        self.__modFunct = modFunct

    def update_titlesRefs(self, titlesRefs):
        """Update the dictionary with the references to movies."""
        self.__titlesRefs.update(titlesRefs)
    
    def get_titlesRefs(self):
        """Return the dictionary with the references to movies."""
        return self.__titlesRefs

    def update_namesRefs(self, namesRefs):
        """Update the dictionary with the references to names."""
        self.__namesRefs.update(namesRefs)

    def get_namesRefs(self):
        """Return the dictionary with the references to names."""
        return self.__namesRefs

    def reset(self):
        """Reset the Movie object."""
        self.__movie_data = {}
        self.current_info = []
        self.movieID = None
        self.myTitle = ''
        self.myID = None
        self.currentRole = ''
        self.notes = ''
        self.__titlesRefs = {}
        self.__namesRefs = {}
        self.__modFunct = modClearRefs

    def set_title(self, title):
        """Set the title of the movie."""
        d_title = analyze_title(title)
        self.__movie_data.update(d_title)

    def set_data(self, md, override=0):
        """Set the movie data to the given dictionary; if 'override' is
        set, the previous data is removed, otherwise the two dictionary
        are merged.
        """
        # XXX: uh.  Not sure this the best place/way to do it.
        md = deepcopy(md)
        if not override:
            self.__movie_data.update(md)
        else:
            self.__movie_data = md
    
    def clear(self):
        """Reset the dictionary."""
        self.__movie_data.clear()
        self.currentRole = ''
        self.notes = ''
        self.__titlesRefs = {}
        self.__namesRefs = {}
        self.current_info = []

    def has_key(self, key):
        """Return true if a given section is defined."""
        try:
            self.__getitem__(key)
        except KeyError:
            return 0
        return 1

    def keys(self):
        """Return a list of valid keys."""
        l = self.__movie_data.keys()
        if 'title' in l:
            l += ['canonical title', 'long imdb title',
                    'long imdb canonical title']
        return l

    def items(self):
        """Return the items in the dictionary."""
        return [(k, self.get(k)) for k in self.keys()]

    def values(self):
        """Return the values in the dictionary."""
        return [self.get(k) for k in self.keys()]

    def append_item(self, key, item):
        """The item is appended to the list identified by
        the given key.
        """
        # TODO: this and the two other methods below are here only
        #       for _future_ usage, when it will make sense to modify
        #       a Movie object; right now they're incomplete and should
        #       not be used.
        if not self.__movie_data.has_key(key):
            self.__movie_data[key] = []
        self.__movie_data[key].append(item)

    def set_item(self, key, item):
        """Directly store the item with the given key."""
        self.__movie_data[key] = item

    def __setitem__(self, key, item):
        """Directly store the item with the given key."""
        self.__movie_data[key] = item
    
    def __delitem__(self, key):
        """Remove the given section or key."""
        # XXX: how to remove an item of a section?
        del self.__movie_data[key]

    def get(self, key, default=None):
        """Return the given section, or default if it's not found."""
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        """Return the value for a given key, checking key aliases;
        a KeyError exception is raised if the key is not found.
        """
        if self.__movie_data.has_key('title'):
            if key == 'title':
                return normalizeTitle(self.__movie_data['title'])
            elif key == 'long imdb title':
                return build_title(self.__movie_data, canonical=0)
            elif key == 'canonical title':
                return self.__movie_data['title']
            elif key == 'long imdb canonical title':
                return build_title(self.__movie_data, canonical=1)
        if key in self.keys_alias.keys():
            key = self.keys_alias[key]
        if self.__modFunct is modNull:
            return self.__movie_data[key]
        else:
            return modifyStrings(self.__movie_data[key], self.__modFunct,
                                    self.__titlesRefs, self.__namesRefs)

    def __nonzero__(self):
        """The Movie is "false" if the self.__movie_data does not contains
        a title."""
        # XXX: check the title and the movieID?
        if self.__movie_data and self.__movie_data.has_key('title'):
            return 1
        return 0

    def __cmp__(self, other):
        """Compare two Movie objects."""
        # XXX: only check the title and the movieID?
        # XXX: comparison should be used to sort movies by year?
        if not isinstance(other, self.__class__):
            return -1
        if self.__movie_data == other.__movie_data:
            return 0
        return 1

    def isSameTitle(self, other):
        """Return true if this and the compared object have the same
        long imdb title and/or movieID.
        """
        if not isinstance(other, self.__class__):
            return 0
        if self.__movie_data.has_key('title') and \
                other.__movie_data.has_key('title') and \
                build_title(self.__movie_data, canonical=1) == \
                build_title(other.__movie_data, canonical=1):
            return 1
        if self.accessSystem == other.accessSystem and \
                self.movieID is not None and self.movieID == other.movieID:
            return 1
        return 0

    def __contains__(self, item):
        """Return true if the given Person object is listed in this Movie."""
        from Person import Person
        if not isinstance(item, Person):
            return 0
        for i in self.__movie_data.values():
            if type(i) in (types.ListType, types.TupleType):
                for j in i:
                    if isinstance(j, Person) and item.isSamePerson(j):
                        return 1
        return 0

    def __deepcopy__(self, memo):
        """Return a deep copy of a Movie instance."""
        m = Movie(self.movieID, '', self.myTitle, self.myID,
                    deepcopy(self.__movie_data, memo), self.currentRole,
                    self.notes, self.accessSystem,
                    deepcopy(self.__titlesRefs, memo),
                    deepcopy(self.__namesRefs, memo))
        m.current_info = self.current_info
        m.set_mod_funct(self.__modFunct)
        return m

    def copy(self):
        """Return a deep copy of the object itself."""
        return deepcopy(self)

    def __str__(self):
        """Simply print the short title."""
        return self.get('title', '')

    def summary(self):
        """Return a string with a pretty-printed summary for the movie."""
        if not self:
            return ''
        s = 'Movie\n=====\n'
        title = self.get('long imdb canonical title')
        if title:
            s += 'Title: %s\n' % title
        genres = self.get('genres')
        if genres:
            s += 'Genres: '
            for gen in genres:
                s += gen + ', '
            s = s[:-2] + '.\n'
        director = self.get('director')
        if director:
            s += 'Director: '
            for name in director:
                s += str(name)
                if name.currentRole:
                    s += ' (%s)' % name.currentRole
                s += ', '
            s = s[:-2] + '.\n'
        writer = self.get('writer')
        if writer:
            s += 'Writer: '
            for name in writer:
                s += str(name)
                if name.currentRole:
                    s += ' (%s)' % name.currentRole
                s += ', '
            s = s[:-2] + '.\n'
        cast = self.get('cast')
        if cast:
            cast = cast[:5]
            s += 'Cast: '
            for name in cast:
                s += str(name)
                if name.currentRole:
                    s += ' (%s)' % name.currentRole
                s += ', '
            s = s[:-2] + '.\n'
        runtime = self.get('runtimes')
        if runtime:
            s += 'Runtime: '
            for r in runtime:
                s += r + ', '
            s = s[:-2] + '.\n'
        countries = self.get('countries')
        if countries:
            s += 'Country: '
            for c in countries:
                s += c + ', '
            s = s[:-2] + '.\n'
        lang = self.get('languages')
        if lang:
            s += 'Language: '
            for l in lang:
                s += l + ', '
            s = s[:-2] + '.\n'
        rating = self.get('rating')
        if rating:
            s += 'Rating: %s\n' % rating
        nr_votes = self.get('votes')
        if nr_votes:
            s += 'Votes: %s\n' % nr_votes
        plot = self.get('plot')
        if plot:
            plot = plot[0]
            i = plot.find('::')
            if i != -1:
                plot = plot[i+2:]
            s += 'Plot: %s' % plot
        return s


