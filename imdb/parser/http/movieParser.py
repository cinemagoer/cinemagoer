"""
parser.http.movieParser module (imdb package).

This module provides the classes (and the instances), used to parse the
IMDb pages on the akas.imdb.com server about a movie.
E.g., for Brian De Palma's "The Untouchables", the referred
pages would be:
    combined details:   http://akas.imdb.com/title/tt0094226/combined
    plot summary:       http://akas.imdb.com/title/tt0094226/plotsummary
    ...and so on...

Copyright 2004-2008 Davide Alberani <da@erlug.linux.it>
               2008 H. Turgut Uyar <uyar@tekir.org>

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

import re
import urllib

from imdb import imdbURL_base
from imdb.Person import Person
from imdb.Movie import Movie
from imdb.Company import Company
from imdb.utils import analyze_title, split_company_name_notes, _Container
from utils import ParserBase, build_person, DOMParserBase, Attribute, \
        Extractor, analyze_imdbid


# Dictionary used to convert some section's names.
_SECT_CONV = {
        'directed': 'director',
        'directed by': 'director',
        'directors': 'director',
        'editors': 'editor',
        'writing credits': 'writer',
        'writers': 'writer',
        'produced': 'producer',
        'cinematography': 'cinematographer',
        'film editing': 'editor',
        'casting': 'casting director',
        'costume design': 'costume designer',
        'makeup department': 'make up',
        'production management': 'production manager',
        'second unit director or assistant director': 'assistant director',
        'costume and wardrobe department': 'costume department',
        'sound department': 'sound crew',
        'stunts':   'stunt performer',
        'other crew': 'miscellaneous crew',
        'also known as': 'akas',
        'country':  'countries',
        'runtime':  'runtimes',
        'language': 'languages',
        'certification':    'certificates',
        'genre': 'genres',
        'created': 'creator',
        'creators': 'creator',
        'color': 'color info',
        'plot': 'plot outline',
        'seasons': 'number of seasons',
        'art directors': 'art direction',
        'assistant directors': 'assistant director',
        'set decorators': 'set decoration',
        'visual effects department': 'visual effects',
        'production managers': 'production manager',
        'miscellaneous': 'miscellaneous crew',
        'make up department': 'make up',
        'plot summary': 'plot outline',
        'cinematographers': 'cinematographer',
        'camera department': 'camera and electrical department',
        'costume designers': 'costume designer',
        'production designers': 'production design',
        'production managers': 'production manager',
        'music original': 'original music',
        'casting directors': 'casting director',
        'other companies': 'miscellaneous companies',
        'producers': 'producer',
        'special effects by': 'special effects department',
        'special effects': 'special effects companies'
        }
# List of allowed sections.
_SECT_KEEP = _SECT_CONV.values() + ['cast', 'original music', 'tv series',
            'mpaa', 'non-original music', 'art direction', 'set decoration',
            'art department', 'special effects', 'visual effects', 'sound mix',
            'camera and electrical department', 'production notes/status',
            'production design', 'transportation department', 'distributors',
            'editorial department', 'casting department',
            'animation department', 'original air date', 'status', 'comments',
            'status updated', 'note']


class HTMLMovieParser(ParserBase):
    """Parser for the "combined details" (and if instance.mdparse is
    True also for the "main details") page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        mparser = HTMLMovieParser()
        result = mparser.parse(combined_details_html_string)
    """
    re_votes = re.compile(r'([0-9][0-9]?\.[0-9])/10(\s+([0-9,]+)\s+votes)?',
                            re.I|re.M|re.S)
    def _reset(self):
        # If true, we're parsing the "maindetails" page; if false,
        # the "combined" page is expected.
        self.mdparse = False
        self._data = {}
        # The current section.
        self._section = u''
        # Most of the data are collected in self._cur_txt; some boolean
        # variable are set to True when we're parsing a significant section.
        self._cur_txt = u''
        self._in_tr = False
        self._in_info_div = False
        self._in_li = False
        # Some variable used to know when to collect data and when to stop.
        # XXX: things can be made much simpler.
        self._keep = False
        self._stop_here = False
        self._exclude_series = False
        self._title = u''
        # Horrible hack to fix some incongruities of the data.
        self._in_td = False
        # Movie status.
        self._in_production_notes = False
        self._status_sect = u''
        # Last movieID/personID/characterID/companyID seen.
        self._last_movie_id = None
        self._last_person_id = None
        self._last_company_id = None
        self._cids = []
        # Counter for the billing position.
        self._billingPos = 1
        # Various information.
        self._in_h1 = False
        self._in_h5 = False
        self._in_b = False
        self._in_total_episodes = False
        self._total_episodes = u''
        self._in_rating = False
        self._rating = u''
        self._in_top250 = False
        self._top250 = u''
        self._in_poster = False
        self._in_small = False
        # Companies information are stored slightly differently.
        self._in_blackcatheader = False
        self._in_company_info = False

    def get_data(self):
        return self._data

    def start_h1(self, attrs):
        self._in_h1 = True

    def end_h1(self):
        self._in_h1 = False
        self._title = self._title.strip()
        seridx = self._title.find(u'\xbbTV series')
        if seridx != -1:
            self._data['series years'] = self._title[seridx+10:].lstrip()
            self._title = self._title[:seridx].rstrip()
        self._title = self._title.replace('More at IMDb Pro', '').rstrip()
        if not self._title: return
        # The movie's title.
        self._data.update(analyze_title(self._title, canonical=1))

    def _manage_section(self):
        # Do some transformation on the section name.
        cs = self._section.strip().lower()
        # Strip commas and parentheses.
        if cs[-1:] == ':':
            cs = cs[:-1].rstrip()
        if not cs:
            self._section = u''
            return
        paridx = cs.find('(')
        if paridx != -1:
            cs = cs[:paridx].rstrip()
        cssplit = cs.split()
        # In tv series, the section name is preceded by 'Series'.
        if cssplit[0] in ('series', 'episode'):
            cssplit[:] = cssplit[1:]
        if cssplit:
            if cssplit[0] == 'cast':
                cssplit[:] = ['cast']
            elif cssplit[-1] == 'by' and cs not in ('special effects by',
                    'series special effects by', 'episode special effects by'):
                cssplit[:] = cssplit[:-1]
        cs = ' '.join(cssplit)
        # Convert the section name, if present in _SECT_CONV.
        cs = _SECT_CONV.get(cs, cs)
        # Check if this is a section to keep.
        if cs not in _SECT_KEEP:
            if cs.endswith('department'):
                # The IMDb site seems prone to adding 'department'
                # categories at will.
                self._section = str(cs)
                self._keep = True
            elif not self._in_company_info:
                # This is not a companies information, so it's ok to
                # discard it.
                cs = u''
                self._keep = False
            else:
                # Companies information; do some transformation.
                if cs == 'special effects':
                    cs = 'special effects companies'
                elif cs == 'other companies':
                    cs = 'miscellaneous companies'
            self._section = str(cs)
        elif cs == 'production notes/status':
            self._in_production_notes = True
            self._keep = False
        else:
            self._section = str(cs)
            self._keep = True

    def start_h5(self, attrs):
        # Normally section names are enclosed in h5 tags.
        if self._exclude_series: return
        self._in_h5 = True
        self._keep = False
        self._stop_here = False
        self._section = u''
        self._billingPos = 1
        self._last_person_id = None
        self._last_company_id = None
        self._cids = []

    def end_h5(self):
        # If self._exclude_series, we're already looking at series-specific
        # information, while parsing an episode.
        if self._exclude_series: return
        self._in_h5 = False
        self._manage_section()
        if self.mdparse and self._section in _SECT_KEEP:
            # Parse also the upper "Directed by" and "Created by", while
            # httpThin is used (they are the only place these info are).
            self._in_tr = True

    start_h3 = start_h5
    end_h3 = end_h5

    def start_h6(self, attrs):
        # Production status is in h6 tags.
        if self._in_production_notes:
            self._in_h5 = True
            self.start_h5(attrs)

    def end_h6(self):
        if self._in_production_notes:
            self._in_h5 = False
            self.end_h5()

    def do_p(self, attrs):
        if self._in_production_notes:
            self._in_production_notes = False

    def start_div(self, attrs):
        # Major information sets are enclosed in div tags with class=info.
        if self._exclude_series: return
        cls = self.get_attr_value(attrs, 'class')
        if cls == 'info':
            self._in_info_div = True
            self._cur_txt = u''
        elif cls == 'meta':
            self._in_rating = True

    def end_div(self):
        if self._exclude_series: return
        if self._in_rating:
            self.end_small()
            self._in_rating = False
        if not self._keep: return
        if self._in_info_div:
            self._add_info()
            self._in_info_div = False
        elif self._in_production_notes:
            # End of 'status note'.
            self._add_info()
            self._in_production_notes = False

    def start_b(self, attrs):
        # Companies information are stored in section enclosed in b tags
        # with class=blackcatheader.
        self._in_b = True
        self._in_company_info = False
        if self.get_attr_value(attrs, 'class') == 'blackcatheader':
            self._in_blackcatheader = True
            self._last_company_id = None
            self._keep = False
            self._section = u''

    def end_b(self):
        self._in_b = False
        if self._in_blackcatheader:
            self._in_blackcatheader = False
            self._keep = True
            self._in_company_info = True
            self._manage_section()

    def start_ul(self, attrs): pass

    def end_ul(self):
        if self._in_company_info:
            self._in_company_info = False
            self._last_company_id = None

    def start_li(self, attrs):
        # Most of companies info are in li tags.
        self._in_li = True

    def end_li(self):
        self._in_li = False
        if self._in_company_info and self._section:
            self._add_info()

    def start_small(self, attrs):
        self._in_small = True

    def end_small(self):
        self._in_small = False
        # Rating and votes.
        if not self._in_rating: return
        self._in_rating = False
        rav = self._rating.strip()
        if not rav: return
        rg = self.re_votes.search(rav)
        if not rg: return
        try: rating = rg.group(1)
        except IndexError: return
        try:
            rating = float(rating)
            self._data['rating'] = rating
        except ValueError:
            pass
        try: votes = rg.group(3)
        except IndexError: return
        votes = votes.replace(',', '')
        try:
            votes = int(votes)
            self._data['votes'] = votes
        except ValueError:
            pass

    def start_span(self, attrs): pass

    def end_span(self):
        # Handle the span for 'status note'.
        if not self._in_production_notes: return
        self._add_info()
        self._in_production_notes = False

    def _add_info(self):
        # Used to add information about h5, h6 and b sections.
        ct = self._cur_txt.strip()
        if ct.endswith('|'):
            ct = ct.rstrip('|').rstrip()
        if not ct:
            self._cur_txt = u''
            return
        if self._section in ('director', 'writer'):
            self._cur_txt = u''
            return
        if self._section in ('status', 'comments', 'status updated', 'note',
                            'status note'):
            if not self._section.startswith('status'):
                self._section = 'status %s' % self._section
            self._data[self._section] = ct
        elif self._section == 'plot outline':
            self._data[self._section] = ct
        elif self._section == 'mpaa':
            self._data[self._section] = ct
        elif self._section == 'number of seasons':
            self._data[self._section] = ct.count('|') + 1
        elif self._section == 'tv series':
            if self._data.get('kind') == 'episode' and \
                        self._last_movie_id is not None:
                m = Movie(title=ct, movieID=self._last_movie_id,
                            accessSystem=self._as, modFunct=self._modFunct)
                self._data['episode of'] = m
            self._cur_txt = u''
            return
        elif self._section == 'original air date':
            aid = self.re_airdate.findall(ct)
            if aid and len(aid[0]) == 3:
                date, season, episode = aid[0]
                date = date.strip()
                try: season = int(season)
                except: pass
                try: episode = int(episode)
                except: pass
                if date and date != '????':
                    self._data['original air date'] = date
                # Handle also "episode 0".
                if season or type(season) is type(0):
                    self._data['season'] = season
                if episode or type(season) is type(0):
                    self._data['episode'] = episode
        elif self._section in ('countries', 'genres', 'languages', 'runtimes',
                                'color info', 'sound mix', 'certificates'):
            if self._section == 'runtimes':
                ct = ct.replace(' min', u'')
            splitted_info = ct.split(' | ')
            splitted_info[:] = [x.strip() for x in splitted_info]
            splitted_info[:] = filter(None, splitted_info)
            splitted_info[:] = [x.replace(' (', '::(', 1)
                                for x in splitted_info]
            if not self._data.has_key(self._section):
                self._data[self._section] = splitted_info
        elif self._in_company_info and self._last_company_id:
            name, notes = split_company_name_notes(ct)
            company = Company(name=name, notes=notes,
                            accessSystem=self._as,
                            companyID=self._last_company_id)
            self._data.setdefault(self._section, []).append(company)
        elif self._section != 'cast':
            self._data.setdefault(self._section, []).append(ct)
        self._cur_txt = u''

    def do_br(self, attrs):
        # Do some transformation on akas.
        if not self._keep: return
        if self._section == 'akas':
            self._cur_txt = self._cur_txt.replace('   ', ' ')
            self._cur_txt = self._cur_txt.replace('  ', ' ')
            self._cur_txt = self._cur_txt.replace(' (', '::(', 1)
            #self._cur_txt = self._cur_txt.replace(' [', '::[', 1)
            self._add_info()
        elif self._in_production_notes:
            self._add_info()
            self._keep = False
        if (self.mdparse or self._section == 'creator') and \
                self._section in _SECT_KEEP:
            if self._cur_txt.endswith('...'):
                self._cur_txt = self._cur_txt[:-3]
            self.end_tr()
            self._in_tr = True

    def start_tr(self, attrs):
        self._in_tr = True

    def end_tr(self):
        # Add cast/roles information.
        self._in_tr = False
        ct = self._cur_txt = self._cur_txt.strip()
        if not self._keep:
            self._cur_txt = u''
            return
        if self._last_person_id is None:
            self._cur_txt = u''
            return
        if not ct: return
        if ct[0] == '(' and ct[-1] == ')':
            self._cur_txt = u''
            return
        if self._section == 'cast' and ct.startswith('rest of cast listed'):
            self._cur_txt = u''
            return
        cids = self._cids
        if not cids:
            cids = None
        elif len(cids) == 1:
            cids = cids[0]
        p = build_person(ct, personID=self._last_person_id,
                        billingPos=self._billingPos,
                        roleID=cids, accessSystem=self._as,
                        modFunct=self._modFunct)
        self._data.setdefault(self._section, []).append(p)
        self._billingPos += 1
        self._cur_txt = u''
        self._last_person_id = None
        self._cids = []

    def start_td(self, attrs):
        if not (self._keep and self._cur_txt and self._last_person_id): return
        self._in_td = True

    def end_td(self):
        self._in_td = False

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if self.get_attr_value(attrs, 'title') == 'Full Episode List':
            self._in_total_episodes = True
        elif href and href.startswith('/chart/top?tt'):
            self._in_top250 = True
        elif self.get_attr_value(attrs, 'name') == 'poster':
            self._in_poster = True
        # From here on, we're inside some kind of information and a href.
        if not (self._keep and href): return
        # Hack!  Keep in mind, if it will ever be needed to know if
        # we're inside a td tag; that's here to prevent lines like:
        #  <td><a href="...">Person Name</a>  </td>
        # to trigger some code in the _handle_data method.
        self._in_td = False
        # Collect personID, movieID and characterID.
        if href.startswith('/name/nm'):
            cur_id = self.re_imdbID.findall(href)
            if cur_id:
                self._last_person_id = cur_id[-1]
            return
        elif self._data.get('kind') == 'episode' and \
                    href.startswith('/title/tt'):
            cur_id = self.re_imdbID.findall(href)
            if cur_id:
                self._last_movie_id = cur_id[-1]
        elif href.startswith('/character/ch'):
            cur_id = self.re_imdbID.findall(href)
            if cur_id:
                lid = cur_id[-1]
                self._cids.append(lid)
        elif self._in_company_info and href.startswith('/company/co'):
            cur_id = self.re_imdbID.findall(href)
            if cur_id:
                self._last_company_id = cur_id[-1]
        elif self.mdparse and href.startswith('fullcredits#'):
            # The "more" link at the end of the cast.
            self._in_tr = False
        if self._in_info_div:
            # The various "more" links.
            cls = self.get_attr_value(attrs, 'class')
            if cls and cls.startswith('tn15more'):
                self._stop_here = True

    def end_a(self):
        if self._in_total_episodes:
            self._in_total_episodes = False
            try:
                te = int(self._total_episodes.strip().split()[0])
                self._data['number of episodes'] = te
            except:
                pass
            self._total_episodes = u''
        elif self._in_top250:
            self._in_top250 = False
            self._top250 = self._top250.strip()
            posidx = self._top250.find('#')
            if posidx != -1:
                top250 = self._top250[posidx+1:]
                try: self._data['top 250 rank'] = int(top250)
                except: pass
        elif self._in_poster:
            self._in_poster = False

    def do_img(self, attrs):
        if self._in_poster:
            src = self.get_attr_value(attrs, 'src')
            if src:
                self._data['cover url'] = src
        # For some funny reason the cast section is tagged by an image.
        alt = self.get_attr_value(attrs, 'alt')
        if alt and alt.lower() == 'cast':
            self._section = 'cast'
            self._manage_section()

    def _handle_data(self, data):
        if self._in_h5 or self._in_blackcatheader:
            # Section's name.
            self._section += data
        elif self._in_h1 and not self._in_small:
            self._title += data
        elif self._in_rating:
            self._rating += data
        if self._in_b:
            sldata = data.strip().lower()
            if sldata == 'user rating:':
                self._in_rating = True
            elif sldata == 'series crew':
                self._exclude_series = True
        elif self._in_total_episodes:
            self._total_episodes += data
        elif self._in_top250:
            self._top250 += data
        if self._stop_here or self._exclude_series or not self._keep: return
        if data == '(more)':
            pass
            self._stop_here = True
            return
        # Collect the data.
        if self._in_tr or self._in_info_div or self._in_li or \
                    self._in_production_notes:
            if self._in_td:
                if data == ' ':
                    self._cur_txt += ' ....'
            if self._section == 'cast':
                nrSep = data.count(' / ')
                if nrSep > 0:
                    sdata = data.strip()
                    if sdata == '/' or (sdata.endswith(' /') and
                                        sdata.startswith('/ ')):
                        nrSep -= 1
                    self._cids += [None]*nrSep
            self._cur_txt += data


def _manageRoles(mo):
    """Perform some transformation on the html, so that roleIDs can
    be easily retrieved."""
    firstHalf = mo.group(0)
    secondHalf = mo.group(1)
    newRoles = []
    roles = secondHalf.split(' / ')
    for role in roles:
        role = role.strip()
        if not role: continue
        roleID = analyze_imdbid(role)
        if roleID is None:
            roleID = u'/'
        else:
            roleID += u'/'
        newRoles.append(u'<div class="_imdbpyrole" roleid="%s">%s</div>' % \
                (roleID, role.strip()))
    return firstHalf.replace(secondHalf, u' / '.join(newRoles))

_reRolesMovie = re.compile(r'<td class="char">(.*?)</td>', re.I | re.M | re.S)

def _replaceBR(mo):
    """Replaces <br> tags with '::' (useful for some akas)"""
    txt = mo.group(0)
    return txt.replace('<br>', '::')

_reAkas = re.compile(r'<h5>also known as:</h5>.*?</div>', re.I | re.M | re.S)

def makeSplitter(lstrip=None, sep='|', comments=True):
    """Return a splitter function suitable for a given set of data."""
    def splitter(x):
        if not x: return x
        x = x.strip()
        if not x: return x
        if lstrip is not None:
            x = x.lstrip(lstrip).lstrip()
        lx = x.split(sep)
        lx[:] = filter(None, [j.strip() for j in lx])
        if comments:
            lx[:] = [j.replace(' (', '::(', 1) for j in lx]
        return lx
    return splitter

class DOMHTMLMovieParser(DOMParserBase):
    """Parser for the "combined details" (and if instance.mdparse is
    True also for the "main details") page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        mparser = DOMHTMLMovieParser()
        result = mparser.parse(combined_details_html_string)
    """
    _containsObjects = True

    # XXX: this class collects also information related to the series,
    #      parsing an episode's page (the old parser, stopped at the
    #      episode's data).  This may not be a problem, but the two
    #      sets of information end up in the same list; it would be
    #      wonderful if the series info can be put in a "series KEYWORD"
    #      list, but I think it's not easy at all.
    extractors = [Extractor(label='title',
                            path="//h1",
                            attrs=Attribute(key='title',
                                            path=".//text()",
                                            postprocess=lambda x: \
                                            analyze_title(x, canonical=1))),

                Extractor(label='glossarysections',
                        group="//a[@class='glossary']",
                        group_key="./@name",
                        group_key_normalize=lambda x: x.replace('_', ' '),
                        path="../../../..//tr",
                        attrs=Attribute(key=None,
                            multi=True,
                            path={'person': ".//text()",
                                    'link': "./td[1]/a[@href]/@href"},
                            postprocess=lambda x: \
                                    build_person(x.get('person') or u'',
                                        personID=analyze_imdbid(x.get('link')))
                                )),

                Extractor(label='cast',
                        path="//table[@class='cast']//tr",
                        attrs=Attribute(key="cast",
                            multi=True,
                            path={'person': ".//text()",
                                'link': "td[2]/a/@href",
                                'roleID': \
                                    "td[4]/div[@class='_imdbpyrole']/@roleid"},
                            postprocess=lambda x: \
                                    build_person(x.get('person') or u'',
                                    personID=analyze_imdbid(x.get('link')),
                                    roleID=(x.get('roleID') or u'').split('/'))
                                )),

                Extractor(label='genres',
                        path="//div[@class='info']//a[starts-with(@href," \
                                " '/Sections/Genres')]",
                        attrs=Attribute(key="genres",
                            multi=True,
                            path="./text()")),

                Extractor(label='h5sections',
                        path="//div[@class='info']/h5/..",
                        attrs=[
                            Attribute(key="plot summary",
                                path="./h5[starts-with(text(), " \
                                        "'Plot:')]/../text()",
                                postprocess=lambda x: \
                                        x.strip().rstrip('|').rstrip()),
                            Attribute(key="aspect ratio",
                                path="./h5[starts-with(text()," \
                                        " 'Aspect')]/../text()",
                                postprocess=lambda x: x.strip()),
                            Attribute(key="mpaa",
                                path="./h5/a[starts-with(text()," \
                                        " 'MPAA')]/../../text()",
                                postprocess=lambda x: x.strip()),
                            Attribute(key="countries",
                                path="./h5[starts-with(text(), " \
                                        "'Countr')]/../a/text()",
                                    postprocess=makeSplitter(sep='\n')),
                            Attribute(key="language",
                                path="./h5[starts-with(text(), " \
                                        "'Language')]/..//text()",
                                    postprocess=makeSplitter('Language:')),
                            Attribute(key='color info',
                                path="./h5[starts-with(text(), " \
                                        "'Color')]/..//text()",
                                postprocess=makeSplitter('Color:')),
                            Attribute(key='sound mix',
                                path="./h5[starts-with(text(), " \
                                        "'Sound Mix')]/..//text()",
                                postprocess=makeSplitter('Sound Mix:')),
                            # Collects akas not encosed in <i> tags.
                            Attribute(key='other akas',
                                path="./h5[starts-with(text(), " \
                                        "'Also Known As')]/../text()",
                                postprocess=makeSplitter(sep='::')),
                            Attribute(key='runtimes',
                                path="./h5[starts-with(text(), " \
                                        "'Runtime')]/../text()",
                                postprocess=makeSplitter()),
                            Attribute(key='certificates',
                                path="./h5[starts-with(text(), " \
                                        "'Certificat')]/..//text()",
                                postprocess=makeSplitter('Certification:')),
                            Attribute(key='number of seasons',
                                path="./h5[starts-with(text(), " \
                                        "'Seasons')]/../text()",
                                postprocess=lambda x: x.count('|') + 1),
                            Attribute(key='original air date',
                                path="./h5[starts-with(text(), " \
                                        "'Original Air Date')]/../text()"),
                            Attribute(key='tv series link',
                                path="./h5[starts-with(text(), " \
                                        "'TV Series')]/../a/@href"),
                            Attribute(key='tv series title',
                                path="./h5[starts-with(text(), " \
                                        "'TV Series')]/../a/text()")
                            ]),

                Extractor(label='creator',
                            path="//h5[starts-with(text(), 'Creator')]/../a",
                            attrs=Attribute(key='creator', multi=True,
                                    path={'name': "./text()",
                                        'link': "./@href"},
                                    postprocess=lambda x: \
                                        build_person(x.get('name') or u'',
                                        personID=analyze_imdbid(x.get('link')))
                                    )),

                Extractor(label='thin writer',
                            path="//h5[starts-with(text(), 'Writer')]/../a",
                            attrs=Attribute(key='thin writer', multi=True,
                                    path={'name': "./text()",
                                        'link': "./@href"},
                                    postprocess=lambda x: \
                                        build_person(x.get('name') or u'',
                                        personID=analyze_imdbid(x.get('link')))
                                    )),

                Extractor(label='thin director',
                            path="//h5[starts-with(text(), 'Director')]/../a",
                            attrs=Attribute(key='thin director', multi=True,
                                    path={'name': "./text()",
                                        'link': "@href"},
                                    postprocess=lambda x: \
                                        build_person(x.get('name') or u'',
                                        personID=analyze_imdbid(x.get('link')))
                                    )),

                Extractor(label='top 250',
                            path="//div[@class='left']/a[starts-with(@href, " \
                                    "'/chart/')]",
                            attrs=Attribute(key='top 250 rank',
                                            path="./text()",
                                            postprocess=lambda x: \
                                            int(x.replace('Top 250: #', '')))),

                Extractor(label='series years',
                            path="//div[@id='tn15title']//span" \
                                "[starts-with(text(), 'TV series')]",
                            attrs=Attribute(key='series years',
                                    path="./text()",
                                    postprocess=lambda x: \
                                            x.replace('TV series','').strip())),

                Extractor(label='number of episodes',
                            path="//a[@title='Full Episode List']",
                            attrs=Attribute(key='number of episodes',
                                    path="./text()",
                                    postprocess=lambda x: \
                                            int(x.replace(' Episodes', '')))),

                Extractor(label='akas',
                        path="//i[@class='transl']",
                        attrs=Attribute(key='akas', multi=True, path='text()',
                                postprocess=lambda x:
                                x.replace('  ', ' ').replace(' (',
                                    '::(', 1).replace('  ', ' '))),

                Extractor(label='production notes/status',
                        path="//div[@class='info inprod']",
                        attrs=Attribute(key='production notes',
                                path=".//text()",
                                postprocess=lambda x: x.strip())),

                Extractor(label='blackcatheader',
                        group="//b[@class='blackcatheader']",
                        group_key="./text()",
                        group_key_normalize=lambda x: x.lower(),
                        path="../ul/li",
                        attrs=Attribute(key=None,
                                multi=True,
                                path={'text': ".//text()",
                                        'comp-link': "./a/@href"},
                                postprocess=lambda x: \
                                        Company(name=x.get('text', u''),
                                companyID=analyze_imdbid(x.get('comp-link')))
                            )),

                #Extractor(label='votes and rating',
                #        path="//div[@class='general rating']",
                #        attrs=Attribute(key='votes and rating',
                #                        path=".//text()")),

                Extractor(label='votes and rating',
                        path="//div[@class='meta']",
                        attrs=Attribute(key='votes and rating',
                                        path=".//text()")),

                Extractor(label='cover url',
                        path="//a[@name='poster']",
                        attrs=Attribute(key='cover url',
                                        path="./img/@src"))
                ]

    preprocessors = [
        (re.compile(r'(<b class="blackcatheader">.+?</b>)', re.I),
            r'</div><div>\1'),
        ('<small>Full cast and crew for<br></small>', ''),
        ('<td> </td>', '<td>...</td>'),
        (_reRolesMovie, _manageRoles),
        (_reAkas, _replaceBR)]

    re_space = re.compile(r'\s+')
    re_airdate = re.compile(r'(.*)\s*\(season (\d+), episode (\d+)\)', re.I)
    re_votes = re.compile(r'([0-9][0-9]?\.[0-9])/10(\s+([0-9,]+)\s+votes)?',
                            re.I|re.M|re.S)
    def postprocess_data(self, data):
        # Convert section names.
        for sect in data.keys():
            if sect in _SECT_CONV:
                data[_SECT_CONV[sect]] = data[sect]
                del data[sect]
                sect = _SECT_CONV[sect]
        # Filter out fake values.
        for key in data:
            value = data[key]
            if isinstance(value, list) and value:
                if isinstance(value[0], Person):
                    data[key] = filter(lambda x: x.personID is not None, value)
                if isinstance(value[0], _Container):
                    for obj in data[key]:
                        obj.accessSystem = self._as
                        obj.modFunct = self._modFunct
        if 'akas' in data or 'other akas' in data:
            data['akas'] = data.get('other akas', []) + data.get('akas', [])
            if 'other akas' in data:
                del data['other akas']
        if 'runtimes' in data:
            data['runtimes'] = [x.replace(' min', u'')
                                for x in data['runtimes']]
        if 'production notes' in data:
            pn = data['production notes'].replace('\n\nComments:',
                                '\nComments:').replace('\n\nNote:',
                                '\nNote:').replace('Note:\n\n',
                                'Note:\n').split('\n')
            for k, v in zip(pn[::2], pn[1::2]):
                v = v.strip()
                if not v:
                    continue
                k = k.lower().strip(':')
                if k == 'note':
                    k = 'status note'
                data[k] = v
            del data['production notes']
        if 'original air date' in data:
            oid = self.re_space.sub(' ', data['original air date']).strip()
            data['original air date'] = oid
            aid = self.re_airdate.findall(oid)
            if aid and len(aid[0]) == 3:
                date, season, episode = aid[0]
                date = date.strip()
                try: season = int(season)
                except: pass
                try: episode = int(episode)
                except: pass
                if date and date != '????':
                    data['original air date'] = date
                else:
                    del data['original air date']
                # Handle also "episode 0".
                if season or type(season) is type(0):
                    data['season'] = season
                if episode or type(season) is type(0):
                    data['episode'] = episode
        for k in ('writer', 'director'):
            t_k = 'thin %s' % k
            if t_k not in data:
                continue
            if k not in data:
                data[k] = data[t_k]
            del data[t_k]
        if 'year' in data and data['year'] == '????':
            del data['year']
        if 'tv series link' in data:
            if 'tv series title' in data:
                data['episode of'] = Movie(title=data['tv series title'],
                                            movieID=analyze_imdbid(
                                                    data['tv series link']),
                                            accessSystem=self._as,
                                            modFunct=self._modFunct)
                del data['tv series title']
            del data['tv series link']
        rav = (data.get('votes and rating') or '').strip()
        if rav:
            del data['votes and rating']
            rg = self.re_votes.search(rav)
            if rg:
                try: rating = rg.group(1)
                except IndexError: rating = 'invalid'
                try:
                    rating = float(rating)
                    data['rating'] = rating
                except ValueError:
                    pass
                try: votes = rg.group(3)
                except IndexError: rating = 'invalid'
                votes = votes.replace(',', '')
                try:
                    votes = int(votes)
                    data['votes'] = votes
                except ValueError:
                    pass
        return data


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
    _defGetRefs = True

    def _init(self):
        self._plot_data = {}

    def _reset(self):
        """Reset the parser."""
        self._plot_data.clear()
        self._is_plot = 0
        self._stop_plot = 0
        self._plot = u''
        self._is_plot_writer = 0
        self._plot_writer = u''

    def get_data(self):
        """Return the dictionary with the 'plot' key."""
        return self._plot_data

    def start_p(self, attrs):
        pclass = self.get_attr_value(attrs, 'class')
        if pclass and pclass.lower() == 'plotpar':
            self._is_plot = 1
            self._stop_plot = 0

    def end_p(self):
        if not self._is_plot: return
        plot = self._plot.strip()
        writer = self._plot_writer.strip()
        if plot:
            # Replace funny email separators.
            writer = writer.replace('{', '<').replace('}', '>')
            txt = plot
            if writer:
                txt = writer + '::' + plot
            self._plot_data.setdefault('plot', []).append(txt)
            self._is_plot = 0
            self._plot_writer = u''
            self._plot = u''

    def start_a(self, attrs):
        if not self._is_plot: return
        link = self.get_attr_value(attrs, 'href')
        # The next data is the name of the author.
        if link and link.lower().startswith('/searchplotwriters'):
            self._is_plot_writer = 1
            self._stop_plot = 1

    def end_a(self):
        if self._is_plot_writer:
            self._is_plot_writer = 0

    def start_i(self, attrs):
        if self._is_plot:
            self._stop_plot = 1

    def end_i(self): pass

    def _handle_data(self, data):
        # Store text for plots and authors.
        if self._is_plot and not self._stop_plot:
            self._plot += data
        if self._is_plot_writer:
            self._plot_writer += data


class DOMHTMLPlotParser(DOMParserBase):
    """Parser for the "plot summary" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a 'plot' key, containing a list
    of string with the structure: 'summary_author <author@email>::summary'.

    Example:
        pparser = HTMLPlotParser()
        result = pparser.parse(plot_summary_html_string)
    """
    _defGetRefs = True

    extractors = [Extractor(label='plot',
                    path="//p[@class='plotpar']",
                    attrs=Attribute(key='plot',
                            multi=True,
                            path={'plot': './text()',
                                'author': './i/a/text()'},
                            postprocess=lambda x: u'%s::%s' % (
                            x.get('author').replace('{', '<').replace('}', '>'),
                            x.get('plot', '').strip())))]


class HTMLAwardsParser(ParserBase):
    """Parser for the "awards" page of a given person or movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        awparser = HTMLAwardsParser()
        result = awparser.parse(awards_html_string)
    """
    def _init(self):
        self._aw_data = []
        # Are we managing awards for a person or a movie?
        self.subject = 'title'

    def _reset(self):
        """Reset the parser."""
        self._aw_data = []
        self._is_big = 0
        self._is_small = 0
        self._is_current_assigner = 0
        self._begin_aw = 0
        self._in_td = 0
        self._cur_year = u''
        self._cur_result = u''
        self._cur_notes = u''
        self._cur_category = u''
        self._cur_forto = u''
        self._cur_assigner = u''
        self._cur_award = u''
        self._cur_sect = u''
        self._no = 0
        self._rowspan = 0
        self._counter = 1
        self._limit = 1
        self._is_tn = 0
        self._cur_id = u''
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
                 self._cur_result = u''
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
        self._cur_category = u''
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
                try: year = unicode(int(href[-4:]))
                except (ValueError, TypeError): year = None
                if year:
                    self._cur_sect = 'year'
                    self._cur_year = year
                    self._begin_aw = 1
                    self._counter = 1
                    self._limit = 1
                    self._no = 0
                    self._cur_result = u''
                    self._cur_notes = u''
                    self._cur_category = u''
                    self._cur_forto = u''
                    self._cur_award = u''
                    self._with = []
                    self._to = []
                    self._for = []
            if self._is_big:
                self._is_current_assigner = 1
                self._cur_assigner = u''
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
                                accessSystem=self._as,
                                modFunct=self._modFunct)
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
                                accessSystem=self._as,
                                modFunct=self._modFunct)
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
                                accessSystem=self._as,
                                modFunct=self._modFunct)
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
                                accessSystem=self._as,
                                modFunct=self._modFunct)
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


def _process_award(x):
    award = {}
    award['year'] = x.get('year').strip()
    award['result'] = x.get('result').strip()
    award['award'] = x.get('award').strip()
    category = x.get('category').strip()
    if category:
        award['category'] = category
    received_with = x.get('with')
    if received_with is not None:
        award['with'] = received_with.strip()
    notes = x.get('notes')
    if notes is not None:
        notes = notes.strip()
        if notes:
            award['notes'] = notes
    award['anchor'] = x.get('anchor')
    return award



class DOMHTMLAwardsParser(DOMParserBase):
    """Parser for the "awards" page of a given person or movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        awparser = HTMLAwardsParser()
        result = awparser.parse(awards_html_string)
    """
    subject = 'title'
    _fixRowSpans = True
    _containsObjects = True

    extractors = [
        Extractor(label='awards',
            group="//table//big",
            group_key="./a",
            path="./ancestor::tr[1]/following-sibling::tr/" \
                    "td[last()][not(@colspan)]",
            attrs=Attribute(key=None,
                multi=True,
                path={
                    'year': "../td[1]/a/text()",
                    'result': "../td[2]/b/text()",
                    'award': "../td[3]/text()",
                    'category': "./text()[1]",
                    # FIXME: takes only the first co-recipient
                    'with': "./small[starts-with(text()," \
                            " 'Shared with:')]/following-sibling::a[1]/text()",
                    'notes': "./small[last()]//text()",
                    'anchor': ".//text()"
                    },
                postprocess=lambda x: _process_award(x)
                )),
        Extractor(label='recipients',
            group="//table//big",
            group_key="./a",
            path="./ancestor::tr[1]/following-sibling::tr/" \
                    "td[last()]/small[1]/preceding-sibling::a",
            attrs=Attribute(key=None,
                multi=True,
                path={
                    'name': "./text()",
                    'link': "./@href",
                    'anchor': "..//text()"
                    }
                ))
    ]

    preprocessors = [
        (re.compile('(<tr><td[^>]*>.*?</td></tr>\n\n</table>)', re.I),
         r'\1</table>'),
        (re.compile('(<tr><td[^>]*>\n\n<big>.*?</big></td></tr>)', re.I),
         r'</table><table class="_imdbpy">\1'),
        (re.compile('(<table[^>]*>\n\n)</table>(<table)', re.I), r'\1\2'),
        (re.compile('(<small>.*?)<br>(.*?</small)', re.I), r'\1 \2'),
        (re.compile('(</tr>\n\n)(<td)', re.I), r'\1<tr>\2')
        ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        nd = []
        for key in data.keys():
            dom = self.get_dom(key)
            assigner = self.xpath(dom, "//a/text()")[0]
            for entry in data[key]:
                if not entry.has_key('name'):
                    # this is an award, not a recipient
                    entry['assigner'] = assigner.strip()
                    # find the recipients
                    matches = [p for p in data[key]
                               if p.has_key('name') and (entry['anchor'] ==
                                   p['anchor'])]
                    if self.subject == 'title':
                        recipients = [Person(name=recipient['name'],
                                    personID=analyze_imdbid(recipient['link']))
                                    for recipient in matches]
                        entry['to'] = recipients
                    elif self.subject == 'name':
                        recipients = [Movie(title=recipient['name'],
                                    movieID=analyze_imdbid(recipient['link']))
                                    for recipient in matches]
                        entry['for'] = recipients
                    nd.append(entry)
                del entry['anchor']
        return {'awards': nd}


class HTMLTaglinesParser(ParserBase):
    """Parser for the "taglines" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = HTMLTaglinesParser()
        result = tparser.parse(taglines_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._in_tl = 0
        self._in_h1 = 0
        self._in_tlu2 = 0
        self._tl = []
        self._ctl = u''
        self._seen_left_div = 0
        self._in_adv = False

    def get_data(self):
        """Return the dictionary."""
        self._tl[:] = [x.strip() for x in self._tl]
        self._tl[:] = filter(None, self._tl)
        if not self._tl: return {}
        return {'taglines': self._tl}

    def start_h1(self, attrs):
        self._in_h1 = 1

    def end_h1(self):
        self._in_h1 = 0
        if self._in_tlu2:
            self._in_tl = 1

    def _end_content(self):
        self._in_tl = 1

    def start_div(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.strip().lower() == 'left':
            self._seen_left_div = 1
        elif self.get_attr_value(attrs, 'id') == 'tn15adrhs':
            self._in_adv = True

    def end_div(self):
        if self._in_adv:
            self._in_adv = False

    def start_table(self, attrs): pass

    def end_table(self):
        self._ctl = u''

    def start_p(self, attrs): pass

    def end_p(self):
        if self._in_tl and self._ctl and not self._seen_left_div:
            self._tl.append(self._ctl.strip())
            self._ctl = u''

    def _handle_data(self, data):
        if self._in_tl and self._in_content and not self._in_adv:
            if data.strip().lower() != 'advertisement':
                self._ctl += data
        elif self._in_h1 and data.lower().find('taglines for') != -1:
            self._in_tlu2 = 1


class DOMHTMLTaglinesParser(DOMParserBase):
    """Parser for the "taglines" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = DOMHTMLTaglinesParser()
        result = tparser.parse(taglines_html_string)
    """
    extractors = [Extractor(label='taglines',
                            path="//div[@id='tn15content']/p",
                            attrs=Attribute(key='taglines', multi=True,
                                            path="./text()"))]


class HTMLKeywordsParser(ParserBase):
    """Parser for the "keywords" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        kwparser = HTMLKeywordsParser()
        result = kwparser.parse(keywords_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._in_kw = 0
        self._kw = []
        self._ckw = u''

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
            self._ckw = u''
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


class DOMHTMLKeywordsParser(DOMParserBase):
    """Parser for the "keywords" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        kwparser = DOMHTMLKeywordsParser()
        result = kwparser.parse(keywords_html_string)
    """
    extractors = [Extractor(label='keywords',
                            path="//a[starts-with(@href, '/keyword/')]",
                            attrs=Attribute(key='keywords',
                                            path="./text()", multi=True,
                                            postprocess=lambda x: \
                                                x.lower().replace(' ', '-')))]


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
    _defGetRefs = True

    def _init(self):
        self.kind = 'alternate versions'

    def _reset(self):
        """Reset the parser."""
        self._in_av = 0
        self._in_avd = 0
        self._av = []
        self._cav = u''
        self._stlist = []
        self._curst = {}
        self._cur_title = u''
        self._curinfo = u''

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
                self._cur_title = u''
                self._curinfo = u''
            else:
                self._av.append(self._cav.strip())
            self._in_avd = 0
            self._cav = u''

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
                self._cav = u''
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
                        self._curst[self._cur_title]['misc'] = u''
                    if self._curst[self._cur_title]['misc'] and \
                            self._curst[self._cur_title]['misc'][-1] != ' ':
                        self._curst[self._cur_title]['misc'] += ' '
                    self._curst[self._cur_title]['misc'] += self._cav
                self._cav = u''

    def _handle_data(self, data):
        if self._in_avd:
            self._cav += data


class DOMHTMLAlternateVersionsParser(DOMParserBase):
    """Parser for the "alternate versions" and "trivia" pages of a
    given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        avparser = HTMLAlternateVersionsParser()
        result = avparser.parse(alternateversions_html_string)
    """
    _defGetRefs = True
    kind = 'alternate versions'
    extractors = [Extractor(label='alternate versions',
                            path="//ul[@class='trivia']/li",
                            attrs=Attribute(key='self.kind',
                                            multi=True,
                                            path=".//text()",
                                            postprocess=lambda x: x.strip()))]


class DOMHTMLSoundtrackParser(DOMHTMLAlternateVersionsParser):
    kind = 'soundtrack'

    preprocessors = [
        ('<br>', '\n')
        ]

    def postprocess_data(self, data):
        if 'soundtrack' in data:
            nd = []
            for x in data['soundtrack']:
                ds = x.split('\n')
                title = ds[0]
                if title[0] == '"' and title[-1] == '"':
                    title = title[1:-1]
                nds = []
                newData = {}
                for l in ds[1:]:
                    if ' with ' in l or ' by ' in l or ' from ' in l \
                            or ' of ' in l or l.startswith('From '):
                        nds.append(l)
                    else:
                        if nds:
                            nds[-1] += l
                        else:
                            nds.append(l)
                newData[title] = {}
                for l in nds:
                    skip = False
                    for sep in ('From ',):
                        if l.startswith(sep):
                            fdix = len(sep)
                            kind = l[:fdix].rstrip().lower()
                            info = l[fdix:].lstrip()
                            newData[title][kind] = info
                            skip = True
                    if not skip:
                        for sep in ' with ', ' by ', ' from ', ' of ':
                            fdix = l.find(sep)
                            if fdix != -1:
                                fdix = fdix+len(sep)
                                kind = l[:fdix].rstrip().lower()
                                info = l[fdix:].lstrip()
                                newData[title][kind] = info
                                break
                nd.append(newData)
            data['soundtrack'] = nd
        return data


class HTMLCrazyCreditsParser(ParserBase):
    """Parser for the "crazy credits" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        ccparser = HTMLCrazyCreditsParser()
        result = ccparser.parse(crazycredits_html_string)
    """
    _defGetRefs = True

    def _reset(self):
        """Reset the parser."""
        self._cc = []
        self._in_cc = False
        self._ccc = u''

    def get_data(self):
        """Return the dictionary."""
        if not self._cc: return {}
        return {'crazy credits': self._cc}

    def start_ul(self, attrs):
        if self._in_content:
            self._in_cc = True

    def end_ul(self):
        self._in_cc = False

    def do_br(self, attrs):
        if not self._in_cc: return
        if self._ccc: self._ccc += u' '

    def start_li(self, attrs):
        self._ccc = u''

    def end_li(self):
        if not self._in_cc: return
        self._ccc = self._ccc.strip()
        if self._ccc:
            self._ccc = self._ccc.replace('\n', ' ').replace('  ', ' ')
            self._cc.append(self._ccc)
            self._ccc = u''

    def _handle_data(self, data):
        if self._in_cc:
            self._ccc += data


class DOMHTMLCrazyCreditsParser(DOMParserBase):
    """Parser for the "crazy credits" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        ccparser = DOMHTMLCrazyCreditsParser()
        result = ccparser.parse(crazycredits_html_string)
    """
    _defGetRefs = True

    extractors = [Extractor(label='crazy credits', path="//ul/li/tt",
                            attrs=Attribute(key='crazy credits', multi=True,
                                path=".//text()",
                                postprocess=lambda x: \
                                    x.replace('\n', ' ').replace('  ', ' ')))]


class HTMLGoofsParser(ParserBase):
    """Parser for the "goofs" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = HTMLGoofsParser()
        result = gparser.parse(goofs_html_string)
    """
    _defGetRefs = True

    def _reset(self):
        """Reset the parser."""
        self._in_go = 0
        self._in_go2 = 0
        self._go = []
        self._cgo = u''
        self._in_gok = 0
        self._cgok = u''

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
            self._cgo = u''
            self._cgok = u''

    def _handle_data(self, data):
        if self._in_gok:
            self._cgok += data
        elif self._in_go2:
            self._cgo += data


class DOMHTMLGoofsParser(DOMParserBase):
    """Parser for the "goofs" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = DOMHTMLGoofsParser()
        result = gparser.parse(goofs_html_string)
    """
    _defGetRefs = True

    extractors = [Extractor(label='goofs', path="//ul[@class='trivia']/li",
                    attrs=Attribute(key='goofs', multi=True, path=".//text()",
                            postprocess=lambda x: u'%s%s' % (x[0].lower(),
                                            x[1:].replace(': ', '::', 1))))]


class HTMLQuotesParser(ParserBase):
    """Parser for the "memorable quotes" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        qparser = HTMLQuotesParser()
        result = qparser.parse(quotes_html_string)
    """
    _defGetRefs = True

    def _reset(self):
        """Reset the parser."""
        self._in_quo2 = 0
        self._quo = []
        self._cquo = u''

    def get_data(self):
        """Return the dictionary."""
        if not self._quo: return {}
        quo = []
        for q in self._quo:
            if q.endswith('::'): q = q[:-2]
            quo.append(q)
        return {'quotes': quo}

    def start_a(self, attrs):
        if not self._in_content: return
        name = self.get_attr_value(attrs, 'name')
        if name and name.startswith('qt'):
            self._in_quo2 = 1

    def end_a(self): pass

    def start_h3(self, attrs):
        self._in_quo2 = 0
        self._cquo = u''

    def end_h3(self): pass

    def do_hr(self, attrs):
        if self._in_content and self._in_quo2 and self._cquo:
            self._cquo = self._cquo.strip()
            if self._cquo.endswith('::'):
                self._cquo = self._cquo[:-2]
            self._quo.append(self._cquo.strip())
            self._cquo = u''

    def start_div(self, attrs):
        if self._in_content and self._in_quo2:
            self.do_hr([])
            self._in_content = 0

    def end_div(self): pass

    def start_img(self, attrs):
        self._in_quo2 = 0

    def end_img(self): pass

    def do_br(self, attrs):
        if self._in_content and self._in_quo2 and self._cquo:
            self._cquo = '%s::' % self._cquo.strip()

    def _handle_data(self, data):
        if self._in_content and self._in_quo2:
            data = data.replace('\n', ' ')
            if self._cquo.endswith('::'):
                data = data.lstrip()
            self._cquo += data


class DOMHTMLQuotesParser(DOMParserBase):
    """Parser for the "memorable quotes" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        qparser = DOMHTMLQuotesParser()
        result = qparser.parse(quotes_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(label='quotes',
            path="//div[@class='_imdbpy']",
            attrs=Attribute(key='quotes',
                multi=True,
                path=".//text()",
                postprocess=lambda x: x.strip().replace(' \n',
                            '::').replace('::\n', '::').replace('\n', ' ')))
        ]

    preprocessors = [
        (re.compile('(<a name="?qt[0-9]{7}"?></a>)', re.I),
            r'\1<div class="_imdbpy">'),
        (re.compile('<hr width="30%">', re.I), '</div>'),
        (re.compile('<hr/>', re.I), '</div>'),
        ]


class HTMLReleaseinfoParser(ParserBase):
    """Parser for the "release dates" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rdparser = HTMLReleaseinfoParser()
        result = rdparser.parse(releaseinfo_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._in_rl = 0
        self._in_rl2 = 0
        self._rl = []
        self._crl = u''
        self._is_country = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._rl: return {}
        return {'release dates': self._rl}

    def start_th(self, attrs):
        if self.get_attr_value(attrs, 'class') == 'xxxx':
            self._in_rl = 1

    def end_th(self): pass

    def start_table(self, attrs): pass

    def end_table(self):
        self._in_rl = 0
        self._in_rl2 = 0

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
            self._crl = u''

    def _handle_data(self, data):
        if self._in_rl2:
            if self._crl and self._crl[-1] not in (' ', ':') \
                    and not data.isspace():
                self._crl += ' '
            self._crl += data.strip()


class DOMHTMLReleaseinfoParser(DOMParserBase):
    """Parser for the "release dates" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rdparser = DOMHTMLReleaseinfoParser()
        result = rdparser.parse(releaseinfo_html_string)
    """
    extractors = [Extractor(label='release dates',
                    path="//th[@class='xxxx']/../../tr",
                    attrs=Attribute(key='release dates', multi=True,
                        path={'country': ".//td[1]//text()",
                            'date': ".//td[2]//text()",
                            'notes': ".//td[3]//text()"}))]

    def postprocess_data(self, data):
        if not 'release dates' in data: return data
        rl = []
        for i in data['release dates']:
            country = i.get('country')
            date = i.get('date')
            if not (country and date): continue
            country = country.strip()
            date = date.strip()
            if not (country and date): continue
            notes = i['notes']
            info = u'%s::%s' % (country, date)
            if notes:
                info += notes
            rl.append(info)
        data['release dates'] = rl
        return data


class HTMLRatingsParser(ParserBase):
    """Parser for the "user ratings" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rparser = HTMLRatingsParser()
        result = rparser.parse(userratings_html_string)
    """
    re_means = re.compile('mean\s*=\s*([0-9]\.[0-9])\.\s*median\s*=\s*([0-9])',
                        re.I)

    def _reset(self):
        """Reset the parser."""
        self._in_t = 0
        self._in_total = 0
        self._in_b = 0
        self._cur_nr = u''
        self._in_cur_vote = 0
        self._cur_vote = u''
        self._in_weighted = 0
        self._weighted = None
        self._first = 0
        self._votes = {}
        self._rank = {}
        self._demo = {}
        self._in_p = 0
        self._in_demo = 0
        self._in_demo_t = 0
        self._cur_demo_t = u''
        self._cur_demo_av = u''
        self._next_is_demo_vote = 0
        self._next_demo_vote = u''
        self._in_td = 0

    def get_data(self):
        """Return the dictionary."""
        data = {}
        if self._votes:
            data['number of votes'] = self._votes
        if self._demo:
            data['demographic'] = self._demo
            tot_votes = self._demo.get('all votes')
            if tot_votes:
                data['votes'] = tot_votes[0]
        if self._weighted is not None:
            data['rating'] = self._weighted
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
                    n = int(self._cur_nr.replace(',', ''))
                    self._votes[c] = n
                except (ValueError, OverflowError): pass
                self._cur_nr = u''
                self._cur_vote = u''
        if self._in_demo:
            self._in_demo = 0
            try:
                av = float(self._cur_demo_av)
                dv = int(self._next_demo_vote.replace(',', ''))
                self._demo[self._cur_demo_t] = (dv, av)
            except (ValueError, OverflowError): pass
            self._cur_demo_av = u''
            self._next_demo_vote = u''
            self._cur_demo_t = u''

    def start_p(self, attrs):
        self._in_p = 1

    def end_p(self):
        self._in_p = 0

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if href:
            if href.startswith('ratings-'):
                self._in_demo = 1
                self._in_demo_t = 1
            elif href.startswith('/List?ratings='):
                self._in_weighted = 1

    def end_a(self):
        self._in_demo_t = 0
        self._in_weighted = 0

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
            if self._in_weighted:
                try:
                    # The 'weighted average' is the usual rating.
                    self._weighted = float(data.strip())
                except (ValueError, OverflowError):
                    pass
            elif sdata.startswith('Ranked #'):
                sd = sdata[8:]
                i = sd.find(' ')
                if i != -1:
                    sd = sd[:i]
                    try: sd = int(sd)
                    except (ValueError, OverflowError): pass
                    if type(sd) is type(0):
                        self._rank['top 250 rank'] = sd
            elif sdata.startswith('Arithmetic mean = '):
                means = self.re_means.findall(sdata)
                if means and len(means[0]) == 2:
                    am, med = means[0]
                    try: am = float(am)
                    except (ValueError, OverflowError): pass
                    if type(am) is type(1.0):
                        self._rank['arithmetic mean'] = am
                    try: med = int(med)
                    except (ValueError, OverflowError): pass
                    if type(med) is type(0):
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
        elif self._in_td and sdata.startswith('IMDb users'):
            self._in_demo = 1
            self._next_is_demo_vote = 1
            self._cur_demo_t = 'all votes'


class DOMHTMLRatingsParser(DOMParserBase):
    """Parser for the "user ratings" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rparser = DOMHTMLRatingsParser()
        result = rparser.parse(userratings_html_string)
    """
    re_means = re.compile('mean\s*=\s*([0-9]\.[0-9])\.\s*median\s*=\s*([0-9])',
                          re.I)
    extractors = [
        Extractor(label='number of votes',
            path="//td[b='Percentage']/../../tr",
            attrs=[Attribute(key='votes',
                            multi=True,
                            path={
                                'votes': "td[1]//text()",
                                'ordinal': "td[3]//text()"
                                })]),
        Extractor(label='mean and median',
            path="//p[starts-with(text(), 'Arithmetic mean')]",
            attrs=Attribute(key='mean and median',
                            path="text()")),
        Extractor(label='rating',
            path="//a[starts-with(@href, '/List?ratings=')]",
            attrs=Attribute(key='rating',
                            path="text()")),
        Extractor(label='demographic voters',
            path="//td[b='Average']/../../tr",
            attrs=Attribute(key='demographic voters',
                            multi=True,
                            path={
                                'voters': "td[1]//text()",
                                'votes': "td[2]//text()",
                                'average': "td[3]//text()"
                                })),
        Extractor(label='top 250',
            path="//a[text()='top 250']",
            attrs=Attribute(key='top 250',
                            path="./preceding-sibling::text()[1]"))
        ]

    def postprocess_data(self, data):
        nd = {}
        votes = data.get('votes', [])
        if votes:
            nd['number of votes'] = {}
            for i in xrange(1, 11):
                nd['number of votes'][int(votes[i]['ordinal'])] = \
                        int(votes[i]['votes'].replace(',', ''))
        mean = data.get('mean and median', '')
        if mean:
            means = self.re_means.findall(mean)
            if means and len(means[0]) == 2:
                am, med = means[0]
                try: am = float(am)
                except (ValueError, OverflowError): pass
                if type(am) is type(1.0):
                    nd['arithmetic mean'] = am
                try: med = int(med)
                except (ValueError, OverflowError): pass
                if type(med) is type(0):
                    nd['median'] = med
        if 'rating' in data:
            nd['rating'] = float(data['rating'])
        dem_voters = data.get('demographic voters')
        if dem_voters:
            nd['demographic'] = {}
            for i in xrange(1, len(dem_voters)):
                if (dem_voters[i]['votes'] is not None) \
                   and (dem_voters[i]['votes'].strip()):
                    nd['demographic'][dem_voters[i]['voters'].strip().lower()] \
                                = (int(dem_voters[i]['votes'].replace(',', '')),
                            float(dem_voters[i]['average']))
        if 'imdb users' in nd.get('demographic', {}):
            nd['votes'] = nd['demographic']['imdb users'][0]
            nd['demographic']['all votes'] = nd['demographic']['imdb users']
            del nd['demographic']['imdb users']
        top250 = data.get('top 250')
        if top250:
            sd = top250[9:]
            i = sd.find(' ')
            if i != -1:
                sd = sd[:i]
                try: sd = int(sd)
                except (ValueError, OverflowError): pass
                if type(sd) is type(0):
                    nd['top 250 rank'] = sd
        return nd


# XXX: way to difficult to fix.  Leave it broken.
class HTMLEpisodesRatings(ParserBase):
    """Parser for the "episode ratings ... by date" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        erparser = HTMLEpisodesRatings()
        result = erparser.parse(eprating_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._res = []
        self._cur_data = {}
        self._in_h4 = 0
        self._in_rating = 0
        self._cur_info = 'season.episode'
        self._cur_info_txt = u''
        self._cur_id = u''
        self._in_title = 0
        self._series_title = u''
        self._series_obj = None
        self._in_td = 0

    def get_data(self):
        """Return the dictionary."""
        if not self._res: return {}
        return {'episodes rating': self._res}

    def start_title(self, attrs):
        self._in_title = 1

    def end_title(self):
        self._in_title = 0
        self._series_title = self._series_title.strip()
        if self._series_title:
            self._series_obj = Movie(title=self._series_title,
                                    accessSystem=self._as,
                                    modFunct=self._modFunct)

    def start_h4(self, attrs):
        self._in_h4 = 1

    def end_h4(self):
        self._in_h4 = 0

    def start_table(self, attrs): pass

    def end_table(self): self._in_rating = 0

    def start_tr(self, attrs):
        if self._in_rating:
            self._cur_info = 'season.episode'
            self._cur_info_txt = u''

    def end_tr(self):
        if not self._in_rating: return
        if self._series_obj is None: return
        if self._cur_data and self._cur_id:
            ep_title = self._series_title
            ep_title += u' {%s' % self._cur_data['episode']
            if self._cur_data.has_key('season.episode'):
                ep_title += ' (#%s)' % self._cur_data['season.episode']
                del self._cur_data['season.episode']
            ep_title += '}'
            m = Movie(title=ep_title, movieID=self._cur_id,
                        accessSystem=self._as, modFunct=self._modFunct)
            m['episode of'] = self._series_obj
            self._cur_data['episode'] = m
            if self._cur_data.has_key('rating'):
                try:
                    self._cur_data['rating'] = float(self._cur_data['rating'])
                except ValueError:
                    pass
            if self._cur_data.has_key('votes'):
                try:
                    self._cur_data['votes'] = int(self._cur_data['votes'])
                except (ValueError, OverflowError):
                    pass
            self._res.append(self._cur_data)
        self._cur_data = {}
        self._cur_id = u''

    def start_td(self, attrs):
        self._in_td = 1

    def end_td(self):
        self._in_td = 0
        if not self._in_rating: return
        self._cur_info_txt = self._cur_info_txt.strip()
        if self._cur_info_txt:
            self._cur_data[self._cur_info] = self._cur_info_txt
        self._cur_info_txt = u''
        if self._cur_info == 'season.episode':
            self._cur_info = 'episode'
        elif self._cur_info == 'episode':
            self._cur_info = 'rating'
        elif self._cur_info == 'rating':
            self._cur_info = 'votes'
        elif self._cur_info == 'votes':
            self._cur_info = 'season.episode'

    def start_a(self, attrs):
        if not (self._in_rating and self._cur_info == 'episode'):
            return
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        curid = self.re_imdbID.findall(href)
        if not curid: return
        self._cur_id = curid[-1]

    def end_a(self): pass

    def _handle_data(self, data):
        if self._in_rating and self._in_td:
            self._cur_info_txt += data
        if self._in_h4 and data.strip().lower() == 'rated episodes':
            self._in_rating = 1
        if self._in_title:
            self._series_title += data


class DOMHTMLEpisodesRatings(DOMParserBase):
    """Parser for the "episode ratings ... by date" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        erparser = DOMHTMLEpisodesRatings()
        result = erparser.parse(eprating_html_string)
    """
    _containsObjects = True

    extractors = [Extractor(label='title', path="//title",
                            attrs=Attribute(key='title', path="./text()")),
                Extractor(label='ep ratings',
                        path="//th/../..//tr",
                        attrs=Attribute(key='episodes', multi=True,
                                path={'nr': ".//td[1]/text()",
                                        'ep title': ".//td[2]//text()",
                                        'movieID': ".//td[2]/a/@href",
                                        'rating': ".//td[3]/text()",
                                        'votes': ".//td[4]/text()"}))]

    def postprocess_data(self, data):
        if 'title' not in data or 'episodes' not in data: return data
        nd = []
        title = data['title']
        for i in data['episodes']:
            ept = i['ep title']
            movieID = analyze_imdbid(i['movieID'])
            votes = i['votes']
            rating = i['rating']
            if not (ept and movieID and votes and rating): continue
            votes = int(votes)
            rating = float(rating)
            ept = ept.strip()
            ept = u'%s {%s' % (title, ept)
            nr = i['nr']
            if nr:
                ept += u' (#%s)' % nr.strip()
            ept += '}'
            m = Movie(title=ept, movieID=movieID, accessSystem=self._as,
                        modFunct=self._modFunct)
            nd.append({'episode': m, 'votes': votes, 'rating': rating})
        return {'episodes rating': nd}



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
    def _init(self):
        self.kind = 'official sites'

    def _reset(self):
        """Reset the parser."""
        self._in_os2 = 0
        self._in_os3 = 0
        self._os = []
        self._cos = u''
        self._cosl = u''

    def get_data(self):
        """Return the dictionary."""
        if not self._os: return {}
        return {self.kind: self._os}

    def start_ol(self, attrs):
        if self._in_content:
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
            self._cosl = u''
            self._cos = u''

    def start_a(self, attrs):
        if self._in_os3:
            href = self.get_attr_value(attrs, 'href')
            if href:
                if not href.lower().startswith('http://'):
                    if href.startswith('/'): href = href[1:]
                    href = '%s%s' % (imdbURL_base, href)
                self._cosl = href

    def end_a(self): pass

    def _handle_data(self, data):
        if self._in_os3:
            self._cos += data


def _normalize_href(href):
    if (href is not None) and (not href.lower().startswith('http://')):
        if href.startswith('/'): href = href[1:]
        href = '%s%s' % (imdbURL_base, href)
    return href


class DOMHTMLOfficialsitesParser(DOMParserBase):
    """Parser for the "official sites", "external reviews", "newsgroup
    reviews", "miscellaneous links", "sound clips", "video clips" and
    "photographs" pages of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        osparser = DOMHTMLOfficialsitesParser()
        result = osparser.parse(officialsites_html_string)
    """
    kind = 'official sites'

    extractors = [
        Extractor(label='site',
            path="//ol/li/a",
            attrs=Attribute(key='self.kind',
                multi=True,
                path={
                    'link': "./@href",
                    'info': "./text()"
                },
                postprocess=lambda x: (x.get('info').strip(),
                            urllib.unquote(_normalize_href(x.get('link'))))))
        ]


class HTMLConnectionParser(ParserBase):
    """Parser for the "connections" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        connparser = HTMLConnectionParser()
        result = connparser.parse(connections_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._connections = {}
        self._in_conn_type = False
        self._conn_type = u''
        self._in_cur_title = False
        self._cur_title = u''
        self._cur_id = u''
        self._cur_note = u''
        self._seen_br = False
        self._stop = False

    def get_data(self):
        """Return the dictionary."""
        if not self._connections: return {}
        return {'connections': self._connections}

    def start_h5(self, attrs):
        if not self._in_content: return
        self._add_info()
        self._in_conn_type = True
        self._conn_type = u''

    def end_h5(self):
        self._conn_type = self._conn_type.strip().lower()
        self._in_conn_type = False

    def start_div(self, attrs): pass

    def end_div(self):
        if self._stop: return
        self._add_info()

    def do_img(self, attrs):
        src = self.get_attr_value(attrs, 'src')
        if src and src.find('header_relatedlinks') != -1:
            self._stop = True

    def start_a(self, attrs):
        if not self._in_content: return
        href = self.get_attr_value(attrs, 'href')
        self._add_info()
        if not href: return
        imdbID = self.re_imdbID.findall(href)
        if imdbID:
            self._cur_id = str(imdbID[0])
            self._in_cur_title = True

    def end_a(self): pass

    def do_hr(self, attrs):
        if self._connections:
            self._stop = True

    def do_br(self, attrs):
        if not self._in_content: return
        self._seen_br = True

    def _add_info(self):
        self._cur_title = self._cur_title.strip()
        self._cur_note = self._cur_note.strip()
        if self._cur_title and self._cur_id and self._conn_type:
            if self._cur_note and self._cur_note[0] == '-':
                self._cur_note = self._cur_note[1:].lstrip()
            m = Movie(movieID=str(self._cur_id), title=self._cur_title,
                                accessSystem=self._as, notes=self._cur_note,
                                modFunct=self._modFunct)
            self._connections.setdefault(self._conn_type, []).append(m)
            self._in_cur_title = False
        self._cur_title = u''
        self._cur_id = u''
        self._cur_note = u''
        self._seen_br = False
        self._in_cur_title = False

    def _handle_data(self, data):
        if not self._in_content: return
        if self._stop: return
        if self._in_conn_type:
            self._conn_type += data
        elif self._in_cur_title:
            if self._seen_br:
                self._cur_note += data
            else:
                self._cur_title += data


class DOMHTMLConnectionParser(DOMParserBase):
    """Parser for the "connections" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        connparser = DOMHTMLConnectionParser()
        result = connparser.parse(connections_html_string)
    """
    _containsObjects = True

    extractors = [Extractor(label='connection',
                    group="//div[@class='_imdbpy']",
                    group_key="./h5/text()",
                    group_key_normalize=lambda x: x.lower(),
                    path="./a",
                    attrs=Attribute(key=None,
                                    path={'title': "./text()",
                                            'movieID': "./@href"},
                                    multi=True))]

    preprocessors = [
        ('<h5>', '</div><div class="_imdbpy"><h5>'),
        # To get the movie's year.
        ('</a> (', ' ('),
        ('\n<br/>', '</a>'),
        ('<br/> - ', '::')
        ]

    def postprocess_data(self, data):
        for key in data.keys():
            nl = []
            for v in data[key]:
                title = v['title']
                ts = title.split('::', 1)
                title = ts[0].strip()
                notes = u''
                if len(ts) == 2:
                    notes = ts[1].strip()
                m = Movie(title=title,
                            movieID=analyze_imdbid(v['movieID']),
                            accessSystem=self._as, notes=notes,
                            modFunct=self._modFunct)
                nl.append(m)
            data[key] = nl
        if not data: return {}
        return {'connections': data}


class HTMLLocationsParser(ParserBase):
    """Parser for the "locations" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        lparser = HTMLLocationsParser()
        result = lparser.parse(locations_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._tc = {}
        self._dotc = 0
        self._indt = 0
        self._indd = 0
        self._cur_sect = u''
        self._curdata = [u'']
        self._cur_data = u''
        self._locations = []

    def get_data(self):
        """Return the dictionary."""
        rl = self._locations
        rl[:] = [x.replace(':: ', '::').replace(' ::', '::') for x in rl]
        if rl:
            return {'locations': rl}
        return {}

    def start_dl(self, attrs):
        self._dotc = 1

    def end_dl(self):
        self._dotc = 0
        self._cur_data = self._cur_data.strip().strip(':').strip()
        if self._cur_data:
            self._locations.append(self._cur_data)

    def start_dt(self, attrs):
        self._cur_data = self._cur_data.strip().strip(':').strip()
        if self._cur_data:
            self._locations.append(self._cur_data)
        self._cur_data = u''
        if self._dotc:
            self._indt = 1

    def end_dt(self):
        self._indt = 0

    def start_dd(self, attrs):
        if self._dotc: self._indd = 1
        self._cur_data = self._cur_data.strip()
        if self._cur_data:
            if self._cur_data[-2:] != '::':
                self._cur_data += '::'

    def end_dd(self): pass

    def do_br(self, attrs):
        if self._indd:
            self._cur_data = self._cur_data.strip()
            ##if self._cur_data and 0:
            ##    if self._cur_data[-2:] != '::':
            ##        self._cur_data += '::'
            self._curdata += [u'']

    def _handle_data(self, data):
        if self._indd or self._indt:
            self._cur_data += data


class DOMHTMLLocationsParser(DOMParserBase):
    """Parser for the "locations" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        lparser = DOMHTMLLocationsParser()
        result = lparser.parse(locations_html_string)
    """
    extractors = [Extractor(label='locations', path="//dt",
                    attrs=Attribute(key='locations', multi=True,
                                path={'place': ".//text()",
                                        'note': "./following-sibling::dd[1]" \
                                                "//text()"},
                                postprocess=lambda x: (u'%s::%s' % (
                                    x['place'].strip(),
                                    (x['note'] or u'').strip())).strip(':')))]



class HTMLTechParser(ParserBase):
    """Parser for the "technical", "business", "literature",
    "publicity" (for people) and "contacts (for people) pages of
    a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = HTMLTechParser()
        result = tparser.parse(technical_html_string)
    """
    def _init(self):
        self.kind = 'tech'

    def _reset(self):
        """Reset the parser."""
        self._tc = {}
        self._in_sect_title = 0
        self._in_data = 0
        self._cur_sect = u''
        self._curdata = [u'']
        self._stop_collecting = False

    def get_data(self):
        """Return the dictionary."""
        if self.kind in ('literature', 'business', 'contacts') and self._tc:
            return {self.kind: self._tc}
        return self._tc

    def _end_content(self):
        self._add_entry()

    def start_h3(self, attrs):
        self._stop_collecting = True

    def end_h3(self): pass

    def start_h5(self, attrs):
        if self._in_content:
            self._add_entry()
            self._in_sect_title = 1

    def end_h5(self):
        self._in_sect_title = 0
        self._in_data = 1

    def start_div(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls == 'left':
            self._stop_collecting = True
        elif self.get_attr_value(attrs, 'id') == 'bottom_center_wrapper':
            self._stop_collecting = True

    def end_div(self): pass

    def start_tr(self, attrs): pass

    def end_tr(self):
        if self._in_data and self.kind == 'publicity':
            if self._curdata:
                self.do_br([])

    def start_td(self, attrs): pass

    def end_td(self):
        if self._in_data and self._curdata and self.kind == 'publicity':
            if self._curdata[-1].find('::') == -1:
                self._curdata[-1] += '::'

    def start_p(self, attrs): pass

    def end_p(self):
        if self._in_data and self.kind == 'publicity':
            if self._curdata:
                self._curdata[-1] += '::'
                self.do_br([])

    def start_form(self, attrs):
        if self._in_data and self.kind == 'contacts':
            self._stop_collecting = True
            self._add_entry()

    def end_form(self): pass

    def _add_entry(self):
        self._curdata = [x.strip(':').strip() for x in self._curdata]
        self._curdata = filter(None, self._curdata)
        if self._cur_sect and self._curdata:
            self._tc[self._cur_sect] = self._curdata[:]
        self._curdata[:] = [u'']
        self._cur_sect = u''
        self._in_data = 0

    def do_br(self, attrs):
        if self._in_data:
            self._curdata += [u'']

    def _handle_data(self, data):
        if self._stop_collecting: return
        if self._in_data:
            self._curdata[-1] += data
        elif self._in_sect_title:
            data = data.lower()
            self._cur_sect += data


class DOMHTMLTechParser(DOMParserBase):
    """Parser for the "technical", "business", "literature",
    "publicity" (for people) and "contacts (for people) pages of
    a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        tparser = HTMLTechParser()
        result = tparser.parse(technical_html_string)
    """
    kind = 'tech'

    extractors = [Extractor(label='tech',
                        group="//h5",
                        group_key="./text()",
                        group_key_normalize=lambda x: x.lower(),
                        path="./following-sibling::div[1]",
                        attrs=Attribute(key=None,
                                    path=".//text()",
                                    postprocess=lambda x: [t.strip()
                                        for t in x.split('\n') if t.strip()]))]

    preprocessors = [
        (re.compile('(<h5>.*?</h5>)', re.I), r'\1<div class="_imdbpy">'),
        (re.compile('((<br/>|</p>|</table>))\n?<br/>(?!<a)', re.I),
            r'\1</div>'),
        # the ones below are for the publicity parser
        (re.compile('<p>(.*?)</p>', re.I), r'\1<br/>'),
        (re.compile('(</td><td valign="top">)', re.I), r'\1::'),
        (re.compile('(</tr><tr>)', re.I), r'\n\1'),
        # this is for splitting individual entries
        (re.compile('<br/>', re.I), r'\n'),
        ]

    def postprocess_data(self, data):
        for key in data:
            data[key] = filter(None, data[key])
        if self.kind in ('literature', 'business', 'contacts') and data:
            data = {self.kind: data}
        return data


class HTMLDvdParser(ParserBase):
    """Parser for the "dvd" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        dparser = HTMLDvdParser()
        result = dparser.parse(dvd_html_string)
    """
    _defGetRefs = True

    def _init(self):
        self._dvd = []

    def _reset(self):
        """Reset the parser."""
        self._cdvd = {}
        self._indvd = 0
        self._cur_sect = u''
        self._cur_data = u''
        self._insect = 0
        self._intitle = 0
        self._cur_title = u''
        self._seencover = 0

    def get_data(self):
        """Return the dictionary."""
        if self._dvd: return {'dvd': self._dvd}
        return {}

    def start_table(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls == 'dvd_section':
            self._indvd = 1
            self._seencover = 0
            self._processDataSet()

    def end_table(self):
        if self._indvd:
            self._processInfo()
        else:
            self._processDataSet()

    def do_hr(self, attrs):
        if not self._indvd: return
        self._processDataSet()

    def _processDataSet(self):
        self._processInfo()
        self._cur_title = self._cur_title.strip()
        if self._cdvd and self._cur_title:
            self._cdvd['title'] = self._cur_title
            self._dvd.append(self._cdvd)
            self._cdvd = {}
            self._cur_title = u''

    def _processInfo(self):
        self._cur_sect = self._cur_sect.replace(':', u'').strip().lower()
        self._cur_data = self._cur_data.strip()
        if self._cur_sect and self._cur_data:
            self._cdvd[self._cur_sect] = self._cur_data
        self._cur_sect = u''
        self._cur_data = u''

    def do_img(self, attrs):
        if not self._indvd: return
        alt = self.get_attr_value(attrs, 'alt')
        if alt and alt.startswith('Rating: '):
            rating = alt[8:].strip()
            if rating:
                self._cdvd['rating'] = rating
        elif alt and not self._seencover:
            self._seencover = 1
            src = self.get_attr_value(attrs, 'src')
            if src and src.find('noposter') == -1:
                if src[0] == '/':
                    src = '%s%s' % (imdbURL_base, src[1:])
                self._cdvd['cover'] = src

    def start_p(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls == 'data_contents':
            self._processInfo()
            self._insect = 1

    def end_p(self): pass

    def start_h3(self, attrs):
        if not self._indvd: return
        self._intitle = 1

    def end_h3(self): self._intitle = 0

    def start_b(self, attrs): pass

    def end_b(self): self._insect = 0

    def start_span(self, attrs):
        if not self._indvd: return
        cls = self.get_attr_value(attrs, 'class')
        if cls == 'expand_icon':
            self._processInfo()
            self._insect = 1

    def end_span(self): pass

    def start_div(self, attrs):
        if not self._indvd: return
        cls = self.get_attr_value(attrs, 'class')
        if cls in ('dvd_row_alt', 'dvd_row'):
            self._insect = 0
            if self._cur_data:
                self._cur_data += '::'
        elif cls == 'dvd_section':
            self._processInfo()
            self._insect = 1

    def end_div(self): pass

    def _handle_data(self, data):
        if not self._indvd: return
        if self._intitle:
            self._cur_title += data
        elif self._insect:
            self._cur_sect += data
        else:
            self._cur_data += data


class DOMHTMLDvdParser(DOMParserBase):
    """Parser for the "dvd" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        dparser = DOMHTMLDvdParser()
        result = dparser.parse(dvd_html_string)
    """
    _defGetRefs = True
    extractors = [Extractor(label='dvd',
            path="//div[@class='base_layer']",
            attrs=[Attribute(key=None,
                multi=True,
                path={
                    'title': "../table[1]//h3/text()",
                    'cover': "../table[1]//img/@src",
                    'region': ".//p[b='Region:']/text()",
                    'asin': ".//p[b='ASIN:']/text()",
                    'upc': ".//p[b='UPC:']/text()",
                    'rating': ".//p/b[starts-with(text(), 'Rating:')]/../img/@alt",
                    'certificate': ".//p[b='Certificate:']/text()",
                    'runtime': ".//p[b='Runtime:']/text()",
                    'label': ".//p[b='Label:']/text()",
                    'studio': ".//p[b='Studio:']/text()",
                    'release date': ".//p[b='Release Date:']/text()",
                    'dvd format': ".//p[b='DVD Format:']/text()",
                    'dvd features': ".//p[b='DVD Features: ']//text()",
                    'supplements': "..//div[span='Supplements']" \
                            "/following-sibling::div[1]//text()",
                    'review': "..//div[span='Review']/following-sibling::div[1]//text()",
                    'titles':  "..//div[starts-with(text(), 'Titles in this Product')]" \
                            "/..//text()",
                },
                postprocess=lambda x: {
                'title': (x.get('title') or u'').strip(),
                'cover': (x.get('cover') or u'').strip(),
                'region': (x.get('region') or u'').strip(),
                'asin': (x.get('asin') or u'').strip(),
                'upc': (x.get('upc') or u'').strip(),
                'rating': (x.get('rating') or u'Not Rated').strip().replace('Rating: ', ''),
                'certificate': (x.get('certificate') or u'').strip(),
                'runtime': (x.get('runtime') or u'').strip(),
                'label': (x.get('label') or u'').strip(),
                'studio': (x.get('studio') or u'').strip(),
                'release date': (x.get('release date') or u'').strip(),
                'dvd format': (x.get('dvd format') or u'').strip(),
                'dvd features': (x.get('dvd features') or u'').strip().replace('DVD Features: ', ''),
                'supplements': (x.get('supplements') or u'').strip(),
                'review': (x.get('review') or u'').strip(),
                'titles in this product': (x.get('titles') or u'').strip().replace('Titles in this Product::', ''),
                }
                 )])]

    preprocessors = [
        (re.compile('<p>(<table class="dvd_section" .*)</p>\s*<hr\s*/>', re.I),
         r'<div class="_imdbpy">\1</div>'),
        (re.compile('<p>(<div class\s*=\s*"base_layer")', re.I), r'\1'),
        (re.compile('</p>\s*<p>(<div class="dvd_section")', re.I), r'\1'),
        (re.compile('</div><div class="dvd_row(_alt)?">', re.I), r'::')
    ]

    def postprocess_data(self, data):
        if not data:
            return data
        dvds = data['dvd']
        for dvd in dvds:
            if dvd['cover'].find('noposter') != -1:
                del dvd['cover']
            for key in dvd.keys():
                if not dvd[key]:
                    del dvd[key]
        return data


class HTMLRecParser(ParserBase):
    """Parser for the "recommendations" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rparser = HTMLRecParser()
        result = rparser.parse(recommendations_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._rec = {}
        self._firsttd = 0
        self._curlist = u''
        self._curtitle = u''
        self._startgath = 0
        self._intable = 0
        self._inb = 0
        self._cur_id = u''
        self._no_more = 0

    def get_data(self):
        if not self._rec: return {}
        return {'recommendations': self._rec}

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if href and (href.find('RemoveRecommendations') != -1 or \
                    href == 'explanation'):
            self._no_more = 1
        if self._firsttd:
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
        if self._firsttd and not self._no_more:
            span = self.get_attr_value(attrs, 'colspan')
            if span: self._firsttd = 0
            if span == '6':
                self._no_more = True

    def end_td(self):
        if self._firsttd and not self._no_more:
            self._curtitle = self._curtitle.strip()
            if self._curtitle:
                if self._curlist:
                    if self._cur_id:
                        m = Movie(movieID=str(self._cur_id),
                                    title=self._curtitle,
                                    accessSystem=self._as,
                                    modFunct=self._modFunct)
                        self._rec.setdefault(self._curlist, []).append(m)
                        self._cur_id = u''
                self._curtitle = u''
            self._firsttd = 0

    def start_b(self, attrs):
        self._inb = 1

    def end_b(self):
        self._inb = 0

    def _handle_data(self, data):
        if self._no_more: return
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


class DOMHTMLRecParser(DOMParserBase):
    """Parser for the "recommendations" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        rparser = HTMLRecParser()
        result = rparser.parse(recommendations_html_string)
    """
    _containsObjects = True

    extractors = [Extractor(label='recommendations',
                    path="//td[@valign='middle'][1]",
                    attrs=Attribute(key='../../tr/td[1]//text()',
                            multi=True,
                            path={'title': ".//text()",
                                    'movieID': ".//a/@href"}))]
    def postprocess_data(self, data):
        for key in data.keys():
            n_key = key
            n_keyl = n_key.lower()
            if n_keyl == 'suggested by the database':
                n_key = 'database'
            elif n_keyl == 'imdb users recommend':
                n_key = 'users'
            data[n_key] = [Movie(title=x['title'],
                        movieID=analyze_imdbid(x['movieID']),
                        accessSystem=self._as, modFunct=self._modFunct)
                        for x in data[key]]
            del data[key]
        if data: return {'recommendations': data}
        return data


class HTMLNewsParser(ParserBase):
    """Parser for the "news" page of a given movie or person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        nwparser = HTMLNewsParser()
        result = nwparser.parse(news_html_string)
    """
    _defGetRefs = True

    def _reset(self):
        """Reset the parser."""
        self._cur_news = {}
        self._cur_text = u''
        self._cur_title = u''
        self._cur_link = u''
        self._cur_full_link = u''
        self._news = []
        self._in_h2 = False
        self._no_more = False
        self._seen_p = False

    def get_data(self):
        """Return the dictionary."""
        if not self._news: return {}
        return {'news': self._news}

    def start_h2(self, attrs):
        if not self._in_content: return
        self._in_h2 = True

    def end_h2(self):
        self._in_h2 = False

    def do_br(self, attrs):
        if not self._in_content: return
        if self._no_more: return
        self._cur_text += '\n'

    def do_hr(self, attrs):
        if not self._in_content: return
        self._cur_text = self._cur_text.strip()
        self._cur_title = self._cur_title.strip()
        if self._cur_title and self._cur_text:
            sepidx = self._cur_text.find('\n\n\n\n')
            if sepidx != -1:
                info = self._cur_text[:sepidx].rstrip().split('|')
                if len(info) == 3:
                    self._cur_news['from'] = info[1].replace('From ','').strip()
                    self._cur_news['date'] = info[0].strip()
                self._cur_text = self._cur_text[sepidx:].strip()
                if self._cur_text.endswith('(more)'):
                    self._cur_text = self._cur_text[:-6].rstrip()
            self._cur_news['title'] = self._cur_title
            self._cur_text = self._cur_text.replace('\n\n', '::::')
            self._cur_text = self._cur_text.replace('\n', ' ')
            self._cur_text = self._cur_text.replace('::::', '\n\n')
            self._cur_news['body'] = self._cur_text
            self._news.append(self._cur_news)
            if self._cur_link:
                self._cur_news['link'] = self._cur_link
        self._cur_title = u''
        self._cur_text = u''
        self._cur_link = u''
        self._cur_full_link = u''
        self._cur_news = {}
        self._no_more = False
        self._seen_p = False

    def start_p(self, attr):
        pass

    def end_p(self):
        if self._cur_text:
            if self._seen_p:
                self._no_more = True
                self._seen_p = False
            else:
                self._seen_p = True

    def start_a(self, attrs):
        if not self._in_content: return
        href = self.get_attr_value(attrs, 'href')
        if href:
            if href.startswith('/news/ni'):
                self._cur_link = '%s%s' % (imdbURL_base, href[1:])
            elif href.startswith('http://') and self._no_more:
                self._cur_full_link = href

    def end_a(self): pass

    def _add_full_link(self):
        if self._cur_full_link and self._news:
            self._news[-1]['full article link'] = self._cur_full_link
            self._cur_full_link = u''

    def _handle_data(self, data):
        if not self._in_content: return
        if self._in_h2:
            self._cur_title += data
        elif not self._no_more:
            self._cur_text += data
        else:
            if data.strip().lower().startswith('see full article at'):
                self._add_full_link()


class DOMHTMLNewsParser(DOMParserBase):
    """Parser for the "news" page of a given movie or person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        nwparser = DOMHTMLNewsParser()
        result = nwparser.parse(news_html_string)
    """
    _defGetRefs = True

    extractors = [
        Extractor(label='news',
            path="//h2",
            attrs=Attribute(key='news',
                multi=True,
                path={
                    'title': "./text()",
                    'fromdate': "../following-sibling::p[1]/small//text()",
                    'body': "../following-sibling::p[2]//text()",
                    'link': "../..//a[text()='Permalink']/@href",
                    'fulllink': "../..//a[starts-with(text(), " \
                            "'See full article at')]/@href"
                    },
                postprocess=lambda x: {
                    'title': x.get('title').strip(),
                    'date': x.get('fromdate').split('|')[0].strip(),
                    'from': x.get('fromdate').split('|')[1].replace('From ',
                            '').strip(),
                    'body': x.get('body').strip(),
                    'link': _normalize_href(x.get('link')),
                    'full article link': _normalize_href(x.get('fulllink'))
                }))
        ]

    preprocessors = [
        (re.compile('(<a name=[^>]+><h2>)', re.I), r'<div class="_imdbpy">\1'),
        (re.compile('(<hr/>)', re.I), r'</div>\1'),
        (re.compile('<p></p>', re.I), r'')
        ]

    def postprocess_data(self, data):
        if not data.has_key('news'):
            return {}
        for news in data['news']:
            if news.has_key('full article link'):
                if news['full article link'] is None:
                    del news['full article link']
        return data


class HTMLAmazonReviewsParser(ParserBase):
    """Parser for the "amazon reviews" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        arparser = HTMLAmazonReviewsParser()
        result = arparser.parse(amazonreviews_html_string)
    """
    def _reset(self):
        """Reset the parser."""
        self._in_amazonrev = 0
        self._inh3 = 0
        self._inreview = 0
        self._in_kind = 0
        self._reviews = []
        self._cur_title = u''
        self._cur_text = u''
        self._cur_link = u''
        self._cur_revkind = u''

    def get_data(self):
        """Return the dictionary."""
        if not self._reviews: return {}
        return {'amazon reviews': self._reviews}

    def start_table(self, attrs):
        self._in_amazonrev = 1

    def end_table(self):
        if self._inreview:
            self._add_info()
            self._cur_title = u''
            self._cur_link = u''
        self._in_amazonrev = 0
        self._inreview = 0

    def start_div(self, attrs):
        theid = self.get_attr_value(attrs, 'id')
        if theid and theid.find('content') != -1:
            self._in_amazonrev = 1

    def end_div(self):
        if self._in_amazonrev: self._in_amazonrev = 0

    def start_h3(self, attrs):
        self._inh3 = 1
        self._cur_link = u''
        self._cur_title = u''

    def end_h3(self):
        self._inh3 = 0

    def start_a(self, attrs):
        if self._inh3:
            href = self.get_attr_value(attrs, 'href')
            if href:
                if not href.startswith('http://'):
                    if href[0] == '/': href = href[1:]
                    href = '%s%s' % (imdbURL_base, href)
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
        self._cur_title = u''
        self._cur_link = u''

    def _add_info(self):
        self._cur_title = self._cur_title.replace('\n', ' ').strip()
        self._cur_text = self._cur_text.replace('\n', ' ').strip()
        self._cur_link = self._cur_link.strip()
        self._cur_revkind = self._cur_revkind.replace('\n', ' ').strip()
        entry = {}
        if not self._cur_text: return
        ai = self._cur_text.rfind(' --', -30)
        author = u''
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
        self._cur_text = u''
        self._cur_revkind = u''

    def _handle_data(self, data):
        if self._inreview:
            if self._in_kind:
                self._cur_revkind += data
            else:
                self._cur_text += data
        elif self._in_content and self._inh3:
            self._inreview = 1
            self._cur_title += data


def _parse_review(x):
    result = {}
    title = x.get('title').strip()
    if title[-1] == ':': title = title[:-1]
    result['title'] = title
    result['link'] = _normalize_href(x.get('link'))
    kind =  x.get('kind').strip()
    if kind[-1] == ':': kind = kind[:-1]
    result['review kind'] = kind
    text = x.get('review').replace('\n\n', '||').replace('\n', ' ').split('||')
    review = '\n'.join(text)
    if x.get('author') is not None:
        author = x.get('author').strip()
        review = review.split(author)[0].strip()
        result['review author'] = author[2:]
    if x.get('item') is not None:
        item = x.get('item').strip()
        review = review[len(item):].strip()
        review = "%s::%s" % (item, review)
    result['review'] = review
    return result


class DOMHTMLAmazonReviewsParser(DOMParserBase):
    """Parser for the "amazon reviews" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        arparser = DOMHTMLAmazonReviewsParser()
        result = arparser.parse(amazonreviews_html_string)
    """
    extractors = [
        Extractor(label='amazon reviews',
            group="//h3",
            group_key="./a/text()",
            group_key_normalize=lambda x: x[:-1],
            path="./following-sibling::p[1]/span[@class='_review']",
            attrs=Attribute(key=None,
                multi=True,
                path={
                    'title': "../preceding-sibling::h3[1]/a[1]/text()",
                    'link': "../preceding-sibling::h3[1]/a[1]/@href",
                    'kind': "./preceding-sibling::b[1]/text()",
                    'item': "./i/b/text()",
                    'review': ".//text()",
                    'author': "./i[starts-with(text(), '--')]/text()"
                    },
                postprocess=lambda x: _parse_review(x)))
        ]

    preprocessors = [
        (re.compile('<p>\n(?!<b>)', re.I), r'\n'),
        (re.compile('(\n</b>\n)', re.I), r'\1<span class="_review">'),
        (re.compile('(</p>\n\n)', re.I), r'</span>\1'),
        (re.compile('(\s\n)(<i><b>)', re.I), r'</span>\1<span class="_review">\2')
        ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        nd = []
        for item in data.keys():
            nd = nd + data[item]
        return {'amazon reviews': nd}

class HTMLSalesParser(ParserBase):
    """Parser for the "merchandising links" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = HTMLSalesParser()
        result = sparser.parse(sales_html_string)
    """
    # XXX: crap!  This parser must be rewritten from scratch.
    def _reset(self):
        self._sales = {}
        self._cur_type = u''
        self._cur_info = {}
        self._in_h5 = 0
        self._in_dt = 0
        self._get_img = 0
        self._get_link = 0
        self._cur_descr = u''
        self._get_descr = 0
        self._in_a = 0
        self._in_dd = 0
        self._cur_link_text = u''
        self._in_table = 0
        self._seen_br = 0
        self._in_layer = 0
        self._ignore_tr = 0

    def get_data(self):
        if not self._sales: return {}
        return {'merchandising links': self._sales}

    def _add_entry(self):
        self._cur_type = self._cur_type.strip()
        ln = self._cur_info.get('link')
        descr = self._cur_descr.strip()
        if self._cur_type and ln and descr and ln[0] != '#':
            self._cur_info['description'] = descr.replace('\n', '::')
            self._sales.setdefault(self._cur_type,
                                    []).append(self._cur_info)
            self._cur_info = {}
            self._cur_descr = u''

    def start_h5(self, attrs):
        self._in_h5 = 1
        if not self._in_table: self._get_link = 1
        self._add_entry()
        self._get_descr = 1
        self._cur_type = u''
        self._seen_br = 0

    def end_h5(self):
        if self._in_h5:
            self._in_h5 = 0

    def start_table(self, attrs):
        self._in_table = 1

    def end_table(self):
        self._in_table = 0

    def start_td(self, attrs):
        if self._ignore_tr: return
        cls = self.get_attr_value(attrs, 'class')
        if cls:
            clsl = cls.lower()
            if clsl == 'w_rowtable_colcover':
                self._get_img = 1
            elif clsl in ('w_rowtable_colshop', 'w_rowtable_coldetails'):
                self._get_descr = 1
                self._cur_descr = u''

    def end_td(self):
        self._get_descr = 0

    def start_layer(self, attrs):
        self._in_layer = 1

    def end_layer(self):
        self._in_layer = 0

    def do_hr(self, attrs):
        self._in_layer = 0

    def do_img(self, attrs):
        if self._get_descr and (self._cur_type and self._in_table == 0
                                and not self._in_a) and self._cur_descr.strip():
            self._add_entry()
            self._cur_descr = u''
            self._get_link = 1
            return

        if self._get_img:
            self._get_img = 0
            src = self.get_attr_value(attrs, 'src')
            if src: self._cur_info['cover'] = src
        if self._get_descr:
            alttxt = self.get_attr_value(attrs, 'alt')
            if alttxt:
                self._cur_link_text = alttxt

    def start_tr(self, attrs):
        if self.get_attr_value(attrs, 'class') == 'w_rowtable_head':
            self._ignore_tr = 1

    def end_tr(self):
        if self._ignore_tr:
            self._ignore_tr = 0
            return
        self._cur_descr = self._cur_descr.strip()
        if self._cur_descr:
            self._cur_info['description'] = self._cur_descr
        self._cur_descr = u''
        self._cur_link_text = self._cur_link_text.strip()
        if self._cur_link_text:
            self._cur_info['link-text'] = self._cur_link_text
        self._cur_link_text = u''
        ln = self._cur_info.get('link', u'')
        if ln[0:1] == '#':
            if self._cur_info.has_key('description'):
                del self._cur_info['description']
        if self._cur_info and ln[0:1] != '#':
            self._sales.setdefault(self._cur_type,
                                    []).append(self._cur_info)
            self._cur_info = {}

    def start_dt(self, attrs):
        self._in_dt = 1
        self._cur_type = u''

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
                    href = href[1:]
                href = '%s%s' % (imdbURL_base, href)
                self._cur_info['link'] = href
                self._get_link = 0

    def end_a(self):
        self._in_a = 0

    def _handle_data(self, data):
        if not self._in_layer: return
        if self._in_h5 or self._in_dt:
            self._cur_type += data.lower()
        elif self._get_descr or (self._cur_type and self._in_table == 0
                                and not self._in_a):
            self._cur_descr += data


def _parse_merchandising_link(x):
    result = {}
    link = x.get('link')
    result['link'] = _normalize_href(link)
    text = x.get('text')
    if text is not None:
        result['link-text'] = text.strip()
    cover = x.get('cover')
    if cover is not None:
        result['cover'] = cover
    description = x.get('description')
    if description is not None:
        shop = x.get('shop')
        if shop is not None:
            result['description'] = u'%s::%s' % (shop, description.strip())
        else:
            result['description'] = description.strip()
    return result


class DOMHTMLSalesParser(DOMParserBase):
    """Parser for the "merchandising links" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = DOMHTMLSalesParser()
        result = sparser.parse(sales_html_string)
    """
    extractors = [
        Extractor(label='shops',
                    group="//h5/a[@name]/..",
                    group_key="./a[1]/text()",
                    group_key_normalize=lambda x: x.lower(),
                    path=".//following-sibling::table[1]/" \
                            "/td[@class='w_rowtable_colshop']//tr[1]",
                    attrs=Attribute(key=None,
                        multi=True,
                        path={
                            'link': "./td[2]/a[1]/@href",
                            'text': "./td[1]/img[1]/@alt",
                            'cover': "./ancestor::td[1]/../td[1]"\
                                    "/a[1]/img[1]/@src",
                            },
                        postprocess=lambda x: _parse_merchandising_link(x))),
        Extractor(label='others',
                    group="//span[@class='_info']/..",
                    group_key="./h5/a[1]/text()",
                    group_key_normalize=lambda x: x.lower(),
                    path="./span[@class='_info']",
                    attrs=Attribute(key=None,
                        multi=True,
                        path={
                            'link': "./preceding-sibling::a[1]/@href",
                            'shop': "./preceding-sibling::a[1]/text()",
                            'description': ".//text()",
                            },
                        postprocess=lambda x: _parse_merchandising_link(x)))
    ]

    preprocessors = [
        (re.compile('(<h5><a name=)', re.I), r'</div><div class="_imdbpy">\1'),
        (re.compile('(</h5>\n<br/>\n)</div>', re.I), r'\1'),
        (re.compile('(<br/><br/>\n)(\n)', re.I), r'\1</div>\2'),
        (re.compile('(\n)(Search.*?)(</a>)(\n)', re.I), r'\3\1\2\4'),
        (re.compile('(\n)(Search.*?)(\n)', re.I),
            r'\1<span class="_info">\2</span>\3')
        ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        return {'merchandising links': data}


class HTMLEpisodesParser(ParserBase):
    """Parser for the "episode list" and "episodes cast" pages of
    a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        eparser = HTMLEpisodesParser()
        result = eparser.parse(episodes_html_string)
    """
    def _reset(self):
        self._in_html_title = 0
        self._series = None
        self._series_id = None
        self._html_title = u''
        self._episodes = {}
        self._in_h1 = 0
        self._in_h3 = 0
        self._in_h4 = 0
        self._cur_season = 0
        self._eps_counter = 1
        self._in_episodes = 0
        self._cur_year = u'????'
        self._cur_id = u''
        self._in_eps_title = 0
        self._eps_number = u''
        self._eps_title = u''
        self._next_is_oad = 0
        self._in_oad = 0
        self._oad = u''
        self._in_plot = 0
        self._never_again_in_plot = 0
        self._plot = u''
        self._in_cast = 0
        self._cast = []
        self._cur_person = u''
        self._cur_person_id = None

    def get_data(self):
        if self._episodes: return {'episodes': self._episodes}
        else: return {}

    def start_title(self, attrs):
        self._in_html_title = 1

    def end_title(self):
        self._in_html_title = 0
        title = self._html_title.replace('- Episode list', u'').strip()
        title = title.replace('- Episodes cast', u'').strip()
        if title:
            self._series = Movie(title=title,
                                accessSystem=self._as,
                                modFunct=self._modFunct)
        self._html_title = u''

    def start_h1(self, attrs):
        self._in_h1 = 1

    def end_h1(self):
        self._in_h1 = 0

    def start_h3(self, attrs):
        self._in_h3 = 1

    def end_h3(self):
        self._in_h3 = 0

    start_h4 = start_h3
    end_h4 = end_h3

    def _add_episode(self):
        self._eps_title = self._eps_title.strip()
        if not (self._eps_title and self._cur_id):
            self._eps_title = u''
            return
        epnidx = self._eps_number.find('Episode ')
        if epnidx != -1:
            self._eps_number = self._eps_number[epnidx+8:]
            self._eps_number = self._eps_number.strip().strip(':').strip()
            try: self._eps_number = int(self._eps_number)
            except: pass
        else:
            self._eps_number = max(self._episodes.get(self._cur_season,
                                    {-1: None}).keys()) + 1
        eps = Movie(movieID=self._cur_id, title=self._eps_title,
                    accessSystem=self._as, modFunct=self._modFunct)
        eps['year'] = self._cur_year
        eps['kind'] = u'episode'
        eps['season'] = self._cur_season
        eps['episode'] = self._eps_number
        eps['episode of'] = self._series
        self._oad = self._oad.strip()
        if self._oad.lower().startswith('original air date:'):
            self._oad = self._oad[18:].lstrip()
        if self._oad and self._oad != '????':
            eps['original air date'] = self._oad
        self._plot = self._plot.strip()
        if self._plot:
            eps['plot'] = self._plot
        if not self._episodes.has_key(self._cur_season):
            self._episodes[self._cur_season] = {}
        if self._cast:
            eps['cast'] = self._cast
            self._cast = []
        self._episodes[self._cur_season][self._eps_number] = eps
        self._eps_title = u''
        self._eps_number = u''
        self._cur_id = u''
        self._cur_year = u'????'
        self._oad = u''
        self._in_plot = 0
        self._never_again_in_plot = 0
        self._plot = u''

    def start_a(self, attrs):
        if self._in_h1:
            href = self.get_attr_value(attrs, 'href')
            if href and href.startswith('/title/tt'):
                curid = self.re_imdbID.findall(href)
                if curid:
                    self._series_id = curid[0]
                    if self._series:
                        self._series.movieID = str(self._series_id)
        elif self._in_h3:
            self._add_episode()
            name = self.get_attr_value(attrs, 'name')
            if name and name.lower().startswith('season-'):
                self._eps_counter = 0
                cs = name[7:]
                try: cs = int(cs)
                except: pass
                self._cur_season = cs
            self._eps_counter += 1
            self._in_episodes = 1
            self._in_eps_title = 1
        if self._in_episodes:
            name = self.get_attr_value(attrs, 'class')
            if name and name.lower().startswith('filter-all filter-year-'):
                self._add_episode()
                year = name[23:]
                if year == 'unknown': year = u'????'
                self._cur_year = year
            href = self.get_attr_value(attrs, 'href')
            if href and href.lower().startswith('/title/tt'):
                curid = self.re_imdbID.findall(href)
                if curid:
                    self._cur_id = curid[0]
                    self._in_eps_title = 1
            elif href and href.lower().startswith('/name/nm'):
                curid = self.re_imdbID.findall(href)
                if curid:
                    self._cur_person_id = curid[0]

    def end_a(self):
        if self._in_eps_title: self._in_eps_title = 0

    def start_b(self, attrs):
        if self._next_is_oad:
            self._in_oad = 1

    def end_b(self):
        if self._in_oad:
            self._next_is_oad = 0
            self._in_oad = 0

    def start_div(self, attrs):
        if self._in_episodes: self._add_episode()
        #self._in_episodes = 0

    def end_div(self): pass

    def do_br(self, attrs):
        if not self._in_episodes: return
        if not self._never_again_in_plot:
            self._in_plot = 1
            self._never_again_in_plot = 1

    def start_table(self, attrs):
        if not self._in_episodes: return
        if self._in_plot: self._in_plot = 0

    def end_table(self): pass

    def start_tr(self, attrs):
        self._in_cast = 1

    def end_tr(self):
        if not self._in_cast: return
        self._in_cast = 0
        name = self._cur_person.strip()
        if name and self._cur_person_id:
            note = u''
            bni = name.find('(')
            if bni != -1:
                eni = name.rfind(')')
                if eni != -1:
                    note = name[bni:]
                    name = name[:bni].strip()
            sn = name.split(' ... ')
            name = sn[0]
            role = ' '.join(sn[1:]).strip()
            p = Person(name=name, personID=str(self._cur_person_id),
                        currentRole=role, accessSystem=self._as,
                        notes=note, billingPos=len(self._cast)+1,
                        modFunct=self._modFunct)
            self._cast.append(p)
        self._cur_person = u''
        self._cur_person_id = None

    def start_td(self, attrs):
        if not self._in_episodes: return
        if self.get_attr_value(attrs, 'width'):
            self._add_episode()
            self._in_episodes = 0

    def _handle_data(self, data):
        if self._in_h1:
            sldata = data.strip().lower()
            if sldata.startswith('episodes'):
                self._in_episodes_h1 = 1
        elif self._in_html_title:
            self._html_title += data
        elif self._in_eps_title:
            self._eps_title += data
        elif self._in_h4:
            self._eps_number += data
        elif self._in_oad:
            self._oad += data
        elif self._in_plot:
            self._plot += data
        elif self._in_cast:
            self._cur_person += data


def _build_episode(x):
    """Create a Movie object for a given series' episode."""
    episode_id = analyze_imdbid(x.get('link'))
    episode_title = x.get('title')
    e = Movie(movieID=episode_id, title=episode_title)
    e['kind'] = u'episode'
    year = x.get('year')
    if year is not None:
        year = year[5:]
        if year == 'unknown': year = u'????'
        e['year'] = year
    epinfo = x.get('episode')
    if epinfo is not None:
        season, episode = epinfo.split(':')[0].split(',')
        e['season'] = int(season[7:])
        e['episode'] = int(episode[8:])
    else:
        e['season'] = 'unknown'
        e['episode'] = 'unknown'
    plot = x.get('plot')
    if plot:
        e['plot'] = plot.strip()
    oad = x.get('oad')
    if oad:
        e['original air date'] = oad.strip()
    return e


class DOMHTMLEpisodesParser(DOMParserBase):
    """Parser for the "episode list" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        eparser = DOMHTMLEpisodesParser()
        result = eparser.parse(episodes_html_string)
    """
    _containsObjects = True

    kind = 'episodes list'
    _episodes_path = "..//h4"
    _oad_path = "./following-sibling::span/strong[1]/text()"

    def _init(self):
        self.extractors = [
            Extractor(label='series',
                path="//html",
                attrs=[Attribute(key='series title',
                                path=".//title/text()"),
                        Attribute(key='series movieID',
                                path=".//h1/a[@class='main']/@href",
                                postprocess=lambda x: analyze_imdbid(x))
                    ]),
            Extractor(label='episodes',
                group="//div[@class='_imdbpy']/h3",
                group_key="./a/@name",
                path=self._episodes_path,
                attrs=Attribute(key=None,
                    multi=True,
                    path={
                        'link': "./a/@href",
                        'title': "./a/text()",
                        'year': "./preceding-sibling::a[1]/@name",
                        'episode': "./text()[1]",
                        'oad': self._oad_path,
                        'plot': "./following-sibling::text()[1]"
                    },
                    postprocess=lambda x: _build_episode(x)))]
        if self.kind == 'episodes cast':
            self.extractors += [
                Extractor(label='cast',
                    group="//h4",
                    group_key="./text()[1]",
                    group_key_normalize=lambda x: x.strip(),
                    path="./following-sibling::table[1]//td[@class='nm']",
                    attrs=Attribute(key=None,
                        multi=True,
                        path={'person': "..//text()",
                            'link': "./a/@href",
                            'roleID': \
                                "../td[4]/div[@class='_imdbpyrole']/@roleid"},
                        postprocess=lambda x: \
                                build_person(x.get('person') or u'',
                                personID=analyze_imdbid(x.get('link')),
                                roleID=(x.get('roleID') or u'').split('/'),
                                accessSystem=self._as,
                                modFunct=self._modFunct)))
                ]

    preprocessors = [
        (re.compile('(<hr/>\n)(<h3>)', re.I),
                    r'</div>\1<div class="_imdbpy">\2'),
        (re.compile('(</p>\n\n)</div>', re.I), r'\1'),
        (re.compile('<h3>(.*?)</h3>', re.I), r'<h4>\1</h4>'),
        (_reRolesMovie, _manageRoles),
        (re.compile('(<br/> <br/>\n)(<hr/>)', re.I), r'\1</div>\2')
        ]

    def postprocess_data(self, data):
        # A bit extreme?
        if not 'series title' in data: return {}
        if not 'series movieID' in data: return {}
        stitle = data['series title'].replace('- Episode list', '')
        stitle = stitle.replace('- Episodes list', '')
        stitle = stitle.replace('- Episode cast', '')
        stitle = stitle.replace('- Episodes cast', '')
        stitle = stitle.strip()
        if not stitle: return {}
        seriesID = data['series movieID']
        if seriesID is None: return {}
        series = Movie(title=stitle, movieID=str(seriesID),
                        accessSystem=self._as, modFunct=self._modFunct)
        nd = {}
        for key in data.keys():
            if key.startswith('season-'):
                season_key = key[7:]
                try: season_key = int(season_key)
                except: pass
                nd[season_key] = {}
                for episode in data[key]:
                    if not episode: continue
                    episode_key = episode.get('episode')
                    if episode_key is None: continue
                    cast_key = 'Season %s, Episode %s:' % (season_key,
                                                            episode_key)
                    if data.has_key(cast_key):
                        cast = data[cast_key]
                        for i in xrange(len(cast)):
                            cast[i].billingPos = i + 1
                        episode['cast'] = cast
                    episode['episode of'] = series
                    nd[season_key][episode_key] = episode
        if len(nd) == 0:
            return {}
        return {'episodes': nd}


class DOMHTMLEpisodesCastParser(DOMHTMLEpisodesParser):
    """Parser for the "episodes cast" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        eparser = DOMHTMLEpisodesParser()
        result = eparser.parse(episodes_html_string)
    """
    kind = 'episodes cast'
    _episodes_path = "..//h4"
    _oad_path = "./following-sibling::b[1]/text()"


class HTMLFaqsParser(ParserBase):
    """Parser for the "FAQ" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        fparser = HTMLFaqsParser()
        result = fparser.parse(faqs_html_string)
    """
    _defGetRefs = True

    def _reset(self):
        self._faqs = []
        self._in_wiki_cont = 0
        self._in_question = 0
        self._in_answer = 0
        self._question = u''
        self._answer = u''
        self._in_spoiler = 0
        self._in_pre = 0

    def get_data(self):
        if not self._faqs: return {}
        return {'faqs': self._faqs}

    def start_pre(self, attrs): self._in_pre = 1

    def end_pre(self): self._in_pre = 0

    def start_ul(self, attrs):
        self._in_wiki_cont = 0
        self._question = u''
        self._answer = u''
        self._in_question = 0
        self._in_answer = 0

    def end_ul(self): pass

    def start_div(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.strip().lower() == 'section':
            self._in_wiki_cont = 1
            self._in_question = 1
            self._in_answer = 0

    def end_div(self):
        if not self._in_wiki_cont: return
        self._question = self._question.strip()
        self._answer = self._answer.strip()
        if self._question and self._answer:
            self._faqs.append('%s::%s' % (self._question, self._answer))
            self._in_wiki_cont = 0
            self._in_question = 0
            self._in_answer = 0
            self._question = u''
            self._answer = u''

    def start_h3(self, attrs):
        if not self._in_wiki_cont: return
        self._in_question = 1

    def end_h3(self):
        if not self._in_wiki_cont: return
        self._in_question = 0
        self._in_answer = 1

    def do_br(self, attrs):
        if self._in_answer and self._answer:
            self._answer += '\n'

    def start_span(self, attrs):
        if not self._in_wiki_cont: return
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.strip().lower():
            self._in_spoiler = 1
        else:
            return
        if self._in_answer:
            self._answer += '[spoiler]'
        elif self._in_question:
            self._question += '[spoiler]'

    def end_span(self):
        if not self._in_spoiler: return
        self._in_spoiler = 0
        if self._in_answer:
            self._answer += '[/spoiler]'
        elif self._in_question:
            self._question += '[/spoiler]'

    def _handle_data(self, data):
        if not self._in_wiki_cont: return
        if self._in_answer:
            if not self._in_pre: data = data.replace('\n', ' ')
            self._answer += data
        elif self._in_question:
            self._question += data


class DOMHTMLFaqsParser(DOMParserBase):
    """Parser for the "FAQ" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        fparser = DOMHTMLFaqsParser()
        result = fparser.parse(faqs_html_string)
    """
    _defGetRefs = True

    # XXX: bsoup and lxml don't match (looks like a minor issue, anyway).

    extractors = [
        Extractor(label='faqs',
            path="//div[@class='section']",
            attrs=Attribute(key='faqs',
                multi=True,
                path={
                    'question': "./h3/a/span/text()",
                    'answer': "../following-sibling::div[1]//text()"
                },
                postprocess=lambda x: u'%s::%s' % (x.get('question').strip(),
                                    '\n\n'.join(x.get('answer').replace(
                                        '\n\n', '\n').strip().split('||')))))
        ]

    preprocessors = [
        (re.compile('<br/><br/>', re.I), r'||'),
        (re.compile('<h4>(.*?)</h4>\n', re.I), r'||\1--'),
        (re.compile('<span class="spoiler"><span>(.*?)</span></span>', re.I),
         r'[spoiler]\1[/spoiler]')
        ]


class HTMLAiringParser(ParserBase):
    """Parser for the "airing" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        aparser = HTMLAiringParser()
        result = aparser.parse(airing_html_string)
    """
    def _reset(self):
        self._air = []
        self._in_air_info = 0
        self._in_ch = 0
        self._cur_info = 'date'
        self._cur_data = {}
        self._cur_txt = u''
        self._in_html_title = 0
        self._title = u''
        self._title_kind = u''
        self._cur_id = u''

    def get_data(self):
        if not self._air: return {}
        return {'airing': self._air}

    def start_title(self, attrs): self._in_html_title = 1

    def end_title(self):
        self._in_html_title = 0
        self._title = self._title.strip()
        self._title_kind = analyze_title(self._title, canonical=1)['kind']

    def start_a(self, attrs):
        href = self.get_attr_value(attrs, 'href')
        if not href: return
        ids = self.re_imdbID.findall(href)
        if ids:
            self._cur_id = ids[-1]

    def end_a(self): pass

    def start_b(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if cls and cls.strip().lower() == 'ch':
            self._in_ch = 1

    def end_b(self): pass

    def start_table(self, attrs): pass

    def end_table(self): self._in_air_info = 0

    def start_td(self, attrs):
        if not self._in_air_info: return
        self._cur_txt = u''

    def end_td(self):
        if not self._in_air_info: return
        self._cur_txt = self._cur_txt.strip()
        if self._cur_txt and self._cur_info != 'episode':
            self._cur_data[self._cur_info] = self._cur_txt
            self._cur_txt = u''
        if self._cur_info == 'date':
            self._cur_info = 'time'
        elif self._cur_info == 'time':
            self._cur_info = 'channel'
        elif self._cur_info == 'channel':
            self._cur_info = 'episode'
        elif self._cur_info == 'episode':
            if self._title_kind == 'episode':
                self._cur_info = 'date'
            else:
                self._cur_info = 'season'
            if self._cur_txt and self._title:
                m = Movie(title='%s {%s}' % (self._title, self._cur_txt),
                            movieID=str(self._cur_id), accessSystem=self._as,
                            modFunct=self._modFunct)
                self._cur_data['episode'] = m
        elif self._cur_info == 'season':
            self._cur_info = 'episode'

    def start_tr(self, attrs):
        if not self._in_air_info: return
        self._cur_txt = u''
        self._cur_data = {}
        self._cur_info = 'date'

    def end_tr(self):
        if not self._in_air_info: return
        if self._cur_data:
            if 'episode' in self._cur_data:
                self._air.append(self._cur_data)
            self._cur_data = {}

    def _handle_data(self, data):
        if self._in_ch and data.lower().startswith('next us tv airing'):
            self._in_air_info = 1
        if self._in_html_title:
            self._title += data
        if not self._in_air_info: return
        self._cur_txt += data


class DOMHTMLAiringParser(DOMParserBase):
    """Parser for the "airing" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        aparser = DOMHTMLAiringParser()
        result = aparser.parse(airing_html_string)
    """
    extractors = [
        Extractor(label='series title',
            path="//title",
            attrs=Attribute(key='series title', path="./text()")),
        Extractor(label='tv airings',
            path="//tr[@class]",
            attrs=Attribute(key='airing',
                multi=True,
                path={
                    'date': "./td[1]//text()",
                    'time': "./td[2]//text()",
                    'channel': "./td[3]//text()",
                    'link': "./td[4]/a[1]/@href",
                    'title': "./td[4]//text()",
                    'season': "./td[5]//text()",
                    },
                postprocess=lambda x: {
                    'date': x.get('date'),
                    'time': x.get('time'),
                    'channel': x.get('channel').strip(),
                    'link': x.get('link'),
                    'title': x.get('title'),
                    'season': x.get('season')
                    }
                ))
    ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        if data.has_key('airing'):
            for airing in data['airing']:
                e = Movie(title='%s {%s}' % (data['series title'],
                    airing['title']),movieID=analyze_imdbid(airing['link']))
                airing['episode'] = e
                del airing['link']
                del airing['title']
        del data['series title']
        return data


class HTMLSynopsisParser(ParserBase):
    """Parser for the "synopsis" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = HTMLSynopsisParser()
        result = sparser.parse(synopsis_html_string)
    """

    def _reset(self):
        self._synops = u''
        self._in_synops = False

    def get_data(self):
        self._synops = self._synops.strip()
        if not self._synops: return {}
        return {'synopsis': self._synops}

    def start_div(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if not cls: return
        style = self.get_attr_value(attrs, 'style')
        if style: return
        if cls.strip().lower() != 'display': return
        # Here we are: a div section with 'class' set to "display" and
        # no 'style' attribute.
        self._in_synops = True

    def end_div(self):
        if self._in_synops:
            self._in_synops = False

    def do_br(self, attrs):
        if not self._in_synops: return
        self._synops += '\n'

    def _handle_data(self, data):
        if not self._in_synops: return
        self._synops += data


class DOMHTMLSynopsisParser(DOMParserBase):
    """Parser for the "synopsis" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = HTMLSynopsisParser()
        result = sparser.parse(synopsis_html_string)
    """
    extractors = [
        Extractor(label='synopsis',
            path="//div[@class='display'][not(@style)]",
            attrs=Attribute(key='synopsis',
                path=".//text()",
                postprocess=lambda x: '\n\n'.join(x.strip().split('||'))))
    ]

    preprocessors = [
        (re.compile('<br/><br/>', re.I), r'||')
        ]


class HTMLParentsGuideParser(ParserBase):
    """Parser for the "parents guide" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        pgparser = HTMLParentsGuideParser()
        result = pgparser.parse(parentsguide_html_string)
    """

    def _reset(self):
        self._pg = {}
        self._in_section = False
        self._in_h3 = False
        self._in_display = False
        self._cur_sect = u''
        self._cur_txt = u''
        self._seen_br = False

    def get_data(self):
        if not self._pg: return {}
        return {'parents guide': self._pg}

    def start_div(self, attrs):
        cls = self.get_attr_value(attrs, 'class')
        if not cls: return
        cls = cls.strip().lower()
        if cls == 'section':
            self._in_section = True
            self._in_display = False
            self._cur_sect = u''
            return
        if cls == 'display':
            style = self.get_attr_value(attrs, 'style')
            if not style:
                self._in_display = True

    def end_div(self):
        if self._in_section:
            self._in_section = False
            self._cur_sect = self._cur_sect.strip().lower()
            return
        if self._in_display:
            self._in_display = False

    def start_h3(self, attrs):
        self._in_h3 = True

    def end_h3(self):
        self._in_h3 = False

    def start_p(self, attrs): pass

    def end_p(self):
        if not self._in_display: return
        self._add_pg()

    def _add_pg(self):
        self._cur_txt = self._cur_txt.strip()
        if not (self._cur_txt and self._cur_sect):
            self._cur_txt = u''
            return
        self._pg.setdefault(self._cur_sect, []).append(self._cur_txt)
        self._cur_txt = u''

    def do_br(self, attrs):
        if not self._in_display: return
        if self._seen_br:
            self._seen_br = False
            self._add_pg()
        if not self._seen_br:
            self._cur_txt += '\n'
            self._seen_br = True

    def _handle_data(self, data):
        if self._in_section and self._in_h3:
            self._cur_sect += data
        elif self._in_display:
            if self._seen_br and data.strip():
                self._seen_br = False
            data = data.replace('\n', ' ')
            self._cur_txt += data


class DOMHTMLParentsGuideParser(DOMParserBase):
    """Parser for the "parents guide" page of a given movie.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        pgparser = HTMLParentsGuideParser()
        result = pgparser.parse(parentsguide_html_string)
    """
    extractors = [
        Extractor(label='parents guide',
            group="//div[@class='section']",
            group_key="./h3/a/span/text()",
            group_key_normalize=lambda x: x.lower(),
            path="../following-sibling::div[1]/p",
            attrs=Attribute(key=None,
                path=".//text()",
                postprocess=lambda x: [t.strip().replace('\n', ' ')
                                       for t in x.split('||') if t.strip()]))
    ]

    preprocessors = [
        (re.compile('<br/><br/>', re.I), r'||')
        ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        return {'parents guide': data}


_OBJECTS = {
    'movie_parser':  ((DOMHTMLMovieParser, HTMLMovieParser), None),
    'plot_parser':  ((DOMHTMLPlotParser, HTMLPlotParser), None),
    'movie_awards_parser': ((DOMHTMLAwardsParser, HTMLAwardsParser), None),
    'taglines_parser':  ((DOMHTMLTaglinesParser, HTMLTaglinesParser), None),
    'keywords_parser':  ((DOMHTMLKeywordsParser, HTMLKeywordsParser), None),
    'crazycredits_parser':  ((DOMHTMLCrazyCreditsParser,
                                HTMLCrazyCreditsParser), None),
    'goofs_parser':  ((DOMHTMLGoofsParser, HTMLGoofsParser), None),
    'alternateversions_parser':  ((DOMHTMLAlternateVersionsParser,
                                    HTMLAlternateVersionsParser), None),
    'trivia_parser':  ((DOMHTMLAlternateVersionsParser,
                        HTMLAlternateVersionsParser), {'kind': 'trivia'}),
    'soundtrack_parser':  ((DOMHTMLSoundtrackParser,
                        HTMLAlternateVersionsParser), {'kind': 'soundtrack'}),
    'quotes_parser':  ((DOMHTMLQuotesParser, HTMLQuotesParser), None),
    'releasedates_parser':  ((DOMHTMLReleaseinfoParser, HTMLReleaseinfoParser),
                            None),
    'ratings_parser':  ((DOMHTMLRatingsParser, HTMLRatingsParser), None),
    'officialsites_parser':  ((DOMHTMLOfficialsitesParser,
                                HTMLOfficialsitesParser), None),
    'externalrev_parser':  ((DOMHTMLOfficialsitesParser,
                            HTMLOfficialsitesParser),
                            {'kind': 'external reviews'}),
    'newsgrouprev_parser':  ((DOMHTMLOfficialsitesParser,
                                HTMLOfficialsitesParser),
                            {'kind': 'newsgroup reviews'}),
    'misclinks_parser':  ((DOMHTMLOfficialsitesParser,
                            HTMLOfficialsitesParser),
                            {'kind': 'misc links'}),
    'soundclips_parser':  ((DOMHTMLOfficialsitesParser,
                            HTMLOfficialsitesParser), {'kind': 'sound clips'}),
    'videoclips_parser':  ((DOMHTMLOfficialsitesParser,
                            HTMLOfficialsitesParser), {'kind': 'video clips'}),
    'photosites_parser':  ((DOMHTMLOfficialsitesParser,
                            HTMLOfficialsitesParser), {'kind': 'photo sites'}),
    'connections_parser':  ((DOMHTMLConnectionParser,
                            HTMLConnectionParser), None),
    'tech_parser':  ((DOMHTMLTechParser, HTMLTechParser), None),
    'business_parser':  ((DOMHTMLTechParser, HTMLTechParser),
                            {'kind': 'business', '_defGetRefs': 1}),
    'literature_parser':  ((DOMHTMLTechParser, HTMLTechParser),
                            {'kind': 'literature'}),
    'locations_parser':  ((DOMHTMLLocationsParser, HTMLLocationsParser), None),
    'dvd_parser':  ((DOMHTMLDvdParser, HTMLDvdParser), None),
    'rec_parser':  ((DOMHTMLRecParser, HTMLRecParser), None),
    'news_parser':  ((DOMHTMLNewsParser, HTMLNewsParser), None),
    'amazonrev_parser':  ((DOMHTMLAmazonReviewsParser, HTMLAmazonReviewsParser),
                            None),
    'sales_parser':  ((DOMHTMLSalesParser, HTMLSalesParser), None),
    'episodes_parser':  ((DOMHTMLEpisodesParser, HTMLEpisodesParser), None),
    'episodes_cast_parser':  ((DOMHTMLEpisodesCastParser, HTMLEpisodesParser),
                        None),
    'eprating_parser':  ((DOMHTMLEpisodesRatings, HTMLEpisodesRatings), None),
    'movie_faqs_parser':  ((DOMHTMLFaqsParser, HTMLFaqsParser), None),
    'airing_parser':  ((DOMHTMLAiringParser, HTMLAiringParser), None),
    'synopsis_parser':  ((DOMHTMLSynopsisParser, HTMLSynopsisParser), None),
    'parentsguide_parser':  ((DOMHTMLParentsGuideParser, HTMLParentsGuideParser),
                            None)
}

