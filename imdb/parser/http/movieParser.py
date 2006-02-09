"""
parser.http.movieParser module (imdb package).

This module provides the classes (and the instances), used to parse the
IMDb pages on the akas.imdb.com server about a movie.
E.g., for Brian De Palma's "The Untouchables", the referred
pages would be:
    combined details:   http://akas.imdb.com/title/tt0094226/combined
    plot summary:       http://akas.imdb.com/title/tt0094226/plotsummary
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

from urllib import unquote

from imdb.Person import Person
from imdb.Movie import Movie
from imdb.utils import analyze_title, re_episodes
from imdb._exceptions import IMDbParserError
from utils import ParserBase


_stypes = (type(u''), type(''))


def strip_amps(theString):
    """Remove '&\S*' AT the end of a string.
    It's used to remove '& ' from strings like '(written by) & '.
    """
    i = theString.rfind('&')
    if i != -1:
        if not theString[i+1:] or theString[i+1:].isspace():
            # There's nothing except spaces after the '&'.
            theString = theString[:i].rstrip()
    return theString


def clear_text(theString):
    """Remove separators and spaces in excess."""
    # Squeeze multiple spaces into one.
    theString = ' '.join(theString.split())
    # Remove spaces around the '::' separator.
    theString = theString.replace(':: ', '::').replace(' ::', '::')
    # Remove exceeding '::' separators.  I love list comprehension! <g>
    theString = '::'.join([piece for piece in theString.split('::') if piece])
    return theString


class HTMLMovieParser(ParserBase):
    """Parser for the "combined details" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        mparser = HTMLMovieParser()
        result = mparser.parse(combined_details_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _init(self):
        self._movie_data = {}
        # If true, we're parsing the "maindetails" page; if false,
        # the "combined" page is expected.
        self.mdparse = 0

    def _reset(self):
        self._movie_data.clear()
        # XXX: this is quite a mess; the boolean variables below are
        #      used to identify what section of the HTML we're parsing,
        #      and the string variables are used to store temporary values.
        # The name of the section we're parsing.
        self._current_section = ''
        # We're in a cast/crew section.
        self._is_cast_crew = 0
        # We're managing the name of a person.
        self._is_name = 0
        # The name and his role, (temporary) sperated by '::'.
        self._name = u''
        self._cur_nameID = ''
        # We're in a company credit section.
        self._is_company_cred = 0
        # The name of the company.
        self._company_data = ''
        self._countries = 0
        self._is_genres = 0
        self._is_title = 0
        self._title = u''
        self._title_short = u'' # used to retrieve the cover URL.
        self._is_rating = 0
        self._rating = ''
        self._is_languages = 0
        self._is_akas = 0
        self._aka_title = u''
        self._is_movie_status = 0
        self._movie_status_sect = ''
        self._movie_status = ''
        self._is_runtimes = 0
        self._runtimes = ''
        self._is_mpaa = 0
        self._mpaa = ''
        self._inbch = 0
        self._isplotoutline = 0
        self._plotoutline = u''
        # If true, the next data should be merged with the previous one,
        # without the '::' separator.
        self._merge_next = 0
        # Counter for the billing position in credits.
        self._counter = 1

    def append_item(self, sect, data):
        """Append a new value in the given section of the dictionary."""
        # Do some cleaning work on the strings.
        sect = clear_text(sect)
        data = clear_text(data)
        self._movie_data.setdefault(sect, []).append(data)

    def set_item(self, sect, data):
        """Put a single value (a string, normally) in the dictionary."""
        if type(data) in _stypes:
            data = clear_text(data)
        self._movie_data[clear_text(sect)] = data

    def get_data(self):
        """Return the dictionary."""
        return self._movie_data

    def start_title(self, attrs):
        self._is_title = 1

    def end_title(self):
        if self._title:
            self._is_title = 0
            d_title = analyze_title(self._title)
            for key, item in d_title.items():
                self.set_item(key, item)
            self._title_short = d_title.get('title', u'').lower()

    def start_table(self, attrs): pass

    def end_table(self):
        self._is_cast_crew = 0
        self._is_company_cred = 0
        self._current_section = ''
        self._is_movie_status = 0
        self._is_runtimes = 0
        self._runtimes = ''

    def start_a(self, attrs):
        # XXX: the current section ('director', 'cast', 'production company',
        #      etc.) name is taken from two different sources: for sections
        #      that contains actors/crew member names, the section name in
        #      the HTML is in the form
        #      <a href="/Glossary/S#SectName/">Description</a>, so we use
        #      the lowecase "sectname" as the name of the current section.
        #      For sections with company credits, the HTML is in the form
        #      <a href="/List?SectName=...">CompanyName</a> so we cut the
        #      href attribute of the <a> tag to get the "sectname".
        #      Underscores and minus signs in section names are replaced
        #      with spaces.
        link = self.get_attr_value(attrs, 'href')
        if not link: return
        olink = link
        link = link.lower()
        if link.startswith('/name'):
            # The following data will be someone's name.
            self._is_name = 1
            ids = self.re_imdbID.findall(link)
            if ids:
                self._cur_nameID = ids[-1]
        elif link.startswith('/list'):
            self._is_company_cred = 1
            # Sections like 'company credits' all begin
            # with a link to "/List" page.
            sect = link[6:].replace('_', ' ').replace('-', ' ')
            # The section name ends at the first '='.
            ind = sect.find('=')
            if ind != -1:
                sect = sect[:ind]
            self._current_section = sect
        # Sections like 'cast', 'director', 'writer', etc. all
        # begin with a link to a "/Glossary" page.
        elif link.startswith('/glossary'):
            self._is_cast_crew = 1
            # Get the section name from the link.
            link = link[12:].replace('_', ' ').replace('-', ' ')
            self._current_section = link
        elif link.startswith('/sections/countries'):
            self._countries = 1
        elif link.startswith('/sections/genres'):
            self._is_genres = 1
        elif link.startswith('/sections/languages'):
            self._is_languages = 1
        elif link.startswith('/mpaa'):
            self._is_mpaa = 1
        elif self._isplotoutline:
            self._isplotoutline = 0
            if self._plotoutline:
                self.set_item('plot outline', self._plotoutline)
        elif link.startswith('http://pro.imdb.com'):
            self._is_movie_status = 0
        elif link.startswith('/titlebrowse?') and \
                    not self._movie_data.has_key('title'):
            try:
                d_title = analyze_title(unquote(olink[13:]))
                for key, item in d_title.items():
                    self.set_item(key, item)
                self._title_short = d_title.get('title', u'').lower()
            except IMDbParserError:
                pass

    def end_a(self): pass

    def start_tr(self, attrs): pass

    def end_tr(self):
        if self._is_name and self._current_section:
            # Every cast/crew information are separated by <tr> tags.
            if self._is_cast_crew:
                # Remember to Strip final '&' (and spaces),
                # to get rid of things like the "& " in "(novel) & ".
                n_split = self._name.split('::')
                n = n_split[0].strip()
                del n_split[0]
                role = ' '.join(n_split).strip()
                notes = u''
                ii = role.find('(')
                if ii != -1:
                    ei = role.rfind(')')
                    if ei != -1:
                        notes = strip_amps(role[ii:ei+1].strip())
                        role = strip_amps('%s%s' % (role[:ii], role[ei+1:]))
                        role = role.replace('  ', ' ').strip()
                sect = clear_text(self._current_section)
                if sect != 'cast':
                    if notes: notes = ' %s' % notes
                    notes = strip_amps(role + notes).strip()
                    role = u''
                if sect == 'crewmembers': sect = 'miscellaneous crew'
                # Create a Person object.
                # XXX: check for self._cur_nameID?
                #      maybe it's not a good idea; is it possible for
                #      a person to be listed without a link?
                p = Person(name=strip_amps(n), currentRole=role,
                        personID=str(self._cur_nameID), accessSystem='http')
                if notes: p.notes = notes
                if self._movie_data.setdefault(sect, []) == []:
                    self._counter = 1
                p.billingPos = self._counter
                self._movie_data[sect].append(p)
                self._counter += 1
            self._name = u''
            self._cur_nameID = ''
        self._movie_status_data = ''
        self._movie_status_sect = ''
        self._is_name = 0

    def start_td(self, attrs): pass

    def end_td(self):
        if self._is_movie_status:
            if self._movie_status_sect and self._movie_status_data:
                sect_name = self._movie_status_sect
                if not sect_name.startswith('status'):
                    sect_name = 'status %s' % sect_name
                self.set_item(sect_name, self._movie_status_data)
        elif self._is_cast_crew and self._current_section:
            if self._is_name:
                self._name += '::'
    
    def do_br(self, attrs):
        if self._is_company_cred:
            # Sometimes companies are separated by <br> tags.
            self._company_data = strip_amps(self._company_data)
            self.append_item(self._current_section, self._company_data)
            self._company_data = ''
            self._is_company_cred = 0
        elif self._is_akas and self._aka_title:
            # XXX: when managing an 'aka title', some transformation
            #      are required; a complete aka title is in the form
            #      of "Aka Title (year) (country1) (country2) [cc]"
            #      The movie's year of release; the "Aka Title", the
            #      countries list and the country code (cc) will be
            #      separated by '::'.
            #      In the example: "Aka Title::(country1) (country2)::[cc]"
            aka = self._aka_title
            year = None
            title = self._movie_data.get('title')
            if title:
                year = self._movie_data.get('year')
            if year:
                syear = ' (%s) ' % year
                if aka.find(syear) != -1:
                    aka = aka.replace(syear, '(%s)::' % year)
                else:
                    fsti = aka.find(' (')
                    if fsti != -1:
                        aka = aka[:fsti] + '::' + aka[fsti+1:]
                    aka = aka.replace(')', ')::')
            ind = aka.rfind(' [')
            if ind != -1:
                aka = aka[:ind] + '::' + aka[ind+1:]
            aka = aka.replace('][', '] [')
            aka = aka.replace(')(', ') (')
            self.append_item('akas', aka)
            self._aka_title = ''
        elif self._is_mpaa and self._mpaa:
            self._is_mpaa = 0
            mpaa = self._mpaa.replace('MPAA:', '')
            self.set_item('mpaa', mpaa)
        elif self._isplotoutline:
            self._isplotoutline = 0
            if self._plotoutline:
                self.set_item('plot outline', self._plotoutline)
        elif self._is_runtimes and self._runtimes:
            self._is_runtimes = 0
            rt = self._runtimes.replace(' min', '')
            # The "(xy episodes)" note.
            episodes = re_episodes.findall(rt)
            if episodes:
                rt = re_episodes.sub('', rt)
                self.set_item('episodes', episodes[0])
            rl = [x.strip() for x in rt.split('/')]
            if rl: self.set_item('runtimes', rl)
        if self.mdparse:
            self.end_tr()

    def start_li(self, attrs): pass

    def end_li(self):
        if self._is_company_cred:
            # Sometimes companies are listed inside an <ul> tag.
            self._company_data = strip_amps(self._company_data)
            self.append_item(self._current_section, self._company_data)
            self._company_data = ''
            self._is_company_cred = 0

    def start_ul(self, attrs): pass

    def end_ul(self):
        self._is_company_cred = 0

    def start_b(self, attrs):
        self._is_akas = 0
        cls = self.get_attr_value(attrs, 'class')
        if cls:
            cls = cls.lower()
            if cls == 'ch':
                self._inbch = 1
            elif self.mdparse and cls == 'blackcatheader':
                self.end_table()

    def end_b(self):
        if self._inbch: self._inbch = 0

    def do_img(self, attrs):
        alttex = self.get_attr_value(attrs, 'alt')
        if not alttex: return
        alttex = alttex.strip().lower()
        if alttex in ('*', '_'):
            # The gold and grey stars; we're near the rating and number
            # of votes.
            self._is_rating = 1
        # XXX: I've a report about alttex==self._movie_data.get('title')
        #      in some situations, but I'm not sure.
        elif alttex == 'cover' or alttex == self._title_short:
            # Get the URL of the cover image.
            src = self.get_attr_value(attrs, 'src')
            if src: self.set_item('cover url', src)
        elif alttex == 'vote here':
            # Parse the rating and the number of votes.
            self._is_rating = 0
            rav = self._rating.strip()
            if rav:
                i = rav.find('/10')
                if i != -1:
                    rating = rav[:i]
                    try:
                        rating = float(rating)
                        self.set_item('rating', rating)
                    except ValueError:
                        pass
                i = rav.find('(')
                if i != -1:
                    votes = rav[i+1:]
                    j = votes.find(' ')
                    votes = votes[:j].replace(',', '')
                    try:
                        votes = int(votes)
                        self.set_item('votes', votes)
                    except ValueError:
                        pass

    def _handle_data(self, data):
        # Manage the plain text part of an HTML document.
        sdata = data.strip()
        sldata = sdata.lower()
        if self._is_cast_crew and self._current_section and self._is_name:
            # Modify the separator for "name .... role"
            data = data.replace(' .... ', '::')
            # Separate the last (...) string; it's here to handle strings
            # like 'screenplay' in "name (screenplay)" in the writing credits.
            if sdata and sdata[0] == '(':
                data = data.lstrip()
                self._name = self._name.strip() + '::'
            self._name += data
        elif self._is_company_cred and self._current_section:
            # Sometimes company credits are separated by a slash;
            # 'certification' is an example.
            if sdata == '/':
                cd = self._company_data
                cd = strip_amps(cd)
                self.append_item(self._current_section, cd)
                self._company_data = ''
                self._is_company_cred = 0
            else:
                # Merge the next data without a separator.
                if self._merge_next:
                    self._company_data += data
                    self._merge_next = 0
                else:
                    if self._company_data:
                        if len(data) > 1:
                            self._company_data += '::'
                        elif data != ' ':
                            self._merge_next = 1
                    self._company_data += data
        elif self._is_akas and sdata != ':':
            self._aka_title += data
        elif self._is_runtimes:
            self._runtimes += data
        elif self._is_mpaa:
            self._mpaa += data
        elif self._is_movie_status:
            if not self._movie_status_sect:
                self._movie_status_sect = sldata.replace(':', '')
            else:
                self._movie_status_data += data.lower()
        elif self._countries:
            self.append_item('countries', data)
            self._countries = 0
        elif self._is_title:
            # Store the title and the year, as taken from the <title> tag.
            self._title += data
        elif self._is_genres:
            self.append_item('genres', data)
            self._is_genres = 0
        elif self._is_rating:
            self._rating += data
        elif self._is_languages:
            self.append_item('languages', data)
            self._is_languages = 0
        elif self._isplotoutline:
            self._plotoutline += data
        elif self._inbch and sldata.startswith('plot outline:'):
            self._isplotoutline = 1
        elif sldata.startswith('also known as'):
            self._is_akas = 1
        elif sldata.startswith('runtime:'):
            self._is_runtimes = 1
        elif sldata.startswith('production notes/status'):
            self._is_movie_status = 1
        # XXX: the following branches are here to manage the "maindetails"
        #      page of a movie, instead of the "combined" page.
        if self.mdparse:
            if sldata.startswith('cast overview, first billed only'):
                self._is_cast_crew = 1
                self._current_section = 'cast'
            elif sldata.startswith('directed by'):
                self._is_cast_crew = 1
                self._current_section = 'director'
            elif sldata.startswith('writing credits'):
                self._is_cast_crew = 1
                self._current_section = 'writer'


class HTMLPlotParser(ParserBase):
    """Parser for the "plot summary" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a 'plot' key, containing a list
    of string with the structure: 'summary_author <author@email>::summary'.
    
    Example:
        pparser = HTMLPlotParser()
        result = pparser.parse(plot_summary_html_string)
    """
    def _init(self):
        self._plot_data = {}

    def _reset(self):
        """Reset the parser."""
        self._plot_data.clear()
        self._is_plot = 0
        self._plot = u''
        self._last_plot = u''
        self._is_plot_writer = 0
        self._plot_writer = u''

    def get_data(self):
        """Return the dictionary with the 'plot' key."""
        return self._plot_data

    def start_p(self, attrs):
        pclass = self.get_attr_value(attrs, 'class')
        if pclass and pclass.lower() == 'plotpar':
            self._is_plot = 1

    def end_p(self):
        if self._is_plot:
            # Store the plot in the self._last_plot variable until
            # the parser will read the name of the author.
            self._last_plot = self._plot
            self._is_plot = 0
            self._plot = u''

    def start_a(self, attrs):
        link = self.get_attr_value(attrs, 'href')
        # The next data is the name of the author.
        if link and link.lower().startswith('/searchplotwriters'):
            self._is_plot_writer = 1

    def end_a(self):
        # We've read the name of an author and the summary he wrote;
        # store everything in _plot_data.
        if self._is_plot_writer and self._last_plot:
            writer = self._plot_writer.strip()
            # Replace funny email separators.
            writer = writer.replace('{', '<').replace('}', '>')
            plot = self._last_plot.strip()
            self._plot_data.setdefault('plot', []).append('%s::%s' %
                                                            (writer, plot))
            self._is_plot_writer = 0
            self._plot_writer = u''
            self._last_plot = u''
            
    def _handle_data(self, data):
        # Store text for plots and authors.
        if self._is_plot:
            self._plot += data
        if self._is_plot_writer:
            self._plot_writer += data


class HTMLAwardsParser(ParserBase):
    """Parser for the "awards" page of a given person or movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        awparser = HTMLAwardsParser()
        result = awparser.parse(awards_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _init(self):
        self._aw_data = []
        # We're managing awards for a person or a movie?
        self.subject = 'title'
    
    def _reset(self):
        """Reset the parser."""
        self._aw_data = []
        self._is_big = 0
        self._is_current_assigner = 0
        self._begin_aw = 0
        self._in_td = 0
        self._cur_year = ''
        self._cur_result = ''
        self._cur_notes = ''
        self._cur_category = ''
        self._cur_forto = u''
        self._cur_assigner = u''
        self._cur_award = u''
        self._cur_sect = ''
        self._no = 0
        self._rowspan = 0
        self._counter = 1
        self._limit = 1
        self._is_tn = 0
        self._cur_id = ''
        self._t_o_n = u''
        self._to = []
        self._for = []
        self._with = []
        self._begin_to_for = 0
        self._cur_role = u''
        self._cur_tn = u''
        # XXX: a Person or Movie object is instantiated only once (i.e.:
        #      every reference to a given movie/person is the _same_
        #      object).
        self._person_obj_list = []
        self._movie_obj_list = []

    def get_data(self):
        """Return the dictionary."""
        if not self._aw_data: return {}
        return {'awards': self._aw_data}

    def start_big(self, attrs):
        self._is_big = 1

    def end_big(self):
        self._is_big = 0

    def start_td(self, attrs):
        self._in_td = 1
        if not self._begin_aw: return
        rowspan = self.get_attr_value(attrs, 'rowspan') or '1'
        try: rowspan = int(rowspan)
        except (ValueError, OverflowError):
            rowspan = 1
        self._rowspan = rowspan
        colspan = self.get_attr_value(attrs, 'colspan') or '1'
        try: colspan = int(colspan)
        except (ValueError, OverflowError):
            colspan = 1
        if colspan == 4:
            self._no = 1

    def end_td(self):
        if self._no or not self._begin_aw: return
        if self._cur_sect == 'year':
            self._cur_sect = 'res'
        elif self._cur_sect == 'res':
            self._limit = self._rowspan
            self._counter = 1
            self._cur_sect = 'award'
        elif self._cur_sect == 'award':
            self._cur_sect = 'cat'
        elif self._cur_sect == 'cat':
           self._counter += 1
           self.store_data()
           self._begin_to_for = 0
           # XXX: if present, the next "Category/Recipient(s)"
           #      has a different "Result", so go back and read it.
           if self._counter == self._limit+1:
                self._cur_result = ''
                self._cur_award = u''
                self._cur_sect = 'res'
                self._counter = 1

    def store_data(self):
        year = self._cur_year.strip()
        res = self._cur_result.strip()
        aw = self._cur_award.strip()
        notes = self._cur_notes.strip()
        assign = self._cur_assigner.strip()
        cat = self._cur_category.strip()
        d = {'year': year, 'result': res, 'award': aw, 'notes': notes,
            'assigner': assign, 'category': cat, 'for': self._for,
            'to': self._to, 'with': self._with}
        # Remove empty keys.
        for key in d.keys():
            if not d[key]: del d[key]
        self._aw_data.append(d)
        self._cur_notes = u''
        self._cur_category = ''
        self._cur_forto = u''
        self._with = []
        self._to = []
        self._for = []
        self._cur_role = u''
        
    def start_th(self, attrs):
        self._begin_aw = 0

    def end_th(self): pass

    def start_table(self, attrs): pass

    def end_table(self):
        self._begin_aw = 0
        self._in_td = 0

    def start_small(self, attrs):
        self._is_small = 1

    def end_small(self):
        self._is_small = 0

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        if href.startswith('/Sections/Awards'):
            if self._in_td:
                try: year = str(int(href[-4:]))
                except (ValueError, TypeError): year = None
                if year:
                    self._cur_sect = 'year'
                    self._cur_year = year
                    self._begin_aw = 1
                    self._counter = 1
                    self._limit = 1
                    self._no = 0
                    self._cur_result = ''
                    self._cur_notes = u''
                    self._cur_category = ''
                    self._cur_forto = u''
                    self._cur_award = ''
                    self._with = []
                    self._to = []
                    self._for = []
            if self._is_big:
                self._is_current_assigner = 1
                self._cur_assigner = ''
        elif href.startswith('/name') or href.startswith('/title'):
            if self._is_small: return
            tn = self.re_imdbID.findall(href)
            if tn:
                self._cur_id = tn[-1]
                self._is_tn = 1
                self._cur_tn = u''
                if href.startswith('/name'): self._t_o_n = 'n'
                else: self._t_o_n = 't'

    def end_a(self):
        if self._is_current_assigner:
            self._is_current_assigner = 0
        if self._is_tn and self._cur_sect == 'cat':
            self._cur_tn = self._cur_tn.strip()
            self._cur_role = self._cur_role.strip()
            if self.subject == 'name':
                if self._t_o_n == 't':
                    self._begin_to_for = 1
                    m = Movie(title=self._cur_tn,
                                movieID=str(self._cur_id),
                                accessSystem='http')
                    if m in self._movie_obj_list:
                        ind = self._movie_obj_list.index(m)
                        m = self._movie_obj_list[ind]
                    else:
                        self._movie_obj_list.append(m)
                    self._for.append(m)
                else:
                    p = Person(name=self._cur_tn,
                                personID=str(self._cur_id),
                                currentRole=self._cur_role,
                                accessSystem='http')
                    if p in self._person_obj_list:
                        ind = self._person_obj_list.index(p)
                        p = self._person_obj_list[ind]
                    else:
                        self._person_obj_list.append(p)
                    self._with.append(p)
            else:
                if self._t_o_n == 't':
                    m = Movie(title=self._cur_tn,
                                movieID=str(self._cur_id),
                                accessSystem='http')
                    if m in self._movie_obj_list:
                        ind = self._movie_obj_list.index(m)
                        m = self._movie_obj_list[ind]
                    else:
                        self._movie_obj_list.append(m)
                    self._with.append(m)
                else:
                    self._begin_to_for = 1
                    p = Person(name=self._cur_tn,
                                personID=str(self._cur_id),
                                currentRole=self._cur_role,
                                accessSystem='http')
                    if p in self._person_obj_list:
                        ind = self._person_obj_list.index(p)
                        p = self._person_obj_list[ind]
                    else:
                        self._person_obj_list.append(p)
                    self._to.append(p)
            self._cur_role = u''
        self._is_tn = 0

    def _handle_data(self, data):
        if self._is_current_assigner:
            self._cur_assigner += data
        if not self._begin_aw or not data or data.isspace() or self._no:
            return
        sdata = data.strip()
        sldata = sdata.lower()
        if self._cur_sect == 'res':
            self._cur_result += data
        elif self._cur_sect == 'award':
            self._cur_award += data
        elif self._cur_sect == 'cat':
            if self._is_tn:
                self._cur_tn += data
            elif sldata not in ('for:', 'shared with:'):
                if self._is_small:
                    self._cur_notes += data
                elif self._begin_to_for:
                    self._cur_role += data
                else:
                    self._cur_category += data


class HTMLTaglinesParser(ParserBase):
    """Parser for the "taglines" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = HTMLTaglinesParser()
        result = tparser.parse(taglines_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._in_tl = 0
        self._in_tlu = 0
        self._in_tlu2 = 0
        self._tl = []
        self._ctl = ''

    def get_data(self):
        """Return the dictionary."""
        if not self._tl: return {}
        return {'taglines': self._tl}

    def start_td(self, attrs):
        # XXX: not good!
        self._in_tlu = 1

    def end_td(self):
        self._in_tl = 0
        self._in_tlu = 0
        self._in_tlu2 = 0

    def start_h1(self, attrs): pass

    def end_h1(self):
        if self._in_tlu2:
            self._in_tl = 1

    def start_p(self, attrs): pass
    
    def end_p(self):
        if self._in_tl and self._ctl:
            self._tl.append(self._ctl.strip())
            self._ctl = ''

    def _handle_data(self, data):
        if self._in_tl:
            self._ctl += data
        elif self._in_tlu and data.lower().find('taglines for') != -1:
            self._in_tlu2 = 1


class HTMLKeywordsParser(ParserBase):
    """Parser for the "keywords" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        kwparser = HTMLKeywordsParser()
        result = kwparser.parse(keywords_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._in_kw = 0
        self._kw = []
        self._ckw = ''

    def get_data(self):
        """Return the dictionary."""
        if not self._kw: return {}
        return {'keywords': self._kw}

    def start_b(self, attrs):
        if self.get_attr_value(attrs, 'class') == 'keyword':
            self._in_kw = 1

    def end_b(self):
        if self._in_kw:
            self._kw.append(self._ckw.strip())
            self._ckw = ''
            self._in_kw = 0

    def start_a(self, attrs):
        if not self._in_kw: return
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        kwi = href.find('keyword/')
        if kwi == -1: return
        kw = href[kwi+8:].strip()
        if not kw: return
        if kw[-1] == '/': kw = kw[:-1].strip()
        if kw: self._ckw = kw

    def end_a(self): pass


class HTMLAlternateVersionsParser(ParserBase):
    """Parser for the "alternate versions" and "trivia" pages of a
    given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        avparser = HTMLAlternateVersionsParser()
        result = avparser.parse(alternateversions_html_string)
    """
    def _init(self):
        self.kind = 'alternate versions'

    def _reset(self):
        """Reset the parser."""
        self._in_av = 0
        self._in_avd = 0
        self._av = []
        self._cav = ''
        self._stlist = []
        self._curst = {}
        self._cur_title = ''
        self._curinfo = ''

    def get_data(self):
        """Return the dictionary."""
        if self.kind == 'soundtrack':
            if self._stlist:
                return {self.kind: self._stlist}
            else:
                return {}
        if not self._av: return {}
        return {self.kind: self._av}

    def start_ul(self, attrs):
        if self.get_attr_value(attrs, 'class') == 'trivia':
            self._in_av = 1

    def end_ul(self):
        self._in_av = 0
        
    def start_li(self, attrs):
        if self._in_av:
            self._in_avd = 1

    def end_li(self):
        if self._in_av and self._in_avd:
            if self.kind == 'soundtrack':
                self._stlist.append(self._curst.copy())
                self._curst.clear()
                self._cur_title = ''
                self._curinfo = ''
            else:
                self._av.append(self._cav.strip())
            self._in_avd = 0
            self._cav = ''

    def do_br(self, attrs):
        if self._in_avd and self.kind == 'soundtrack':
            if not self._cur_title:
                self._cav = self._cav.strip()
                if self._cav and self._cav[-1] == '"':
                    self._cav = self._cav[:-1]
                if self._cav and self._cav[0] == '"':
                    self._cav = self._cav[1:]
                self._cur_title = self._cav
                self._curst[self._cur_title] = {}
                self._cav = ''
            else:
                lcw = self._cav.lower()
                for i in ('with', 'by', 'from', 'of'):
                    posi = lcw.find(i)
                    if posi != -1:
                        self._curinfo = self._cav[:posi+len(i)]
                        if self.kind == 'soundtrack':
                            self._curinfo = self._curinfo.lower().strip()
                        rest = self._cav[posi+len(i)+1:]
                        self._curst[self._cur_title][self._curinfo] = \
                                rest
                        break
                else:
                    if not lcw.strip(): return
                    if not self._curst[self._cur_title].has_key('misc'):
                        self._curst[self._cur_title]['misc'] = ''
                    if self._curst[self._cur_title]['misc'] and \
                            self._curst[self._cur_title]['misc'][-1] != ' ':
                        self._curst[self._cur_title]['misc'] += ' '
                    self._curst[self._cur_title]['misc'] += self._cav
                self._cav = ''

    def _handle_data(self, data):
        if self._in_avd:
            self._cav += data


class HTMLCrazyCreditsParser(ParserBase):
    """Parser for the "crazy credits" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        ccparser = HTMLCrazyCreditsParser()
        result = ccparser.parse(crazycredits_html_string)
    """

    def _reset(self):
        """Reset the parser."""
        self._in_cc = 0
        self._in_cc2 = 0
        self._cc = []
        self._ccc = ''
        self._nrbr = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._cc: return {}
        return {'crazy credits': self._cc}

    def start_td(self, attrs):
        # XXX: not good!
        self._in_cc = 1

    def end_td(self):
        self._in_cc = 0

    def start_pre(self, attrs):
        if self._in_cc:
            self._in_cc2 = 1
    
    def end_pre(self):
        if self._in_cc2:
            self.app()
            self._in_cc2 = 0

    def do_br(self, attrs):
        if not self._in_cc2: return
        self._nrbr += 1
        if self._nrbr == 2:
            self.app()

    def app(self):
        self._ccc = self._ccc.strip()
        if self._in_cc2 and self._ccc:
            self._cc.append(self._ccc.replace('\n', ' '))
            self._ccc = ''
            self._nrbr = 0
    
    def _handle_data(self, data):
        if self._in_cc2:
            self._ccc += data


class HTMLGoofsParser(ParserBase):
    """Parser for the "goofs" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = HTMLGoofsParser()
        result = gparser.parse(goofs_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._in_go = 0
        self._in_go2 = 0
        self._go = []
        self._cgo = ''
        self._in_gok = 0
        self._cgok = ''

    def get_data(self):
        """Return the dictionary."""
        if not self._go: return {}
        return {'goofs': self._go}

    def start_ul(self, attrs):
        if self.get_attr_value(attrs, 'class') == 'trivia':
            self._in_go = 1

    def end_ul(self):
        self._in_go = 0
        
    def start_b(self, attrs):
        if self._in_go2:
            self._in_gok = 1

    def end_b(self):
        self._in_gok = 0
            
    def start_li(self, attrs):
        if self._in_go:
            self._in_go2 = 1

    def end_li(self):
        if self._in_go and self._in_go2:
            self._in_go2 = 0
            self._go.append('%s:%s' % (self._cgok.strip().lower(),
                                        self._cgo.strip()))
            self._cgo = ''
            self._cgok = ''

    def _handle_data(self, data):
        if self._in_gok:
            self._cgok += data
        elif self._in_go2:
            self._cgo += data


class HTMLQuotesParser(ParserBase):
    """Parser for the "memorable quotes" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        qparser = HTMLQuotesParser()
        result = qparser.parse(quotes_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._in_quo = 0
        self._in_quo2 = 0
        self._quo = []
        self._cquo = ''

    def get_data(self):
        """Return the dictionary."""
        if not self._quo: return {}
        quo = []
        for q in self._quo:
            if q.endswith('::'): q = q[:-2]
            quo.append(q)
        return {'quotes': quo}

    def start_td(self, attrs):
        # XXX: not good!
        self._in_quo = 1

    def end_td(self):
        self._in_quo = 0
        self._in_quo2 = 0

    def start_a(self, attrs):
        name = self.get_attr_value(attrs, 'name')
        if name and name.startswith('qt'):
            self._in_quo2 = 1
    
    def end_a(self): pass

    def do_hr(self, attrs):
        if self._in_quo and self._in_quo2 and self._cquo:
            self._cquo = self._cquo.strip()
            if self._cquo.endswith('::'):
                self._cquo = self._cquo[:-2]
            self._quo.append(self._cquo.strip())
            self._cquo = ''

    def do_p(self, attrs):
        if self._in_quo and self._in_quo2:
            self.do_hr([])
            self._in_quo = 0

    def do_br(self, attrs):
        if self._in_quo and self._in_quo2 and self._cquo:
            self._cquo = '%s::' % self._cquo.strip()
    
    def _handle_data(self, data):
        if self._in_quo and self._in_quo2:
            data = data.replace('\n', ' ')
            if self._cquo.endswith('::'):
                data = data.lstrip()
            self._cquo += data


class HTMLReleaseinfoParser(ParserBase):
    """Parser for the "release dates" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rdparser = HTMLReleaseinfoParser()
        result = rdparser.parse(releaseinfo_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._in_rl = 0
        self._in_rl2 = 0
        self._rl = []
        self._crl = ''
        self._is_country = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._rl: return {}
        return {'release dates': self._rl}

    def start_th(self, attrs):
        if self.get_attr_value(attrs, 'class') == 'xxxx':
            self._in_rl = 1

    def end_th(self): pass
        
    def start_a(self, attrs):
        if self._in_rl:
            href = self.get_attr_value(attrs, 'href')
            if href and href.startswith('/Recent'):
                self._in_rl2 = 1
                self._is_country = 1

    def end_a(self):
        if self._is_country:
            if self._crl:
                self._crl += '::'
            self._is_country = 0
     
    def start_tr(self, attrs): pass

    def end_tr(self):
        if self._in_rl2:
            self._in_rl2 = 0
            self._rl.append(self._crl)
            self._crl = ''

    def _handle_data(self, data):
        if self._in_rl2:
            if self._crl and self._crl[-1] not in (' ', ':') \
                    and not data.isspace():
                self._crl += ' '
            self._crl += data.strip()


class HTMLRatingsParser(ParserBase):
    """Parser for the "user ratings" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rparser = HTMLRatingsParser()
        result = rparser.parse(userratings_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._in_t = 0
        self._in_total = 0
        self._in_b = 0
        self._cur_nr = ''
        self._in_cur_vote = 0
        self._cur_vote = ''
        self._first = 0
        self._votes = {}
        self._rank = {}
        self._demo = {}
        self._in_p = 0
        self._in_demo = 0
        self._in_demo_t = 0
        self._cur_demo_t = ''
        self._cur_demo_av = ''
        self._next_is_demo_vote = 0
        self._next_demo_vote = ''
        self._in_td = 0

    def get_data(self):
        """Return the dictionary."""
        data = {}
        if self._votes:
            data['number of votes'] = self._votes
        if self._demo:
            data['demographic'] = self._demo
        data.update(self._rank)
        return data

    def start_table(self, attrs):
        self._in_t = 1

    def end_table(self):
        self._in_t = 0
        self._in_total = 0

    def start_b(self, attrs):
        self._in_b = 1

    def end_b(self):
        self._in_b = 0

    def start_td(self, attrs):
        self._in_td = 1

    def end_td(self):
        self._in_td = 0
        if self._in_total:
            if self._first:
                self._first = 0

    def start_tr(self, attrs):
        if self._in_total:
            self._first = 1

    def end_tr(self):
        if self._in_total:
            if self._cur_nr:
                try:
                    c = int(self._cur_vote)
                    n = int(self._cur_nr)
                    self._votes[c] = n
                except (ValueError, OverflowError): pass
                self._cur_nr = ''
                self._cur_vote = ''
        if self._in_demo:
            self._in_demo = 0
            try:
                av = float(self._cur_demo_av)
                dv = int(self._next_demo_vote)
                self._demo[self._cur_demo_t] = (dv, av)
            except (ValueError, OverflowError): pass
            self._cur_demo_av = ''
            self._next_demo_vote = ''
            self._cur_demo_t = ''

    def start_p(self, attrs):
        self._in_p = 1

    def end_p(self):
        self._in_p = 0
    
    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if href and href.startswith('ratings-'):
            self._in_demo = 1
            self._in_demo_t = 1

    def end_a(self):
        self._in_demo_t = 0
    
    def _handle_data(self, data):
        if self._in_b and data == 'Rating':
            self._in_total = 1
        sdata = data.strip()
        if not sdata: return
        if self._first:
            self._cur_nr = sdata
        else:
            self._cur_vote = sdata
        if self._in_p:
            if sdata.startswith('Ranked #'):
                sd = sdata[8:]
                i = sd.find(' ')
                if i != -1:
                    sd = sd[:i]
                    try: sd = int(sd)
                    except (ValueError, OverflowError): pass
                    if type(sd) is type(1):
                        self._rank['top 250 rank'] = sd
            elif sdata.startswith('Arithmetic mean = '):
                if sdata[-1] == '.': sdata = sdata[:-1]
                am = sdata[18:]
                try: am = float(am)
                except (ValueError, OverflowError): pass
                if type(am) is type(1.0):
                    self._rank['arithmetic mean'] = am
            elif sdata.startswith('Median = '):
                med = sdata[9:]
                try: med = int(med)
                except (ValueError, OverflowError): pass
                if type(med) is type(1):
                    self._rank['median'] = med
        if self._in_demo:
            if self._next_is_demo_vote:
                self._next_demo_vote = sdata
                self._next_is_demo_vote = 0
            elif self._in_demo_t:
                self._cur_demo_t = sdata.lower()
                self._next_is_demo_vote = 1
            else:
                self._cur_demo_av = sdata
        elif self._in_td and sdata.startswith('All votes'):
            self._in_demo = 1
            self._next_is_demo_vote = 1
            self._cur_demo_t = 'all votes'


class HTMLOfficialsitesParser(ParserBase):
    """Parser for the "official sites", "external reviews", "newsgroup
    reviews", "miscellaneous links", "sound clips", "video clips" and
    "photographs" pages of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        osparser = HTMLOfficialsitesParser()
        result = osparser.parse(officialsites_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _init(self):
        self.kind = 'official sites'
    
    def _reset(self):
        """Reset the parser."""
        self._in_os = 0
        self._in_os2 = 0
        self._in_os3 = 0
        self._os = []
        self._cos = ''
        self._cosl = ''

    def get_data(self):
        """Return the dictionary."""
        if not self._os: return {}
        return {self.kind: self._os}

    def start_td(self, attrs):
        # XXX: not good at all!
        self._in_os = 1

    def end_td(self):
        self._in_os = 0

    def start_ol(self, attrs):
        if self._in_os:
            self._in_os2 = 1
    
    def end_ol(self):
        if self._in_os2:
            self._in_os2 = 0

    def start_li(self, attrs):
        if self._in_os2:
            self._in_os3 = 1

    def end_li(self):
        if self._in_os3:
            self._in_os3 = 0
            if self._cosl and self._cos:
                self._os.append((self._cos.strip(), self._cosl.strip()))
            self._cosl = ''
            self._cos = ''

    def start_a(self, attrs):
        if self._in_os3:
            href = self.get_attr_value(attrs, 'href')
            if href:
                if not href.lower().startswith('http://'):
                    if href.startswith('/'): href = href[1:]
                    href = 'http://akas.imdb.com/%s' % href
                self._cosl = href
        
    def end_a(self): pass
    
    def _handle_data(self, data):
        if self._in_os3:
            self._cos += data


class HTMLConnectionParser(ParserBase):
    """Parser for the "connections" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        connparser = HTMLConnectionParser()
        result = connparser.parse(connections_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._in_cn = 0
        self._in_cnt = 0
        self._cn = {}
        self._cnt = ''
        self._cur_id = ''
        self._mtitle = ''

    def get_data(self):
        """Return the dictionary."""
        if not self._cn: return {}
        return {'connections': self._cn}

    def start_dt(self, attrs):
        self._in_cnt = 1
        self._cnt = ''

    def end_dt(self):
        self._in_cnt = 0

    def start_dd(self, attrs):
        self._in_cn = 1

    def end_dd(self):
        self._in_cn = 0
        self._cur_id = ''

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if not (self._in_cn and href and href.startswith('/title')): return
        tn = self.re_imdbID.findall(href)
        if tn:
            self._cur_id = tn[-1]
    
    def end_a(self): pass

    def do_br(self, attrs):
        sectit = self._cnt.strip()
        if self._in_cn and self._mtitle and self._cur_id and sectit:
            m = Movie(title=self._mtitle,
                        movieID=str(self._cur_id),
                        accessSystem='http')
            self._cn.setdefault(sectit, []).append(m)
            self._mtitle = ''
            self._cur_id = ''

    def _handle_data(self, data):
        if self._in_cn:
            self._mtitle += data
        elif self._in_cnt:
            self._cnt += data.lower()


class HTMLTechParser(ParserBase):
    """Parser for the "technical", "business", "literature",
    "publicity" (for people) and "locations" pages of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = HTMLTechParser()
        result = tparser.parse(technical_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _init(self):
        self.kind = 'something else'
    
    def _reset(self):
        """Reset the parser."""
        self._tc = {}
        self._dotc = 0
        self._indt = 0
        self._indd = 0
        self._cur_sect = ''
        self._curdata = ['']
    
    def get_data(self):
        """Return the dictionary."""
        if self.kind == 'locations':
            rl = []
            for item in self._tc.items():
                tmps = item[0].strip() + ' ' + \
                        ' '.join([x.strip() for x in item[1]])
                rl.append(tmps)
            if rl: return {'locations': rl}
        if self.kind in ('literature', 'business') and self._tc:
            return {self.kind: self._tc}
        return self._tc

    def start_dl(self, attrs):
        self._dotc = 1

    def end_dl(self):
        self._dotc = 0

    def start_dt(self, attrs):
        if self._dotc: self._indt = 1

    def end_dt(self):
        self._indt = 0

    def start_tr(self, attrs): pass

    def end_tr(self):
        if self._indd and self.kind == 'publicity':
            if self._curdata:
                self.do_br([])

    def start_td(self, attrs): pass

    def end_td(self):
        if self._indd and self._curdata and self.kind == 'publicity':
            if self._curdata[-1].find('::') == -1:
                self._curdata[-1] += '::'

    def start_p(self, attrs): pass

    def end_p(self):
        if self._indd and self.kind == 'publicity':
            if self._curdata:
                self._curdata[-1] += '::'
                self.do_br([])

    def start_dd(self, attrs):
        if self._dotc: self._indd = 1

    def end_dd(self):
        self._indd = 0
        self._curdata[:] = [x.strip() for x in self._curdata]
        self._curdata[:] = [x for x in self._curdata if x]
        for i in xrange(len(self._curdata)):
            if self._curdata[i][-2:] == '::':
                self._curdata[i] = self._curdata[i][:-2]
        if self._cur_sect and self._curdata:
            self._tc[self._cur_sect] = self._curdata[:]
        self._curdata[:] = ['']
        self._cur_sect = ''

    def do_br(self, attrs):
        if self._indd:
            self._curdata += ['']

    def _handle_data(self, data):
        if self._indd:
            self._curdata[-1] += data
        elif self._indt:
            if self.kind != 'locations': data = data.lower()
            self._cur_sect += data


class HTMLDvdParser(ParserBase):
    """Parser for the "dvd" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        dparser = HTMLDvdParser()
        result = dparser.parse(dvd_html_string)
    """
    # TODO: it's not still ready to handle the "laserdisc" page.
    kind = 'dvd'

    def _init(self):
        self._dvd = []

    def _reset(self):
        """Reset the parser."""
        self._cdvd = {}
        self._indvd = 0
        self._intitle = 0
        self._curtitle = ''
        self._binfo = 0
        self._binfo_txt = ''
        self._inth = 0
        self._noendb = 0
        self._finfo = 0
        self._finfo_txt = ''
        self._inar = 0
        self._thl = []
        self._thmult = 1
        self._colcount = -1
        self._coldata = ''
        self._insound = 0

    def get_data(self):
        """Return the dictionary."""
        if self._dvd: return {'dvd': self._dvd}
        return {}

    def _put_data(self, s):
        s = s.strip()
        if not s: return
        dcmi = s.find('::-')
        mini = s.find('min')
        if dcmi != -1 and mini != -1:
            self._put_data('color::%s' % s[:dcmi])
            self._put_data('runtime::%s' % s[dcmi+3:mini])
            return
        ss = [x.strip() for x in s.split('::') if x.strip()]
        ssl = len(ss)
        if ssl == 1:
            if ss[0].lower().find('read about how we rate dvds') != -1: return
            self._cdvd.setdefault('misc', []).append(ss[0])
        else:
            k = ss[0].lower()
            v = ' '.join(ss[1:]).replace('\n', '')
            if self._cdvd.has_key(k) and type(self._cdvd[k]) is not type([]):
                self._cdvd[k] = [self._cdvd[k]]
            if self._cdvd.has_key(k):
                self._cdvd[k] += v
            else:
                self._cdvd[k] = v

    def do_hr(self, attrs):
        if self._indvd and self._cdvd:
            self._dvd.append(self._cdvd.copy())
            self._reset()

    def start_a(self, attrs):
        name = self.get_attr_value(attrs, 'name')
        if name and len(name) > 1 and name[0] == "X":
            self._indvd = 1
        if not self._indvd: return
        href = self.get_attr_value(attrs, 'href')
        hrefl = href
        if href: hrefl = href.lower()
        if hrefl and hrefl.find('sections/dvds/labels') != -1:
            self._binfo_txt = 'label::'
            self._noendb = 1
        elif hrefl and hrefl.find('sections/dvds/pictureformats') != -1:
            self._binfo_txt = 'picture format::'
            self._noendb = 1
        elif hrefl and hrefl.find('sections/dvds/regions') != -1:
            self._finfo_txt = 'region::'
        elif hrefl and hrefl.find('sections/dvds/video') != -1:
            self._finfo_txt = 'video standard::'
        elif hrefl and hrefl.find('sections/dvds/packaging') != -1:
            self._finfo_txt = 'packaging::'

    def end_a(self): pass

    def do_br(self, attrs):
        if self._indvd:
            if self._intitle: self._curtitle += ' - '
            if self._binfo:
                self._binfo = 0
                if self._binfo_txt:
                    self._put_data(self._binfo_txt)
                    self._binfo_txt = ''

    def start_table(self, attrs):
        self._thl = []

    def end_table(self):
        if self._insound: self._insound = 0

    def start_th(self, attrs):
        if self._indvd:
            self._inth = 1
            span = self.get_attr_value(attrs, 'colspan')
            if span:
                try:self._thmult = int(span)
                except (ValueError, OverflowError): pass

    def end_th(self):
        self._inth = 0

    def start_tr(self, attrs):
        if not self._indvd: return
        if self._thl:
            self._colcount = -1

    def end_tr(self): pass

    def start_td(self, attrs):
        if not self._indvd: return
        if self._thl:
            self._colcount += 1
            self._colcount %= len(self._thl)

    def end_td(self):
        if not self._indvd: return
        if self._thl:
            self._coldata = self._coldata.strip()
            if not self._coldata: return
            if not self._insound:
                k = self._thl[self._colcount]
                v = self._coldata.strip().replace('\n', ' ').replace('  ', ' ')
                if v.find('::') != -1:
                    v = [x.strip() for x in v.split('::') if x.strip()]
                if not (k and v): return
                self._cdvd[k] = v
            else:
                if not self._cdvd.has_key('sound'): self._cdvd['sound'] = {}
                lang = self._thl[self._colcount].lower()
                self._cdvd['sound'][lang] = self._coldata
            self._coldata = ''

    def start_li(self, attrs):
        if self._indvd and self._thl and self._coldata.strip():
            self._coldata += '::'

    def end_li(self): pass
            
    def start_h3(self, attrs):
        if self._indvd:
            self._intitle = 1

    def end_h3(self):
        if self._indvd:
            self._intitle = 0
            self._cdvd['title'] = self._curtitle

    def start_font(self, attrs):
        if not self._indvd: return
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.lower() in ('catheader', 'smalltxt') and \
                not self._inth and not self._binfo:
            self._finfo = 1

    def end_font(self):
        if not self._indvd: return
        if self._finfo:
            self._finfo = 0
            self._finfo_txt = self._finfo_txt.strip()
            if self._finfo_txt:
                self._put_data(self._finfo_txt)
                self._finfo_txt = ''

    def do_img(self, attrs):
        src = self.get_attr_value(attrs, 'src')
        if src and src.lower().find('images.amazon.com') != -1:
            self._cdvd['cover'] = src

    def start_b(self, attrs):
        if self.kind == 'laserdisc':
            cls = self.get_attr_value(attrs, 'class')
            if cls and cls.lower() == 'ch':
                if not self._indvd:
                    self._indvd = 1
        if not self._indvd: return
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.lower() in ('catheader', 'smalltxt', 'aspectratio') \
                and not self._inth:
            self._binfo = 1
            self._binfo_txt = ''
            if cls.lower() == 'aspectratio': self._inar = 1

    def end_b(self):
        if self._binfo:
            self._binfo_txt = self._binfo_txt.strip()
            if self._binfo_txt:
                if self._binfo_txt[-1] == ':':
                    self._binfo_txt = self._binfo_txt[:-1]
                sep = '::'
                if self._noendb:
                    sep = ' '
                    self._noendb = 0
                self._binfo_txt += sep
            if  self._inar:
                self._inar = 0
                self._binfo_txt = self._binfo_txt.replace(' : ', ':')
                self._put_data('aspect ratio::%s' % self._binfo_txt)

    def _handle_data(self, data):
        if self._indvd:
            if self._inth:
                dsl = data.replace(':', '').strip().lower()
                self._thl += [dsl]*self._thmult
                if dsl == 'sound':
                    self._insound = 1
            if self._intitle:
                self._curtitle += data
            elif self._binfo:
                sdata = data.lstrip()
                if sdata:
                    self._binfo_txt += sdata
            elif self._finfo:
                sdata = data.lstrip()
                if sdata:
                    self._finfo_txt += sdata
            elif self._thl and not self._inth:
                self._coldata += data


class HTMLRecParser(ParserBase):
    """Parser for the "recommendations" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rparser = HTMLRecParser()
        result = rparser.parse(recommendations_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._rec = {}
        self._firsttd = 0
        self._curlist = ''
        self._curtitle = ''
        self._startgath = 0
        self._intable = 0
        self._inb = 0
        self._cur_id = ''
    
    def get_data(self):
        if not self._rec: return {}
        return {'recommendations': self._rec}

    def start_a(self, attrs):
        if self._firsttd:
            href = self.get_attr_value(attrs, 'href')
            if href:
                tn = self.re_imdbID.findall(href)
                if tn:
                    self._cur_id = tn[-1]

    def end_a(self): pass

    def start_table(self, attrs):
        self._intable = 1

    def end_table(self):
        self._intable = 0
        self._startgath = 0

    def start_tr(self, attrs):
        self._firsttd = 1

    def end_tr(self): pass

    def start_td(self, attrs):
        if self._firsttd:
            span = self.get_attr_value(attrs, 'colspan')
            if span: self._firsttd = 0

    def end_td(self):
        if self._firsttd:
            self._curtitle = clear_text(self._curtitle)
            if self._curtitle:
                if self._curlist:
                    if self._cur_id:
                        m = Movie(movieID=str(self._cur_id),
                                    title=self._curtitle,
                                    accessSystem='http')
                        self._rec.setdefault(self._curlist, []).append(m)
                        self._cur_id = ''
                self._curtitle = ''
            self._firsttd = 0

    def start_b(self, attrs):
        self._inb = 1

    def end_b(self):
        self._inb = 0

    def _handle_data(self, data):
        ldata = data.lower()
        if self._intable and self._inb:
            if ldata.find('suggested by the database') != -1:
                self._startgath = 1
                self._curlist = 'database'
            elif ldata.find('imdb users recommend') != -1:
                self._startgath = 1
                self._curlist = 'users'
        elif self._firsttd and self._curlist:
            self._curtitle += data


class HTMLNewsParser(ParserBase):
    """Parser for the "news" page of a given movie or person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        nwparser = HTMLNewsParser()
        result = nwparser.parse(news_html_string)
    """

    def _reset(self):
        """Reset the parser."""
        self._intable = 0
        self._inh1 = 0
        self._innews = 0
        self._cur_news = {}
        self._news = []
        self._cur_stage = 'title'
        self._cur_text = ''
        self._cur_link = ''

    def get_data(self):
        """Return the dictionary."""
        if not self._news: return {}
        return {'news': self._news}

    def start_table(self, attrs):
        self._intable = 1

    def end_table(self):
        self._intable = 0
        self._innews = 0

    def start_h1(self, attrs):
        self._inh1 = 1

    def end_h1(self):
        self._inh1 = 0

    def start_p(self, attrs): pass

    def end_p(self):
        if self._innews:
            if self._cur_news:
                self._news.append(self._cur_news)
                self._cur_news = {}
            self._cur_stage = 'title'
            self._cur_text = ''

    def do_br(self, attrs):
        if self._innews and not self._inh1:
            self._cur_text = self._cur_text.strip()
            if self._cur_text:
                if self._cur_stage == 'body':
                    if self._cur_news.has_key('body'):
                        bodykey = self._cur_news['body']
                        if bodykey and not bodykey[0].isspace():
                            self._cur_news['body'] += ' '
                        self._cur_news['body'] += self._cur_text
                    else:
                        self._cur_news['body'] = self._cur_text
                else:
                    self._cur_news[self._cur_stage] = self._cur_text
                self._cur_text = ''
                if self._cur_stage == 'title':
                    self._cur_stage = 'date'
                elif self._cur_stage == 'date':
                    self._cur_stage = 'body'

    def start_a(self, attrs):
        if self._innews and self._cur_stage == 'date':
            href = self.get_attr_value(attrs, 'href')
            if href:
                if not href.startswith('http://'):
                    if href[0] == '/': href = href[1:]
                    href = 'http://akas.imdb.com/%s' % href
                self._cur_news['link'] = href

    def _handle_data(self, data):
        if self._innews:
            if not self._inh1:
                self._cur_text += data
        elif self._inh1 and self._intable:
            if data.strip().lower().startswith('news for'):
                self._innews = 1


class HTMLAmazonReviewsParser(ParserBase):
    """Parser for the "amazon reviews" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        arparser = HTMLAmazonReviewsParser()
        result = arparser.parse(amazonreviews_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        """Reset the parser."""
        self._intable = 0
        self._inh3 = 0
        self._inreview = 0
        self._in_kind = 0
        self._reviews = []
        self._cur_title = ''
        self._cur_text = ''
        self._cur_link = ''
        self._cur_revkind = ''
    
    def get_data(self):
        """Return the dictionary."""
        if not self._reviews: return {}
        return {'amazon reviews': self._reviews}

    def start_table(self, attrs):
        self._intable = 1

    def end_table(self):
        if self._inreview:
            self._add_info()
            self._cur_title = ''
            self._cur_link = ''
        self._intable = 0
        self._inreview = 0

    def start_h3(self, attrs):
        self._inh3 = 1
        self._cur_link = ''
        self._cur_title = ''

    def end_h3(self):
        self._inh3 = 0

    def start_a(self, attrs):
        if self._inh3:
            href = self.get_attr_value(attrs, 'href')
            if href:
                if not href.startswith('http://'):
                    if href[0] == '/': href = href[1:]
                    href = 'http://akas.imdb.com/%s' % href
                self._cur_link = href.strip()

    def end_a(self): pass

    def start_b(self, attrs):
        if self._inreview:
            self._in_kind = 1

    def end_b(self):
        self._in_kind = 0

    def start_p(self, attrs):
        if self._inreview:
            self._add_info()

    def end_p(self):
        self._inreview = 0
        self._cur_title = ''
        self._cur_link = ''

    def _add_info(self):
        self._cur_title = self._cur_title.replace('\n', ' ').strip()
        self._cur_text = self._cur_text.replace('\n', ' ').strip()
        self._cur_link = self._cur_link.strip()
        self._cur_revkind = self._cur_revkind.replace('\n', ' ').strip()
        entry = {}
        if not self._cur_text: return
        ai = self._cur_text.rfind(' --', -30)
        author = ''
        if ai != -1:
            author = self._cur_text[ai+3:]
            self._cur_text = self._cur_text[:ai-1]
        if self._cur_title and self._cur_title[-1] == ':':
            self._cur_title = self._cur_title[:-1]
        if self._cur_revkind and self._cur_revkind[-1] == ':':
            self._cur_revkind = self._cur_revkind[:-1]
        if self._cur_title: entry['title'] = self._cur_title
        if self._cur_text: entry['review'] = self._cur_text
        if self._cur_link: entry['link'] = self._cur_link
        if self._cur_revkind: entry['review kind'] = self._cur_revkind
        if author: entry['review author'] = author
        if entry: self._reviews.append(entry)
        self._cur_text = ''
        self._cur_revkind = ''

    def _handle_data(self, data):
        if self._inreview:
            if self._in_kind:
                self._cur_revkind += data
            else:
                self._cur_text += data
        elif self._intable and self._inh3:
            self._inreview = 1
            self._cur_title += data


class HTMLGuestsParser(ParserBase):
    """Parser for the "episodes cast" page of a given tv series.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = HTMLGuestsParser()
        result = gparser.parse(guests_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        self._guests = {}
        self._in_guests = 0
        self._inh1 = 0
        self._goth1 = 0
        self._ingtable = 0
        self._inname = 0
        self._curname = ''
        self._curid = ''
        self._inepisode = 0
        self._curepisode = ''

    def get_data(self):
        if not self._guests: return {}
        return {'guests': self._guests}

    def start_h1(self, attrs):
        self._inh1 = 1

    def end_h1(self):
        self._inh1 = 0

    def start_a(self, attrs):
        if self._inname:
            href = self.get_attr_value(attrs, 'href')
            if not href:
                self._curid = ''
                return
            cid = self.re_imdbID.findall(href)
            if not cid: self._curid = ''
            else: self._curid = cid[0]

    def end_a(self): pass

    def start_table(self, attrs):
        if self._goth1: self._in_guests = 1

    def end_table(self):
        self._goth1 = 0

    def start_div(self, attrs):
        self._in_guests = 0

    def end_div(self): pass

    def do_br(self, attrs):
        if self._inepisode and self._curepisode:
            self._curepisode += '::'

    def start_tr(self, attrs): pass

    def end_tr(self):
        if self._inname:
            self._curepisode = self._curepisode.replace('\n',
                                ' ').replace('  ', ' ').strip(':').strip()
            if not self._curepisode: self._curepisode = 'UNKNOWN EPISODE'
            self._curname = self._curname.replace('\n', '').strip()
            if self._curname and self._curid:
                name = self._curname.strip()
                note = ''
                bni = name.find('(')
                if bni != -1:
                    eni = name.rfind(')')
                    if eni != -1:
                        note = name[bni:]
                        name = name[:bni].strip()
                sn = name.split(' .... ')
                name = sn[0]
                role = ' '.join(sn[1:]).strip()
                p = Person(name=name, personID=str(self._curid),
                            currentRole=role, accessSystem='http',
                            notes=note)
                self._guests.setdefault(self._curepisode, []).append(p)
        if self._in_guests:
            self._inname = 0
            self._curname = ''
            self._curid = ''

    def start_td(self, attrs):
        if self._in_guests:
            colstyle = self.get_attr_value(attrs, 'style')
            if colstyle and colstyle.startswith('padding-top: 5px'):
                self._inepisode = 1
                self._curepisode = ''
            else:
                self._inname = 1

    def end_td(self): pass

    def _handle_data(self, data):
        if self._inh1 and data.lower().find('episodes cast') != -1:
            self._goth1 = 1
        elif self._in_guests:
            if self._inname: self._curname += data
            elif self._inepisode: self._curepisode += data


class HTMLSalesParser(ParserBase):
    """Parser for the "merchandising links" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = HTMLSalesParser()
        result = sparser.parse(sales_html_string)
    """

    # Do not gather names and titles references.
    getRefs = 0

    def _reset(self):
        self._sales = {}
        self._cur_type = ''
        self._cur_info = {}
        self._in_h3 = 0
        self._in_dt = 0
        self._get_img = 0
        self._get_link = 0
        self._cur_descr = ''
        self._get_descr = 0
        self._in_a = 0
        self._in_dd = 0

    def get_data(self):
        if not self._sales: return {}
        return {'merchandising links': self._sales}
    
    def start_h3(self, attrs):
        self._in_h3 = 1
        self._cur_type = ''

    def end_h3(self):
        if self._in_h3:
            self._in_h3 = 0

    def start_td(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls:
            clsl = cls.lower()
            if clsl == 'w_rowtable_colcover':
                self._get_img = 1
            elif clsl == 'w_rowtable_coldetails':
                self._get_descr = 1
                self._cur_descr = ''

    def end_td(self):
        self._get_descr = 0

    def start_img(self, attrs):
        if self._get_img:
            self._get_img = 0
            src = self.get_attr_value(attrs, 'src')
            if src: self._cur_info['cover'] = src

    def end_img(self): pass

    def start_tr(self, attrs): pass

    def end_tr(self):
        self._cur_descr = self._cur_descr.strip()
        if self._cur_descr:
            self._cur_info['description'] = self._cur_descr
            self._cur_descr = ''
            if self._cur_info:
                self._sales.setdefault(self._cur_type,
                                        []).append(self._cur_info)
                self._cur_info = {}

    def start_dt(self, attrs):
        self._in_dt = 1
        self._cur_type = ''

    def end_dt(self):
        if self._in_dt:
            self._in_dt = 0

    def start_dd(self, attrs):
        self._in_dd = 1
        self._get_link = 1

    def end_dd(self):
        self._in_dd = 0
        if self._cur_info.has_key('cover'):
            del self._cur_info['cover']
        self.end_tr()

    def start_a(self, attrs):
        self._in_a = 1
        href = self.get_attr_value(attrs, 'href')
        if href:
            if self._get_img or self._get_link:
                if href[0] == '/':
                    href = 'http://akas.imdb.com%s' % href
                self._cur_info['link'] = href
                self._get_link = 0

    def end_a(self):
        self._in_a = 0

    def _handle_data(self, data):
        if self._in_h3 or self._in_dt:
            self._cur_type += data.lower()
        elif self._get_descr or (self._in_dd and not self._in_a):
            self._cur_descr += data


# The used instances.
movie_parser = HTMLMovieParser()
plot_parser = HTMLPlotParser()
movie_awards_parser = HTMLAwardsParser()
taglines_parser = HTMLTaglinesParser()
keywords_parser = HTMLKeywordsParser()
crazycredits_parser = HTMLCrazyCreditsParser()
goofs_parser = HTMLGoofsParser()
alternateversions_parser = HTMLAlternateVersionsParser()
trivia_parser = HTMLAlternateVersionsParser()
soundtrack_parser = HTMLAlternateVersionsParser()
trivia_parser.kind = 'trivia'
soundtrack_parser.kind = 'soundtrack'
quotes_parser = HTMLQuotesParser()
releasedates_parser = HTMLReleaseinfoParser()
ratings_parser = HTMLRatingsParser()
officialsites_parser = HTMLOfficialsitesParser()
externalrev_parser = HTMLOfficialsitesParser()
externalrev_parser.kind = 'external reviews'
newsgrouprev_parser = HTMLOfficialsitesParser()
newsgrouprev_parser.kind = 'newsgroup reviews'
misclinks_parser = HTMLOfficialsitesParser()
misclinks_parser.kind = 'misc links'
soundclips_parser = HTMLOfficialsitesParser()
soundclips_parser.kind = 'sound clips'
videoclips_parser = HTMLOfficialsitesParser()
videoclips_parser.kind = 'video clips'
photosites_parser = HTMLOfficialsitesParser()
photosites_parser.kind = 'photo sites'
connections_parser = HTMLConnectionParser()
tech_parser = HTMLTechParser()
business_parser = HTMLTechParser()
business_parser.kind = 'business'
business_parser.getRefs = 1
locations_parser = HTMLTechParser()
locations_parser.kind = 'locations'
dvd_parser = HTMLDvdParser()
rec_parser = HTMLRecParser()
news_parser = HTMLNewsParser()
amazonrev_parser = HTMLAmazonReviewsParser()
guests_parser = HTMLGuestsParser()
sales_parser = HTMLSalesParser()

