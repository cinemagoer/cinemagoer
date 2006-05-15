"""
parser.http.personParser module (imdb package).

This module provides the classes (and the instances), used to parse
the IMDb pages on the akas.imdb.com server about a person.
E.g., for "Mel Gibson" the referred pages would be:
    categorized:    http://akas.imdb.com/name/nm0000154/maindetails
    biography:      http://akas.imdb.com/name/nm0000154/bio
    ...and so on...

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

from imdb.Movie import Movie
from imdb.utils import analyze_name, build_name, canonicalName, \
                        normalizeName, analyze_title
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
        self._person_data = {}

    def _reset(self):
        """Reset the parser."""
        self._person_data.clear()
        self._in_name = 0
        self._name = u''
        self._in_birth = 0
        self._in_death = 0
        self._birth = ''
        self._death = ''
        self._in_list = 0
        self._in_title = 0
        self._title = ''
        self._seen_br = 0
        self._roles = ''
        self._last_imdbID = ''
        self._get_imdbID = 0
        self._in_sect = 0
        self._in_b = 0
        self._sect_name = ''
        self._in_emailfriend = 0
        self._in_akas = 0
        self._aka = ''
        self._akas = []

    def get_data(self):
        """Return the dictionary."""
        # Split birth/death date/notes.
        b = self._birth.split('::')
        if b:
            b_date = b[0]
            del b[0]
            b_notes = ''.join(b)
            if b_date:
                self._person_data['birth date'] = b_date.strip()
            if b_notes:
                self._person_data['birth notes'] = b_notes.strip()
        d = self._death.split('::')
        if d:
            d_date = d[0]
            del d[0]
            d_notes = ''.join(d)
            if d_date:
                self._person_data['death date'] = d_date.strip()
            if d_notes:
                self._person_data['death notes'] = d_notes.strip()
        if self._akas:
            self._person_data['akas'] = self._akas
        if self._person_data.has_key('miscellaneouscrew'):
            self._person_data['miscellaneous crew'] = \
                    self._person_data['miscellaneouscrew']
            del self._person_data['miscellaneouscrew']
        return self._person_data

    def start_title(self, attrs):
        self._in_name = 1

    def end_title(self):
        self._in_name = 0
        d = analyze_name(self._name.strip(), canonical=1)
        self._person_data.update(d)

    def do_img(self, attrs):
        alt = self.get_attr_value(attrs, 'alt')
        if alt and alt.lower().strip() == \
                build_name(self._person_data).lower():
            src = self.get_attr_value(attrs, 'src')
            if src: self._person_data['headshot'] = src
        if self._in_list:
            self._in_list = 0

    def do_br(self, attrs):
        self._seen_br = 1
        # Birth/death date/notes are separated by a <br> tag.
        if self._in_birth and self._birth:
            self._birth += '::'
        elif self._in_death and self._death:
            self._death += '::'
        elif self._in_list:
            self._in_list = 0
        elif self._in_akas:
            self._aka = self._aka.strip()
            if self._aka:
                self._akas.append(self._aka)
                self._aka = ''

    def start_b(self, attrs):
        self._in_b = 1

    def end_b(self):
        self._in_b = 0

    def start_p(self, attrs):
        cl = self.get_attr_value(attrs, 'class')
        if cl == 'ch':
            self._in_b = 1

    def end_p(self): pass

    def start_form(self, attrs):
        act = self.get_attr_value(attrs, 'action')
        if act and act.lower() == '/emailafriend':
            self._in_emailfriend = 1

    def end_form(self):
        self._in_emailfriend = 0

    def do_input(self, attrs):
        if self._in_emailfriend and not self._person_data.has_key('name'):
            name = self.get_attr_value(attrs, 'name')
            if name and name.lower() == 'arg':
                value = self.get_attr_value(attrs, 'value')
                if value:
                    d = analyze_name(value, canonical=1)
                    self._person_data.update(d)

    def start_ol(self, attrs): pass

    def end_ol(self):
        self._death += '::'
        self._in_sect = 0
        self._sect_name = ''

    def start_li(self, attrs):
        self._in_list = 1
        self._seen_br = 0
        self._get_imdbID = 1

    def end_li(self):
        if self._title and self._sect_name:
            tit = self._title
            notes = ''
            self._roles = self._roles.strip()
            if len(self._roles) > 5:
                if self._roles[0] == '(' and self._roles[1:5].isdigit():
                    endp = self._roles.find(')')
                    if endp != -1:
                        tit += ' %s' % self._roles[:endp+1]
                        self._roles = self._roles[endp+1:].strip()
            if self._roles.startswith('(TV)'):
                tit += ' (TV)'
                self._roles = self._roles[4:].strip()
            elif self._roles.startswith('TV Series'):
                self._roles = self._roles[10:].strip()
            elif self._roles.startswith('(V)'):
                tit += ' (V)'
                self._roles = self._roles[3:].strip()
            elif self._roles.startswith('(mini)'):
                tit += ' (mini)'
                self._roles = self._roles[6:].strip()
                if self._roles.startswith('TV Series'):
                    self._roles = self._roles[10:].strip()
            elif self._roles.startswith('(VG)'):
                tit += ' (VG)'
                self._roles = self._roles[4:].strip()
            sp = self._roles.find('(')
            if sp != -1:
                ep = self._roles.rfind(')')
                if ep != -1:
                    notes = self._roles[sp:ep+1]
                    self._roles = self._roles[:sp-1].strip()
            if self._roles.startswith('.... '):
                self._roles = self._roles[5:]
            movie = Movie(movieID=str(self._last_imdbID), title=tit,
                            accessSystem='http')
            if notes: movie.notes = notes
            movie.currentRole = self._roles
            sect = self._sect_name.strip().lower()
            self._person_data.setdefault(sect, []).append(movie)
        self._title = ''
        self._roles = ''
        self._in_list = 0
        self._seen_br = 0

    def start_dd(self, attrs): pass

    def end_dd(self):
        self._in_birth = 0
        self._in_death = 0
        if self._in_akas:
            self._aka = self._aka.strip()
            if self._aka:
                self._akas.append(self._aka)
                self._aka = ''
            self._in_akas = 0

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        # A movie title.
        if self._get_imdbID and href and href.find('/title/tt') != -1:
            self._in_title = 1
            imdbID = self.re_imdbID.findall(href)
            if imdbID:
                self._last_imdbID = imdbID[-1]
                self._get_imdbID = 0
        elif self._in_b:
            name = self.get_attr_value(attrs, 'name')
            if name: self._in_sect = 1

    def end_a(self):
        self._in_title = 0
        self._in_sect = 0

    def _handle_data(self, data):
        sdata = data.strip()
        sldata = sdata.lower()
        if self._in_name:
            self._name += data
        elif self._in_birth:
            if self._birth and not self._birth[-1].isspace():
                self._birth += ' '
            self._birth += sdata
        elif self._in_death:
            if self._death and not self._death[-1].isspace():
                self._death += ' '
            self._death += sdata
        elif self._in_akas:
            self._aka += data
        elif sldata.startswith('date of death'):
            self._in_death = 1
        elif sldata.startswith('date of birth'):
            self._in_birth = 1
        elif sldata.startswith('sometimes credited as'):
            self._in_akas = 1
        elif self._in_sect:
            self._sect_name += sldata
        elif self._in_title and not self._seen_br:
            self._title += data
        elif self._in_list:
            self._roles += data


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
        self._bio_data = {}

    def _reset(self):
        """Reset the parser."""
        self._bio_data.clear()
        self._sect_name = ''
        self._sect_data = ''
        self._in_sect = 0
        self._in_sect_name = 0

    def get_data(self):
        """Return the dictionary."""
        return self._bio_data

    def do_br(self, attrs):
        if self._sect_name.lower() == 'mini biography' and self._sect_data \
                and  not self._sect_data[-1].isspace():
            self._sect_data += ' '

    def start_a(self, attrs): pass

    def end_a(self): pass

    def start_dt(self, attrs):
        self._in_sect = 1
        self._in_sect_name = 1

    def end_dt(self):
        self._in_sect_name = 0

    def start_dd(self, attrs): pass

    def end_dd(self):
        # Add a new section in the biography.
        if self._sect_name and self._sect_data:
            sect = self._sect_name.strip().lower()
            # XXX: to get rid of the last colons.
            if sect[-1] == ':':
                sect = sect[:-1]
            if sect == 'salary': sect = 'salary history'
            elif sect == 'nickname': sect = 'nick names'
            elif sect == 'where are they now': sect = 'where now'
            elif sect == 'personal quotes': sect = 'quotes'
            data = self._sect_data.strip()
            d_split = data.split('::')
            d_split[:] = filter(None, [x.strip() for x in d_split])
            if sect == 'salary history':
                newdata = []
                for j in d_split:
                    j = filter(None, [x.strip() for x in j.split('@@@@')])
                    newdata.append('::'.join(j))
                d_split[:] = newdata
            elif sect == 'nick names':
                d_split[:] = [normalizeName(x) for x in d_split]
            if sect == 'birth name':
                self._bio_data[sect] = canonicalName(d_split[0])
            elif sect == 'height':
                self._bio_data[sect] = d_split[0]
            elif sect == 'imdb mini-biography by' and \
                    self._bio_data.has_key('mini biography'):
                self._bio_data['mini biography'][-1] = '%s::%s' % (d_split[0],
                                    self._bio_data['mini biography'][-1])

            elif d_split:
                # Multiple items are added separately (e.g.: 'trivia' is
                # a list of strings).
                self._bio_data[sect] = d_split
        self._sect_name = ''
        self._sect_data = ''
        self._in_sect = 0

    def start_p(self, attrs):
        if self._in_sect:
            if self._sect_data:
                self._sect_data += '::'

    def end_p(self): pass

    def start_tr(self, attrs):
        if self._in_sect:
            if self._sect_data:
                if self._sect_data[-1].isspace():
                    self._sect_data = self._sect_data.strip()
                self._sect_data += '::'

    def end_tr(self): pass

    def start_td(self, attrs): pass

    def end_td(self):
        if self._in_sect and \
                self._sect_name.strip().lower() in \
                ('salary', 'salary history'):
            if self._sect_data: self._sect_data += '@@@@'

    def _handle_data(self, data):
        if self._in_sect_name:
            self._sect_name += data
        elif self._in_sect:
            if not data.isspace() and self._sect_data \
                    and self._sect_data[-1].isspace():
                data = data.strip()
            self._sect_data += data.replace('\n', ' ')


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
        self._in_ow = 0
        self._ow = []
        self._cow = ''
        self._dostrip = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._ow: return {}
        return {self.kind: self._ow}

    def start_dd(self, attrs):
        self._in_ow = 1

    def end_dd(self): pass

    def start_b(self, attrs): pass

    def end_b(self):
        if self.kind == 'agent' and self._in_ow and self._cow:
            self._cow += '::'
            self._dostrip = 1

    def do_br(self, attrs):
        if self._in_ow and self._cow:
            self._ow.append(self._cow.strip())
            self._cow = ''

    def start_dl(self, attrs): pass

    def end_dl(self):
        self.do_br([])
        self._in_ow = 0

    def _handle_data(self, data):
        if self._in_ow:
            if self._dostrip:
                data = data.lstrip()
                if data: self._dostrip = 0
            self._cow += data


class HTMLSeriesParser(ParserBase):
    """Parser for the "by TV series" page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = HTMLSeriesParser()
        result = sparser.parse(filmoseries_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._episodes = {}
        self._seen_h1 = 0
        self._in_b = 0
        self._in_episodes = 0
        self._in_ol = 0
        self._in_li = 0
        self._in_series_title = 0
        self._series_id = None
        self._cur_series_title = u''
        self._cur_series = None
        self._in_episode_title = 0
        self._episode_id = None
        self._cur_episode_title = u''
        self._in_misc_info = 0
        self._misc_info = u''
        self._in_i = 0
        self._got_i_info = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._episodes: return {}
        return {'episodes': self._episodes}

    def start_h1(self, attrs): pass

    def end_h1(self): self._seen_h1 = 1

    def start_b(self, attrs): self._in_b = 1

    def end_b(self): self._in_b = 0

    def start_i(self, attrs): self._in_i = 1

    def end_i(self): self._in_i = 0

    def start_ol(self, attrs): self._in_ol = 1

    def end_ol(self):
        self._in_ol = 0
        self._cur_series_title = u''
        self._cur_series = None
        self._series_id = None

    def start_li(self, attrs):
        self._in_li = 1
        self._got_i_info = 0

    def end_li(self):
        self._in_li = 0
        if self._in_episodes:
            et = self._cur_episode_title.strip()
            minfo = self._misc_info.strip()
            if et and self._episode_id:
                eps_data = analyze_title(et, canonical=1)
                eps_data['kind'] = 'episode'
                e = Movie(movieID=str(self._episode_id), data=eps_data,
                            accessSystem='http')
                e['episode of'] = self._cur_series
                if minfo.startswith('('):
                    pe = minfo.find(')')
                    if pe != -1:
                        date = minfo[1:pe]
                        if date != '????':
                            e['original air date'] = date
                            if eps_data.get('year', '????') == '????':
                                syear = date.split()[-1]
                                if syear.isdigit():
                                    e['year'] = syear
                rolei = minfo.find(' - ')
                if rolei != -1:
                    if not self._got_i_info:
                        role = ''
                        role = minfo[rolei+3:].strip()
                        notei = role.rfind('(')
                        note = ''
                        if notei != -1 and role and role[-1] == ')':
                            note = role[notei:]
                            role = role[:notei].strip()
                        e.notes = note
                        e.currentRole = role
                    else:
                        randn = minfo[rolei+3:].strip().split()
                        note = '[%s]' % randn[0]
                        note += ' '.join(randn[1:])
                        e.notes = note
                self._episodes.setdefault(self._cur_series, []).append(e)
            self._cur_episode_title = u''
            self._episode_id = None
        self._in_misc_info = 0
        self._misc_info = u''

    def start_a(self, attrs):
        if not self._in_episodes: return
        if self._in_ol:
            if not self._in_li: return
            href = self.get_attr_value(attrs, 'href')
            if not href: return
            mid = self.re_imdbID.findall(href)
            if not mid: return
            self._in_episode_title = 1
            self._episode_id = mid[0]
            return
        else:
            href = self.get_attr_value(attrs, 'href')
            if not href: return
            mid = self.re_imdbID.findall(href)
            if not mid: return
            self._in_series_title = 1
            self._series_id = mid[0]

    def end_a(self):
        if self._in_episode_title:
            self._in_episode_title = 0
            self._in_misc_info = 1
        elif self._in_series_title:
            self._in_series_title = 0
            st = self._cur_series_title.strip()
            if st and self._series_id is not None:
                series_data = analyze_title(st, canonical=1)
                s = Movie(movieID=str(self._series_id), data=series_data,
                                accessSystem='http')
                self._cur_series = s

    def _handle_data(self, data):
        if self._seen_h1 and self._in_b:
            if data.strip().lower().find('filmography by series'):
                self._seen_h1 = 0
                self._in_episodes = 1
                return
        elif self._in_episode_title:
            self._cur_episode_title += data
        elif self._in_series_title:
            self._cur_series_title += data
        elif self._in_misc_info:
            # Handles roles like "director".
            if self._in_i:
                # Put these info in the "notes" property.
                data = data.lower()
                self._got_i_info = 1
            self._misc_info += data


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
person_series_parser = HTMLSeriesParser()

