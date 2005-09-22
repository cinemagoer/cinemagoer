"""
Person module (imdb package).

This module provides the Person class, used to store information about
a given person.

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
from utils import analyze_name, build_name, modifyStrings, modClearRefs, \
                    modNull, normalizeName


class Person:
    """A Person.

    A Person object emulates (most of) the dictionary interface.

    Every information about a person can be accessed as:
        personObject['information']
    to get a list of the kind of information stored in a
    Person object, use the keys() method; some useful aliases
    are defined (as "biography" for the "mini biography" key);
    see the keys_alias dictionary.
    """
    # The default sets of information retrieved.
    default_info = ('main', 'filmography', 'biography')

    # Aliases for some not-so-intuitive keys.
    keys_alias = {'biography': 'mini biography',
                  'bio': 'mini biography',
                  'misc': 'miscellaneouscrew',
                  'aka': 'akas',
                  'also known as': 'akas',
                  'nick name': 'nick names',
                  'nicks': 'nick names',
                  'miscellaneous crew': 'miscellaneouscrew',
                  'crewmembers': 'miscellaneouscrew',
                  'tv guest': 'notable tv guest appearances',
                  'guest appearances': 'notable tv guest appearances',
                  'spouses': 'spouse',
                  'salary': 'salary history',
                  'salaries': 'salary history',
                  'otherworks': 'other works',
                  "maltin's biography":
                        "biography from leonard maltin's movie encyclopedia",
                  'real name': 'birth name'}

    def __init__(self, personID=None, name='', myName='', myID=None,
                personData={}, currentRole='', notes='', accessSystem=None,
                titlesRefs={}, namesRefs={}, modFunct=modClearRefs):
        """Initialize a Person object.

        *personID* -- the unique identifier for the person.
        *name* -- the name of the Person, if not in the personData dictionary.
        *myName* -- the nickname you use for this person.
        *myID* -- your personal id for this person.
        *personData* -- a dictionary used to initialize the object.
        *currentRole* -- a string representing the current role or duty
                        of the person in a movie.
        *notes* -- notes about the given person for a specific movie
                    or role (e.g.: the alias used in the movie credits).
        *accessSystem* -- a string representing the data access system used.
        *titlesRefs* -- a dictionary with references to movies.
        *namesRefs* -- a dictionary with references to persons.
        *modFunct* -- function called returning text fields.
        """
        self.reset()
        self.accessSystem = accessSystem
        self.set_data(personData, override=1)
        self.update_titlesRefs(titlesRefs)
        self.update_namesRefs(namesRefs)
        if name and not personData.get('name'):
            self.set_name(name)
        self.personID = personID
        self.myName = myName
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
    
    def has_current_info(self, val):
        """Return true if the given set of information is in the list."""
        return val in self.current_info

    def reset(self):
        """Reset the Person object."""
        self.personID = None
        self.__person_data = {}
        self.current_info = []
        self.myName = ''
        self.myID = None
        self.currentRole = ''
        self.notes = ''
        self.__titlesRefs = {}
        self.__namesRefs = {}

    def set_name(self, name):
        """Set the name of the person."""
        d = analyze_name(name)
        self.__person_data.update(d)

    def set_data(self, pd, override=0):
        """Set the person data to the given dictionary; if 'override' is
        set, the previous data is removed, otherwise the two dictionary
        are merged.
        """
        # XXX: uh.  Not sure this the best place/way to do it.
        pd = deepcopy(pd)
        if not override:
            self.__person_data.update(pd)
        else:
            self.__person_data = pd

    def __str__(self):
        """Simply print the short name."""
        return self.get('name', '')

    def clear(self):
        """Reset the dictionary."""
        self.__person_data.clear()
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
        l = self.__person_data.keys()
        if 'name' in l:
            l += ['canonical name', 'long imdb name',
                    'long imdb canonical name']
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
        #       a Person object; right now they're incomplete and should
        #       not be used.
        if not self.__person_data.has_key(key):
            self.__person_data[key] = []
        self.__person_data[key].append(item)

    def set_item(self, key, item):
        """Directly store the item with the given key."""
        self.__person_data[key] = item

    def __setitem__(self, key, item):
        """Directly store the item with the given key."""
        self.__person_data[key] = item
    
    def __contains__(self, item):
        """Return true if this Person has worked in the given Movie."""
        from Movie import Movie
        if not isinstance(item, Movie):
            return 0
        for i in self.__person_data.values():
            if type(i) in (types.ListType, types.TupleType):
                for j in i:
                    if isinstance(j, Movie) and item.isSameTitle(j):
                        return 1
        return 0

    def __delitem__(self, key):
        """Remove the given section or key."""
        # XXX: how to remove an item of a section?
        del self.__person_data[key]

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
        if self.__person_data.has_key('name'):
            if key == 'name':
                return normalizeName(self.__person_data['name'])
            elif key == 'canonical name':
                return self.__person_data['name']
            elif key == 'long imdb name':
                return build_name(self.__person_data)
            elif key == 'long imdb canonical name':
                return build_name(self.__person_data, canonical=1)
        if key in self.keys_alias.keys():
            key = self.keys_alias[key]
        if self.__modFunct is modNull:
            return self.__person_data[key]
        else:
            return modifyStrings(self.__person_data[key], self.__modFunct,
                                    self.__titlesRefs, self.__namesRefs)

    def __nonzero__(self):
        """The Person is "false" if the self.__person_data is empty."""
        # XXX: check the name and the personID?
        if self.__person_data:
            return 1
        return 0

    def __cmp__(self, other):
        """Compare two Person objects."""
        # XXX: check the name and the personID?
        # XXX: use comparison to sort people based on the 
        #      billing position in credits?
        if not isinstance(other, self.__class__):
            return -1
        if self.__person_data == other.__person_data:
            return 0
        return 1

    def isSamePerson(self, other):
        """Return true if two persons have the same name and imdbIndex
        and/or personID.
        """
        if not isinstance(other, self.__class__):
            return 0
        if self.__person_data.has_key('name') and \
                other.__person_data.has_key('name') and \
                build_name(self.__person_data, canonical=1) == \
                build_name(other.__person_data, canonical=1):
            return 1
        if self.accessSystem == other.accessSystem and \
                self.personID and self.personID == other.personID:
            return 1
        return 0

    def __deepcopy__(self, memo):
        """Return a deep copy of a Person instance."""
        p = Person(self.personID, '', self.myName, self.myID,
                    deepcopy(self.__person_data, memo), self.currentRole,
                    self.notes, self.accessSystem,
                    deepcopy(self.__titlesRefs, memo),
                    deepcopy(self.__namesRefs, memo))
        p.current_info = self.current_info
        p.set_mod_funct(self.__modFunct)
        return p

    def copy(self):
        """Return a deep copy of the object itself."""
        return deepcopy(self)

    def summary(self):
        """Return a string with a pretty-printed summary for the person."""
        s = ''
        if not self:
            return ''
        s = 'Person\n=====\n'
        name = self.get('long imdb canonical name')
        if name:
            s += 'Name: %s\n' % name
        bdate = self.get('birth date')
        if bdate:
            s += 'Birth date: %s' % bdate
            bnotes = self.get('birth notes')
            if bnotes:
                s += ' (%s)' % bnotes
            s += '.\n'
        ddate = self.get('death date')
        if ddate:
            s += 'Death date: %s' % ddate
            dnotes = self.get('death notes')
            if dnotes:
                s += ' (%s)' % dnotes
            s += '.\n'
        bio = self.get('mini biography')
        if bio:
            s += 'Biography: %s\n' % bio[0]
        director = self.get('director')
        if director:
            s += 'Last movies directed: '
            for m in director[:3]:
                s += str(m) + '; '
            s = s[:-2] + '.\n'
        act = self.get('actor') or self.get('actress')
        if act:
            s += 'Last movies acted: '
            for m in act[:5]:
                s += str(m) + '; '
            s = s[:-2] + '.\n'
        return s


