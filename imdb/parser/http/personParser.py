"""
parser.http.personParser module (imdb package).

This module provides the classes (and the instances), used to parse
the IMDb pages on the akas.imdb.com server about a person.
E.g., for "Mel Gibson" the referred pages would be:
    categorized:    http://akas.imdb.com/name/nm0000154/maindetails
    biography:      http://akas.imdb.com/name/nm0000154/bio
    ...and so on...

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

from imdb.Movie import Movie
from imdb.utils import analyze_name, canonicalName, \
                        normalizeName, analyze_title, date_and_notes
from utils import ParserBase, build_movie


class HTMLMaindetailsParser(ParserBase):
    """Parser for the "categorized" (maindetails) page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        cparser = HTMLMaindetailsParser()
        result = cparser.parse(categorized_html_string)
    """

    def _init(self):
        self.kind = 'person'

    def _reset(self):
        self._data = {}
        self._in_title = False
        self._title = u''
        # Get section names.
        self._in_h5 = False
        self._section = u''
        # Sections are ended by br tags.
        self._in_post_section = False
        # Stop before the Additional Details section.
        self._stop_here = False
        self._in_tn15more = False
        # Most of the information are stored here.
        self._cur_txt = u''
        # Handle filmography.
        self._in_ol = False
        self._in_i = False
        self._in_movie = False
        # The movie title/role/notes is stored here.
        self._movie = u''
        # Stop before akas/episodes information.
        self._seen_br = False
        self._in_headshot = False
        self._cur_status = u''
        # Get a movieID.
        self._last_imdbID = None
        self._last_nameIDs = []
        self._get_imdbID = False
        self._cids = []
        self._seen_movie_sep = False

    def get_data(self):
        return self._data

    def start_title(self, attrs):
        self._in_title = True

    def end_title(self):
        self._in_title = False
        self._title = self._title.strip()
        if self._title:
            if self.kind != 'character':
                self._data.update(analyze_name(self._title, canonical=1))
            else:
                self._title = self._title.replace('(Character)', '').strip()
                self._data['name'] = self._title

    def start_h5(self, attrs):
        if self._stop_here or not self._in_content: return
        self._seen_br = False
        self._in_h5 = True
        self._in_post_section = False
        self._section = u''
        self._cur_txt = u''
        self._in_movie = False

    def end_h5(self):
        if self._stop_here or not self._in_content: return
        self._in_h5 = False
        self._section = str(self._section.strip().lower())
        if self._section[-1:] == ':':
            self._section = self._section[:-1].rstrip()
        # XXX: I don't like this way at all: here we're excluding some
        #      useless section, but who knows how many other there can be?
        if self._section in (u'', 'genres', 'awards', 'publicity listings',
                            'other works', 'trivia'):
            return
        # Do some basic transformation.
        if self._section in ('sometimes credited as', 'alternate names'):
            self._section = 'akas'
        elif self._section == 'date of birth':
            self._section = 'birth date'
        elif self._section == 'date of death':
            self._section = 'death date'
        self._in_post_section = True

    def do_img(self, attrs):
        if self._in_headshot:
            src = self.get_attr_value(attrs, 'src')
            if src:
                self._data['headshot'] = src
        if self._stop_here or not self._in_content: return
        if self.get_attr_value(attrs, 'alt') == 'Additional Details':
            self._stop_here = True

    def do_input(self, attrs):
        itype = self.get_attr_value(attrs, 'type')
        if itype is None or itype.lower() != 'hidden': return
        iname = self.get_attr_value(attrs, 'name')
        if iname is None or iname != 'primary': return
        ivalue = self.get_attr_value(attrs, 'value')
        if ivalue is None: return
        # It's hard to catch the correct 'Surname, Name' from the
        # title, so if the "credited alongside another name" form
        # is found, use it.
        self._data.update(analyze_name(ivalue, canonical=0))

    def start_div(self, attrs): pass

    def end_div(self):
        pass
        self.do_br([])

    def do_br(self, attrs):
        if self._stop_here or not self._in_content: return
        # Inside li tags in filmography, some useless information after a br.
        self._seen_br = True
        self._cur_txt = self._cur_txt.strip()
        if not (self._in_post_section and self._section and self._cur_txt):
            self._in_post_section = False
            self._cur_txt = u''
            return
        # We're at the end of a section.
        if self._section == 'birth date':
            date, notes = date_and_notes(self._cur_txt)
            if date:
                self._data['birth date'] = date
            if notes:
                self._data['birth notes'] = notes
        elif self._section == 'death date':
            date, notes = date_and_notes(self._cur_txt)
            if date:
                self._data['death date'] = date
            if notes:
                self._data['death notes'] = notes
        elif self._section == 'akas':
            sep = ' | '
            if self.kind == 'character':
                sep = ' / '
            akas = self._cur_txt.split(sep)
            if akas: self._data['akas'] = akas
        # XXX: not providing an 'else', we're deliberately ignoring
        #      other sections.
        self._in_post_section = False
        if self.kind == 'character':
            # XXX: I'm not confident this is the best place for this...
            self._section = 'filmography'
        self._cur_txt = u''

    def start_a(self, attrs):
        name = self.get_attr_value(attrs, 'name')
        if name and name.lower() == 'headshot':
            self._in_headshot = True
        if self._stop_here or not self._in_content: return
        cls = self.get_attr_value(attrs, 'class')
        # Detect "more" links.
        if cls and cls.startswith('tn15more'):
            self._in_tn15more = True
        href = self.get_attr_value(attrs, 'href')
        if href and href.find('/character/ch') != -1:
            imdbID = self.re_imdbID.findall(href)
            if imdbID:
                self._cids.append(imdbID[-1])
        elif href and href.find('/name/nm') != -1:
            imdbID = self.re_imdbID.findall(href)
            if imdbID:
                self._last_nameIDs.append(imdbID[-1])
        if not (self._in_movie and self._get_imdbID): return
        # A movie title.
        if href and href.find('/title/tt') != -1:
            imdbID = self.re_imdbID.findall(href)
            if imdbID:
                self._last_imdbID = imdbID[-1]
                self._get_imdbID = False

    def end_a(self):
        if self._in_headshot:
            self._in_headshot = False
        if self._in_tn15more:
            self._in_tn15more = False

    def start_ol(self, attrs):
        if self._stop_here or not self._in_content: return
        # We're not in a informational section, but in a filmography list.
        self._in_post_section = False
        self._in_ol = True
        self._cur_txt = u''

    def end_ol(self):
        if self._stop_here or not self._in_content: return
        self._in_ol = False

    def start_li(self, attrs):
        if self._stop_here or not self._in_content: return
        # We're reading a movie title/role/notes.
        if self._in_ol:
            self._get_imdbID = True
            self._in_movie = True
        self._last_imdbID = None
        self._last_nameIDs = []
        self._cids = []
        self._cur_status = u''
        self._movie = u''
        self._seen_movie_sep = False
        self._seen_br = False

    def end_li(self):
        if self._stop_here or not self._in_content: return
        self._get_imdbID = False
        if not self._in_movie: return
        self._movie = self._movie.strip()
        self._cur_status = self._cur_status.strip()
        if not (self._movie and self._last_imdbID and self._section): return
        if not self._cids:
            self._cids = None
        elif len(self._cids) == 1:
            self._cids = self._cids[0]
        # Add this movie to the list.
        kwds = {'movieID': self._last_imdbID, 'status': self._cur_status,
                'roleID': self._cids, 'modFunct': self._modFunct,
                'accessSystem': self._as}
        if self.kind == 'character':
            kwds['_parsingCharacter'] = True
            lnids = self._last_nameIDs
            if not lnids:
                lnids = None
            elif len(lnids) == 1:
                lnids = lnids[0]
            kwds['roleID'] = lnids
        movie = build_movie(self._movie, **kwds)
        self._data.setdefault(self._section, []).append(movie)

    def start_i(self, attrs):
        self._in_i = True

    def end_i(self):
        self._in_i = False

    def _handle_data(self, data):
        if self._in_title:
            self._title += data
        if self._stop_here or not self._in_content: return
        if self._in_h5:
            self._section += data
        elif self._in_post_section and not self._in_tn15more:
            self._cur_txt += data
        elif self._in_movie and not self._seen_br:
            if self._in_i:
                self._cur_status += data
            else:
                # XXX: keeps multiple characterIDs separated; quite a mess.
                if self._section in ('actor', 'actress', 'self'):
                    ldata = data
                    if not self._seen_movie_sep:
                        # Consider only ' / ' after the separator.
                        sepIdx = ldata.find(' ....')
                        if sepIdx != -1:
                            ldata = ldata[sepIdx+5:]
                    nrSep = ldata.count(' / ')
                    if nrSep > 0:
                        sdata = data.strip()
                        if sdata.endswith(' /') and sdata.startswith('/ '):
                            nrSep -= 1
                        self._cids += [None]*nrSep
                if not self._seen_movie_sep and data.find(' ....') != -1:
                    self._seen_movie_sep = True
                self._movie += data


class HTMLBioParser(ParserBase):
    """Parser for the "biography" page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        bioparser = HTMLBioParser()
        result = bioparser.parse(biography_html_string)
    """
    # XXX: this parser is really old; consider a rewrite.
    _defGetRefs = True

    def _init(self):
        # This is the dictionary that will be returned by the parse() method.
        self._bio_data = {}

    def _reset(self):
        """Reset the parser."""
        self._bio_data.clear()
        self._sect_name = u''
        self._sect_data = u''
        self._in_sect = 0
        self._in_sect_name = 0

    def get_data(self):
        """Return the dictionary."""
        return self._bio_data

    def _end_content(self):
        self._add_items()
        if self._bio_data.has_key('mini biography'):
            nl = []
            for bio in self._bio_data['mini biography']:
                byidx = bio.rfind('IMDb Mini Biography By')
                if byidx != -1:
                    bio = u'%s::%s' % (bio[byidx+23:].lstrip(),
                                        bio[:byidx].rstrip())
                nl.append(bio)
            self._bio_data['mini biography'][:] = nl

    def do_br(self, attrs):
        snl = self._sect_name.lower()
        if snl != 'mini biography':
            self._add_items()
        if snl == 'mini biography' and self._sect_data \
                and  not self._sect_data[-1].isspace():
            self._sect_data += ' '

    def start_a(self, attrs): pass

    def end_a(self): pass

    def start_h5(self, attrs):
        if self._in_content:
            self._add_items()
            self._in_sect = 1
            self._in_sect_name = 1
            self._sect_name = u''

    def end_h5(self):
        if self._in_sect_name:
            self._in_sect_name = 0

    def do_hr(self, attrs):
        if self._in_content: self._in_content = 0

    def start_dd(self, attrs): pass

    def _add_items(self):
        # Add a new section in the biography.
        if self._in_content and self._sect_name and self._sect_data:
            sect = self._sect_name.strip().lower()
            # XXX: to get rid of the last colons and normalize section names.
            if sect[-1] == ':':
                sect = sect[:-1]
            if sect == 'salary':
                sect = 'salary history'
            elif sect == 'nickname':
                sect = 'nick names'
            elif sect == 'where are they now':
                sect = 'where now'
            elif sect == 'personal quotes':
                sect = 'quotes'
            elif sect == 'date of birth':
                sect = 'birth date'
            elif sect == 'date of death':
                sect = 'death date'
            data = self._sect_data.strip()
            d_split = data.split('::')
            d_split[:] = filter(None, [x.strip() for x in d_split])
            # Do some transformation on some special cases.
            if sect == 'salary history':
                newdata = []
                for j in d_split:
                    j = filter(None, [x.strip() for x in j.split('@@@@')])
                    newdata.append('::'.join(j))
                d_split[:] = newdata
            elif sect == 'nick names':
                d_split[:] = [normalizeName(x) for x in d_split]
            elif sect == 'birth name':
                d_split = canonicalName(d_split[0])
            elif sect == 'height':
                d_split = d_split[0]
            elif sect == 'spouse':
                d_split[:] = [x.replace(' (', '::(', 1).replace(' ::', '::')
                                for x in d_split]
            # Birth/death date are in both maindetails and bio pages;
            # it's safe to collect both of them.
            if sect == 'birth date':
                date, notes = date_and_notes(d_split[0])
                if date:
                    self._bio_data['birth date'] = date
                if notes:
                    self._bio_data['birth notes'] = notes
            elif sect == 'death date':
                date, notes = date_and_notes(d_split[0])
                if date:
                    self._bio_data['death date'] = date
                if notes:
                    self._bio_data['death notes'] = notes
            elif d_split:
                # Multiple items are added separately (e.g.: 'trivia' is
                # a list of strings).
                self._bio_data[sect] = d_split
        self._sect_name = u''
        self._sect_data = u''
        self._in_sect = 0

    def start_p(self, attrs):
        if self._in_sect:
            if self._sect_data:
                if self._sect_data[-1].isspace():
                    self._sect_data = self._sect_data.rstrip()
                self._sect_data += '::'

    def end_p(self): pass

    def start_tr(self, attrs):
        if self._in_sect:
            if self._sect_data:
                if self._sect_data[-1].isspace():
                    self._sect_data = self._sect_data.rstrip()
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
    _defGetRefs = True

    def _init(self):
        self.kind = 'other works'

    def _reset(self):
        """Reset the parser."""
        self._ow = []
        self._cow = u''
        self._dostrip = 0
        self._seen_hr = 0
        self._seen_h5 = 0
        self._seen_left_div = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._ow: return {}
        return {self.kind: self._ow}

    def start_b(self, attrs): pass

    def end_b(self):
        if self._seen_hr: return
        if self.kind == 'agent' and self._in_content and self._cow:
            self._cow += '::'
            self._dostrip = 1

    def start_h5(self, attrs): pass

    def end_h5(self):
        self._seen_h5 = 1

    def start_div(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.strip().lower() == 'left':
            self._seen_left_div = 1

    def end_div(self): pass

    def do_hr(self, attrs):
        self._seen_hr = 1

    def do_br(self, attrs):
        if self._seen_hr: return
        self._cow = self._cow.strip()
        if self._in_content and self._cow:
            self._ow.append(self._cow)
            self._cow = u''

    def _handle_data(self, data):
        if not self._seen_h5: return
        if self._seen_hr or self._seen_left_div: return
        if self._in_content:
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
    def _reset(self):
        """Reset the parser."""
        self._episodes = {}
        self._seen_h1 = 0
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
        self._in_span = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._episodes: return {}
        return {'episodes': self._episodes}

    def start_h1(self, attrs): self._seen_h1 = 1

    def end_h1(self): self._seen_h1 = 0

    def start_i(self, attrs): self._in_i = 1

    def end_i(self): self._in_i = 0

    def start_div(self, attrs):
        if not self._in_content: return
        if self.get_attr_value(attrs, 'class') == 'filmo':
            self._in_episodes = 1

    def end_div(self):
        if self._in_episodes: self._in_episodes = 0

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
                eps_data['kind'] = u'episode'
                e = Movie(movieID=str(self._episode_id), data=eps_data,
                            accessSystem=self._as, modFunct=self._modFunct)
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
                        role = u''
                        role = minfo[rolei+3:].strip()
                        notei = role.rfind('(')
                        note = u''
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

    def start_span(self, attrs):
        self._in_span = 1

    def end_span(self):
        self._in_span = 0

    def start_a(self, attrs):
        if not self._in_episodes: return
        if self._in_ol:
            if not self._in_li: return
            href = self.get_attr_value(attrs, 'href')
            if not href: return
            if 'character/ch' in href: return
            mid = self.re_imdbID.findall(href)
            if not mid: return
            self._in_episode_title = 1
            self._episode_id = mid[0]
            return
        elif self._in_span:
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
                            accessSystem=self._as, modFunct=self._modFunct)
                self._cur_series = s

    def _handle_data(self, data):
        if self._in_episode_title:
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


class HTMLPersonGenresParser(ParserBase):
    """Parser for the "by genre" and "by keywords" pages of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = HTMLPersonGenresParser()
        result = gparser.parse(bygenre_html_string)
    """
    kind = 'genres'

    def _reset(self):
        """Reset the parser."""
        self._info = {}
        self._cur_key = ''
        self._cur_title = u''
        self._in_table = False
        self._in_li = False
        self._cur_movieID = None
        self._cur_characterID = None

    def get_data(self):
        """Return the dictionary."""
        if not self._info: return {}
        return {self.kind: self._info}

    def start_table(self, attrs):
        if not self._in_content: return
        self._in_table = True

    def end_table(self):
        self._in_table = False

    def start_a(self, attrs):
        if not self._in_content: return
        if self._in_li:
            href = self.get_attr_value(attrs, 'href')
            if href:
                imdbID = self.re_imdbID.findall(href)
                if imdbID:
                    if 'title/tt' in href:
                        self._cur_movieID = imdbID[-1]
                    elif 'character/ch' in href:
                        self._cur_characterID = imdbID[-1]
                    return
        if not self._in_table: return
        name = self.get_attr_value(attrs, 'name')
        if name:
            self._cur_key = name

    def end_a(self): pass

    def start_li(self, attrs):
        if not (self._in_content and self._cur_key): return
        self._in_li = True

    def end_li(self):
        self._in_li = False
        self._add_info()

    def do_br(self, attrs):
        if not self._in_li: return
        self._in_li = False
        self._add_info()

    def _add_info(self):
        self._cur_key = self._cur_key.strip()
        self._cur_title = self._cur_title.strip()
        if not (self._cur_key and self._cur_title and self._cur_movieID):
            self._cur_title = u''
            self._cur_movieID = None
            self._cur_characterID = None
            return
        ridx = self._cur_title.find('[')
        notes = u''
        if ridx != -1:
            notes = self._cur_title[ridx:].lstrip()
            self._cur_title = self._cur_title[:ridx].rstrip()
        m = build_movie(self._cur_title, movieID=self._cur_movieID,
                        roleID=self._cur_characterID, modFunct=self._modFunct,
                        accessSystem=self._as)
        m.notes = notes
        self._info.setdefault(self._cur_key.replace('X2D', '-'), []).append(m)
        self._cur_title = u''
        self._cur_movieID = None
        self._cur_characterID = None

    def _handle_data(self, data):
        if not self._in_li: return
        self._cur_title += data


from movieParser import HTMLOfficialsitesParser
from movieParser import HTMLAwardsParser
from movieParser import HTMLTechParser
from movieParser import HTMLNewsParser
from movieParser import HTMLLocationsParser
from movieParser import HTMLSalesParser

_OBJECTS = {
    'maindetails_parser': (HTMLMaindetailsParser, None),
    'bio_parser': (HTMLBioParser, None),
    'otherworks_parser': (HTMLOtherWorksParser, None),
    'agent_parser': (HTMLOtherWorksParser, {'kind': 'agent'}),
    'person_officialsites_parser': (HTMLOfficialsitesParser, None),
    'person_awards_parser': (HTMLAwardsParser, {'subject': 'name'}),
    'publicity_parser': (HTMLTechParser, {'kind': 'publicity'}),
    'person_series_parser': (HTMLSeriesParser, None),
    'person_contacts_parser': (HTMLTechParser, {'kind': 'contacts'}),
    'person_genres_parser': (HTMLPersonGenresParser, None),
    'person_keywords_parser': (HTMLPersonGenresParser, {'kind': 'keywords'}),
    'news_parser':  (HTMLNewsParser, None),
    'sales_parser':  (HTMLSalesParser, None)
}

