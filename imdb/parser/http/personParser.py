"""
parser.http.personParser module (imdb package).

This module provides the classes (and the instances), used to parse
the IMDb pages on the akas.imdb.com server about a person.
E.g., for "Mel Gibson" the referred pages would be:
    categorized:    http://akas.imdb.com/name/nm0000154/maindetails
    biography:      http://akas.imdb.com/name/nm0000154/bio
    ...and so on...

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

from imdb.Movie import Movie
from imdb.utils import analyze_name, build_name, canonicalName
from utils import ParserBase


class HTMLMaindetailsParser(ParserBase):
    """Parser for the "categorized" page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        cparser = HTMLMaindetailsParser()
        result = cparser.parse(categorized_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _init(self):
        # This is the dictionary that will be returned by the parse() method.
        self.__person_data = {}
        
    def _reset(self):
        """Reset the parser."""
        self.__person_data.clear()
        self.__in_name = 0
        self.__name = ''
        self.__in_birth = 0
        self.__in_death = 0
        self.__birth = ''
        self.__death = ''
        self.__in_list = 0
        self.__in_title = 0
        self.__title = ''
        self.__roles = ''
        self.__last_imdbID = ''
        self.__in_sect = 0
        self.__in_b = 0
        self.__sect_name = ''
        self.__in_emailfriend = 0
        self.__in_akas = 0
        self.__aka = ''
        self.__akas = []

    def get_data(self):
        """Return the dictionary."""
        # Split birth/death date/notes.
        b = self.__birth.split('::')
        if b:
            b_date = b[0]
            del b[0]
            b_notes = ''.join(b)
            if b_date:
                self.__person_data['birth date'] = b_date.strip()
            if b_notes:
                self.__person_data['birth notes'] = b_notes.strip()
        d = self.__death.split('::')
        if d:
            d_date = d[0]
            del d[0]
            d_notes = ''.join(d)
            if d_date:
                self.__person_data['death date'] = d_date.strip()
            if d_notes:
                self.__person_data['death notes'] = d_notes.strip()
        if self.__akas:
            self.__person_data['akas'] = self.__akas
        if self.__person_data.has_key('miscellaneouscrew'):
            self.__person_data['miscellaneous crew'] = \
                    self.__person_data['miscellaneouscrew']
            del self.__person_data['miscellaneouscrew']
        return self.__person_data
    
    def start_title(self, attrs):
        self.__in_name = 1

    def end_title(self):
        self.__in_name = 0
        d = analyze_name(self.__name.strip())
        self.__person_data.update(d)

    def do_img(self, attrs):
        alt = self.get_attr_value(attrs, 'alt')
        if alt and alt.lower().strip() == \
                build_name(self.__person_data).lower():
            src = self.get_attr_value(attrs, 'src')
            if src: self.__person_data['headshot'] = src
        if self.__in_list:
            self.__in_list = 0

    def do_br(self, attrs):
        # Birth/death date/notes are separated by a <br> tag.
        if self.__in_birth and self.__birth:
            self.__birth += '::'
        elif self.__in_death and self.__death:
            self.__death += '::'
        elif self.__in_list:
            self.__in_list = 0
        elif self.__in_akas:
            self.__aka = self.__aka.strip()
            if self.__aka:
                self.__akas.append(self.__aka)
                self.__aka = ''

    def start_b(self, attrs):
        self.__in_b = 1

    def end_b(self):
        self.__in_b = 0

    def start_p(self, attrs):
        cl = self.get_attr_value(attrs, 'class')
        if cl == 'ch':
            self.__in_b = 1

    def end_p(self): pass

    def start_form(self, attrs):
        act = self.get_attr_value(attrs, 'action')
        if act and act.lower() == '/emailafriend':
            self.__in_emailfriend = 1

    def end_form(self):
        self.__in_emailfriend = 0

    def do_input(self, attrs):
        if self.__in_emailfriend:
            name = self.get_attr_value(attrs, 'name')
            if name and name.lower() == 'arg':
                value = self.get_attr_value(attrs, 'value')
                if value:
                    d = analyze_name(value)
                    if d.has_key('name'):
                        self.__person_data['name'] = d['name']

    def start_ol(self, attrs): pass

    def end_ol(self):
        self.__death += '::'
        self.__in_sect = 0
        self.__sect_name = ''

    def start_li(self, attrs):
        self.__in_list = 1

    def end_li(self):
        if self.__title and self.__sect_name:
            tit = self.__title
            notes = ''
            self.__roles = self.__roles.strip()
            if len(self.__roles) > 5:
                if self.__roles[0] == '(' and self.__roles[1:5].isdigit():
                    endp = self.__roles.find(')')
                    if endp != -1:
                        tit += ' %s' % self.__roles[:endp+1]
                        self.__roles = self.__roles[endp+1:].strip()
            if self.__roles.startswith('(TV)'):
                tit += ' (TV)'
                self.__roles = self.__roles[4:].strip()
            elif self.__roles.startswith('TV Series'):
                self.__roles = self.__roles[10:].strip()
            elif self.__roles.startswith('(V)'):
                tit += ' (V)'
                self.__roles = self.__roles[3:].strip()
            elif self.__roles.startswith('(mini)'):
                tit += ' (mini)'
                self.__roles = self.__roles[6:].strip()
                if self.__roles.startswith('TV Series'):
                    self.__roles = self.__roles[10:].strip()
            elif self.__roles.startswith('(VG)'):
                tit += ' (VG)'
                self.__roles = self.__roles[4:].strip()
            sp = self.__roles.find('(')
            if sp != -1:
                ep = self.__roles.rfind(')')
                if ep != -1:
                    notes = self.__roles[sp:ep+1]
                    self.__roles = self.__roles[ep+1:].strip()
            if self.__roles.startswith('.... '):
                self.__roles = self.__roles[5:]
            movie = Movie(movieID=self.__last_imdbID, title=tit,
                            accessSystem='http')
            if notes: movie.notes = notes
            movie.currentRole = self.__roles
            sect = self.__sect_name.strip().lower()
            if not self.__person_data.has_key(sect):
                self.__person_data[sect] = []
            self.__person_data[sect].append(movie)
        self.__title = ''
        self.__roles = ''
        self.__in_list = 0

    def start_dd(self, attrs): pass

    def end_dd(self):
        self.__in_birth = 0
        self.__in_death = 0
        if self.__in_akas:
            self.__aka = self.__aka.strip()
            if self.__aka:
                self.__akas.append(self.__aka)
                self.__aka = ''
            self.__in_akas = 0

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        # A movie title.
        if href and href.find('/title/tt') != -1:
            self.__in_title = 1
            imdbID = self.re_imdbID.findall(href)
            if imdbID:
                self.__last_imdbID = imdbID[-1]
        elif self.__in_b:
            name = self.get_attr_value(attrs, 'name')
            if name: self.__in_sect = 1

    def end_a(self):
        self.__in_title = 0
        self.__in_sect = 0

    def _handle_data(self, data):
        sdata = data.strip()
        sldata = sdata.lower()
        if self.__in_name:
            self.__name += data
        elif self.__in_birth:
            if self.__birth and not self.__birth[-1].isspace():
                self.__birth += ' '
            self.__birth += sdata
        elif self.__in_death:
            if self.__death and not self.__death[-1].isspace():
                self.__death += ' '
            self.__death += sdata
        elif self.__in_akas:
            self.__aka += data
        elif sldata.startswith('date of death'):
            self.__in_death = 1
        elif sldata.startswith('date of birth'):
            self.__in_birth = 1
        elif sldata.startswith('sometimes credited as'):
            self.__in_akas = 1
        elif self.__in_sect:
            self.__sect_name += sldata
        elif self.__in_title:
            self.__title += data
        elif self.__in_list:
            if self.__roles and not self.__roles[-1].isspace():
                self.__roles += ' '
            self.__roles += data.strip()


class HTMLBioParser(ParserBase):
    """Parser for the "biography" page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        bioparser = HTMLBioParser()
        result = bioparser.parse(biography_html_string)
    """
    def _init(self):
        # This is the dictionary that will be returned by the parse() method.
        self.__bio_data = {}

    def _reset(self):
        """Reset the parser."""
        self.__bio_data.clear()
        self.__sect_name = ''
        self.__sect_data = ''
        self.__in_sect = 0
        self.__in_sect_name = 0

    def get_data(self):
        """Return the dictionary."""
        return self.__bio_data

    def do_br(self, attrs):
        if self.__sect_name.lower() == 'mini biography' and self.__sect_data \
                and  not self.__sect_data[-1].isspace():
            self.__sect_data += ' '

    def start_a(self, attrs): pass

    def end_a(self): pass

    def start_dt(self, attrs):
        self.__in_sect = 1
        self.__in_sect_name = 1

    def end_dt(self):
        self.__in_sect_name = 0

    def start_dd(self, attrs): pass

    def end_dd(self):
        # Add a new section in the biography.
        if self.__sect_name and self.__sect_data:
            sect = self.__sect_name.strip().lower()
            # XXX: to get rid of the last colons.
            if sect[-1] == ':':
                sect = sect[:-1]
            if sect == 'salary': sect = 'salary history'
            elif sect == 'nickname': sect = 'nick names'
            elif sect == 'where are they now': sect = 'where now'
            elif sect == 'personal quotes': sect = 'quotes'
            data = self.__sect_data.strip()
            d_split = data.split('::')
            d_split[:] = filter(None, [x.strip() for x in d_split])
            if sect == 'salary history':
                newdata = []
                for j in d_split:
                    j = filter(None, [x.strip() for x in j.split('@@@@')])
                    newdata.append('::'.join(j))
                d_split[:] = newdata
            if sect in ('height', 'birth name'):
                self.__bio_data[sect] = canonicalName(d_split[0])
            elif sect == 'imdb mini-biography by' and \
                    self.__bio_data.has_key('mini biography'):
                self.__bio_data['mini biography'][-1] = '%s::%s' % (d_split[0],
                                    self.__bio_data['mini biography'][-1])
                    
            else:
                # Multiple items are added separately (e.g.: 'trivia' is
                # a list of strings).
                if not self.__bio_data.has_key(sect):
                    self.__bio_data[sect] = []
                for d in [x.strip() for x in d_split]:
                    if not d: continue
                    self.__bio_data[sect].append(d)
                if not self.__bio_data[sect]: del self.__bio_data[sect]
        self.__sect_name = ''
        self.__sect_data = ''
        self.__in_sect = 0

    def start_p(self, attrs):
        if self.__in_sect:
            if self.__sect_data:
                self.__sect_data += '::'

    def end_p(self): pass

    def start_tr(self, attrs):
        if self.__in_sect:
            if self.__sect_data:
                if self.__sect_data[-1].isspace():
                    self.__sect_data = self.__sect_data.strip()
                self.__sect_data += '::'

    def end_tr(self): pass

    def start_td(self, attrs): pass

    def end_td(self):
        if self.__in_sect and \
                self.__sect_name.strip().lower() in \
                ('salary', 'salary history'):
            if self.__sect_data: self.__sect_data += '@@@@'
    
    def _handle_data(self, data):
        if self.__in_sect_name:
            self.__sect_name += data
        elif self.__in_sect:
            if not data.isspace() and self.__sect_data \
                    and self.__sect_data[-1].isspace():
                data = data.strip()
            self.__sect_data += data.replace('\n', ' ')


class HTMLOtherWorksParser(ParserBase):
    """Parser for the "other works" and "agent" pages of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        owparser = HTMLOtherWorksParser()
        result = owparser.parse(otherworks_html_string)
    """

    def _init(self):
        self.kind = 'other works'
    
    def _reset(self):
        """Reset the parser."""
        self.__in_ow = 0
        self.__ow = []
        self.__cow = ''
        self.__dostrip = 0

    def get_data(self):
        """Return the dictionary."""
        if not self.__ow: return {}
        return {self.kind: self.__ow}

    def start_dd(self, attrs):
        self.__in_ow = 1

    def end_dd(self): pass

    def start_b(self, attrs): pass

    def end_b(self):
        if self.kind == 'agent' and self.__in_ow and self.__cow:
            self.__cow += '::'
            self.__dostrip = 1

    def do_br(self, attrs):
        if self.__in_ow and self.__cow:
            self.__ow.append(self.__cow.strip())
            self.__cow = ''

    def start_dl(self, attrs): pass

    def end_dl(self):
        self.do_br([])
        self.__in_ow = 0
    
    def _handle_data(self, data):
        if self.__in_ow:
            if self.__dostrip:
                data = data.lstrip()
                if data: self.__dostrip = 0
            self.__cow += data


# The used instances.
maindetails_parser = HTMLMaindetailsParser()
bio_parser = HTMLBioParser()
otherworks_parser = HTMLOtherWorksParser()
agent_parser = HTMLOtherWorksParser()
agent_parser.kind = 'agent'
from movieParser import HTMLOfficialsitesParser
person_officialsites_parser = HTMLOfficialsitesParser()
from movieParser import HTMLAwardsParser
person_awards_parser = HTMLAwardsParser()
person_awards_parser.subject = 'name'
from movieParser import HTMLTechParser
publicity_parser = HTMLTechParser()
publicity_parser.kind = 'publicity'
from movieParser import news_parser

