"""
parser.mobile package (imdb package).

This package provides the IMDbMobileAccessSystem class used to access
IMDb's data for mobile systems.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "mobile".

Copyright 2005-2007 Davide Alberani <da@erlug.linux.it>

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
from types import ListType, TupleType

from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import analyze_title, analyze_name, canonicalName, re_episodes
from imdb._exceptions import IMDbDataAccessError
from imdb.parser.http import IMDbHTTPAccessSystem, \
                                imdbURL_movie, imdbURL_person
from imdb.parser.http.utils import subXMLRefs, subSGMLRefs

# XXX NOTE: the first version of this module was heavily based on
#           regular expressions.  This new version replace regexps with
#           find() strings' method calls; despite being less flexible, it
#           seems to be at least as fast and, hopefully, much more
#           lightweight.  Yes: the regexp-based version was too heavyweight
#           for systems with very limited CPU power and memory footprint.

# To strip spaces.
re_spaces = re.compile(r'\s+')
re_spacessub = re_spaces.sub
# Strip html.
re_unhtml = re.compile(r'<.+?>')
re_unhtmlsub = re_unhtml.sub
# imdb person or movie ids.
re_imdbID = re.compile(r'(?<=nm|tt)([0-9]{7})\b')


def _unHtml(s):
    """Return a string without tags and no multiple spaces."""
    return subSGMLRefs(re_spacessub(' ', re_unhtmlsub('', s)).strip())


_inttype = type(0)

def _getTagWith(s, cont):
    """Return the html tags in the 's' string containing the 'cont'
    string."""
    lres = []
    bi = s.find(cont)
    if bi != -1:
        btag = s[:bi].rfind('<')
        if btag != -1:
            etag = s[bi+1:].find('>')
            if etag != -1:
                lres.append(s[btag:bi+2+etag])
                lres += _getTagWith(s[btag+1+etag:], cont)
    return lres


def _findBetween(s, begins, ends, beginindx=0):
    """Return the list of strings from the 's' string which are included
    between the 'begins' and 'ends' strings."""
    lres = []
    #if endindx is None: endindx = len(s)
    bi = s.find(begins, beginindx)
    if bi != -1:
        lbegins = len(begins)
        if isinstance(ends, (ListType, TupleType)):
            eset = [s.find(end, bi+lbegins) for end in ends]
            eset[:] = [x for x in eset if x != -1]
            if not eset: ei = -1
            else: ei = min(eset)
        else:
            ei = s.find(ends, bi+lbegins)
        if ei != -1:
            match = s[bi+lbegins:ei]
            lres.append(match)
            lres += _findBetween(s, begins, ends, ei)
            ##if maxRes > 0 and len(lres) >= maxRes: return lres
    return lres


class IMDbMobileAccessSystem(IMDbHTTPAccessSystem):
    """The class used to access IMDb's data through the web for
    mobile terminals."""

    accessSystem = 'mobile'

    def __init__(self, isThin=1, *arguments, **keywords):
        IMDbHTTPAccessSystem.__init__(self, isThin, *arguments, **keywords)
        self.accessSystem = 'mobile'

    def _clean_html(self, html):
        """Normalize the retrieve html."""
        html = re_spaces.sub(' ', html)
        return subXMLRefs(html)

    def _mretrieve(self, url, size=-1):
        """Retrieve an html page and normalize it."""
        cont = self._retrieve(url, size=size)
        return self._clean_html(cont)

    def _getPersons(self, s, sep='<br>', hasCr=0, aonly=0):
        """Return a list of Person objects, from the string s; items
        are assumed to be separated by the sep string; if hasCr is set,
        the currentRole of a person is searched."""
        names = s.split(sep)
        pl = []
        plappend = pl.append
        counter = 1
        currentRole = u''
        for name in names:
            notes = u''
            currentRole = u''
            fpi = name.find(' (')
            if fpi != -1:
                fpe = name.rfind(')')
                if fpe > fpi:
                    notes = _unHtml(name[fpi:fpe+1])
                    name = name[:fpi] + name[fpe+1:]
                    lampi = name.rfind('&')
                    if lampi != -1 and name[lampi+1:].isspace():
                        name = name[:lampi].rstrip()
            if hasCr:
                name = name.split(' .... ')
                if len(name) > 1:
                    currentRole = _unHtml(name[1])
                name = name[0]
            pid = re_imdbID.findall(name)
            if aonly:
                stripped = _findBetween(name, '>', '</a>')
                if len(stripped) == 1: name = stripped[0]
            name = _unHtml(name)
            gt_indx = name.find('>')
            if gt_indx != -1:
                name = name[gt_indx+1:].lstrip()
            if not (pid and name): continue
            plappend(Person(personID=str(pid[0]), name=name,
                            currentRole=currentRole, notes=notes,
                            accessSystem=self.accessSystem,
                            modFunct=self._defModFunct, billingPos=counter))
            counter += 1
        return pl

    def _search_movie(self, title, results):
        ##params = urllib.urlencode({'tt': 'on','mx': str(results),'q': title})
        ##params = 'q=%s&tt=on&mx=%s' % (urllib.quote_plus(title), str(results))
        ##cont = self._mretrieve(imdbURL_search % params)
        cont = subXMLRefs(self._get_search_content('tt', title, results))
        title = _findBetween(cont, '<title>', '</title>')
        res = []
        if not title: return res
        tl = title[0].lower()
        if not tl.startswith('imdb title'):
            # XXX: a direct hit!
            title = _unHtml(title[0])
            midtag = _getTagWith(cont, 'name="arg"')
            if not midtag: midtag = _getTagWith(cont, 'name="auto"')
            mid = None
            if midtag:
                mid = _findBetween(midtag[0], 'value="', '"')
                if mid and not mid[0].isdigit():
                    mid = re_imdbID.findall(mid[0])
            if not (mid and title): return res
            res[:] = [(str(mid[0]), analyze_title(title, canonical=1))]
        else:
            lis = _findBetween(cont, '<li>', ['</li>', '<br>'])
            for li in lis:
                imdbid = re_imdbID.findall(li)
                mtitle = _unHtml(li)
                if not (imdbid and mtitle): continue
                res.append((str(imdbid[0]), analyze_title(mtitle, canonical=1)))
        return res

    def get_movie_main(self, movieID):
        cont = self._mretrieve(imdbURL_movie % movieID + 'maindetails')
        d = {}
        title = _findBetween(cont, '<title>', '</title>')
        if not title:
            raise IMDbDataAccessError, 'unable to get movieID "%s"' % movieID
        title = _unHtml(title[0])
        d = analyze_title(title, canonical=1)
        tv_series = _findBetween(cont, 'TV Series:</b>', '</a>')
        if tv_series: mid = re_imdbID.findall(tv_series[0])
        else: mid = None
        if tv_series and mid:
            s_title = _unHtml(tv_series[0])
            s_data = analyze_title(s_title, canonical=1)
            m = Movie(movieID=str(mid), data=s_data, accessSystem='mobile')
            d['kind'] = 'episode'
            d['episode of'] = m
            d['movieID'] = mid[0]
            ep_title = _findBetween(cont, '<h1><strong class="title">',
                                            '</strong></h1>')
            if ep_title:
                ep_title = _findBetween(ep_title[0], '<small>', '</small>')
            if ep_title:
                s_data = analyze_title(ep_title[0], canonical=1)
                del s_data['kind']
                d.update(s_data)
        air_date = _findBetween(cont, 'Original Air Date:</b>', '<br><br>')
        if air_date:
            air_date = air_date[0]
            vi = air_date.find('(')
            if vi != -1:
                date = air_date[:vi].strip()
                if date != '????':
                    d['original air date'] = date
                air_date = air_date[vi:]
                season = _findBetween(air_date, 'Season', ',')
                if season:
                    season = season[0].strip()
                    try: season = int(season)
                    except: pass
                    if season or type(season) is _inttype:
                        d['season'] = season
                episode = _findBetween(air_date, 'Episode', ')')
                if episode:
                    episode = episode[0].strip()
                    try: episode = int(episode)
                    except: pass
                    if episode or type(season) is _inttype:
                        d['episode'] = episode
        direct = _findBetween(cont, 'Directed by</b><br>', '<br> <br>')
        if direct:
            dirs = self._getPersons(direct[0], aonly=1)
            if dirs: d['director'] = dirs
        writers = _findBetween(cont, 'Writing credits</b>', '<br> <br>')
        if writers:
            ws = self._getPersons(writers[0], aonly=1)
            if ws: d['writer'] = ws
        cvurl = _getTagWith(cont, 'alt="cover"')
        if cvurl:
            cvurl = _findBetween(cvurl[0], 'src="', '"')
            if cvurl: d['cover url'] = cvurl[0]
        if not d.has_key('cover url'):
            # Cover, the new style.
            short_title = d.get('title', u'')
            if short_title:
                if d.get('kind') in ('tv series', 'tv mini series'):
                    short_title = '&#34;%s&#34;' % short_title
                cvurl = _getTagWith(cont, 'alt="%s"' % short_title)
                if not cvurl:
                    cvurl = _getTagWith(cont, 'alt="%s"' %
                                        short_title.replace('#34', 'quot'))
                cvurl[:] = [x for x in cvurl if x[0:4] == '<img']
                if cvurl:
                    cvurl = _findBetween(cvurl[0], 'src="', '"')
                    if cvurl: d['cover url'] = cvurl[0]
        genres = _findBetween(cont, 'href="/Sections/Genres/', '/')
        if genres: d['genres'] = genres
        ur = _findBetween(cont, 'User Rating:</b>', ' votes)')
        if ur:
            rat = _findBetween(ur[0], '<b>', '</b>')
            if rat:
                teni = rat[0].find('/10')
                if teni != -1:
                    rat = rat[0][:teni]
                    try:
                        rat = float(rat.strip())
                        d['rating'] = rat
                    except ValueError:
                        pass
            vi = ur[0].rfind('(')
            if vi != -1 and ur[0][vi:].find('await') == -1:
                try:
                    votes = int(ur[0][vi+1:].replace(',', '').strip())
                    d['votes'] = votes
                except ValueError:
                    pass
        top250 = _findBetween(cont, 'href="/top_250_films"', '</a>')
        if top250:
            fn = top250[0].rfind('#')
            if fn != -1:
                try:
                    td = int(top250[0][fn+1:])
                    d['top 250 rank'] = td
                except ValueError:
                    pass
        castdata = _findBetween(cont, 'Cast overview', '</table>')
        if not castdata:
            castdata = _findBetween(cont, 'Credited cast', '</table>')
        if not castdata:
            castdata = _findBetween(cont, 'Complete credited cast', '</table>')
        if not castdata:
            castdata = _findBetween(cont, 'Series Cast Summary', '</table>')
        if castdata:
            castdata = castdata[0]
            fl = castdata.find('href=')
            if fl != -1: castdata = '<a ' + castdata[fl:]
            smib = castdata.find('<tr><td align="center" colspan="3"><small>')
            if smib != -1:
                smie = castdata.rfind('</small></td></tr>')
                if smie != -1:
                    castdata = castdata[:smib].strip() + \
                                castdata[smie+18:].strip()
            castdata = castdata.replace('/tr> <tr', '/tr><tr')
            cast = self._getPersons(castdata, sep='</tr><tr', hasCr=1)
            if cast: d['cast'] = cast
        # FIXME: doesn't catch "complete title", which is not
        #        included in <i> tags.
        #        See "Gehr Nany Fgbevrf 11", movieID: 0282910
        akas = _findBetween(cont, '<b class="ch">Also Known As:</b>',
                                    '<b class="ch">')
        if akas:
            akas[:] = [x for x in akas[0].split('<br>') if x.strip()]
            akas = [_unHtml(x).replace(' (','::(', 1).replace(' [','::[')
                    for x in akas]
            d['akas'] = akas
        mpaa = _findBetween(cont, 'MPAA</a>:', '<br>')
        if mpaa: d['mpaa'] = _unHtml(mpaa[0])
        runtimes = _findBetween(cont, 'Runtime:</b>', '<br>')
        if runtimes:
            # XXX: number of episodes?
            runtimes = runtimes[0]
            episodes = re_episodes.findall(runtimes)
            if episodes:
                runtimes = re_episodes.sub('', runtimes)
                episodes = episodes[0]
                try: episodes = int(episodes)
                except: pass
                d['number of episodes'] = episodes
            runtimes = [x.strip().replace(' min', '')
                    for x in runtimes.split('/')]
            d['runtimes'] = runtimes
        country = _findBetween(cont, 'href="/Sections/Countries/', ['"', '/'])
        if country: d['countries'] = country
        lang = _findBetween(cont, 'href="/Sections/Languages/', ['"', '/'])
        if lang: d['languages'] = lang
        col = _findBetween(cont, '"/List?color-info=', '<br')
        if col:
            col[:] = col[0].split(' / ')
            col[:] = ['<a %s' % x for x in col if x]
            col[:] = [_unHtml(x.replace(' <i>', '::')) for x in col]
            if col: d['color info'] = col
        sm = _findBetween(cont, '/List?sound-mix=', '<br>')
        if sm:
            sm[:] = sm[0].split(' / ')
            sm[:] = ['<a %s' % x for x in sm if x]
            sm[:] = [_unHtml(x.replace(' <i>', '::')) for x in sm]
            if sm: d['sound mix'] = sm
        cert = _findBetween(cont, 'Certification:</b>', '<br')
        if cert:
            cert[:] = cert[0].split(' / ')
            cert[:] = [_unHtml(x.replace(' <i>', '::')) for x in cert]
            if cert: d['certificates'] = cert
        plotoutline = _findBetween(cont, 'Plot Outline:</b>', ['<a ', '<br'])
        if plotoutline:
            plotoutline = plotoutline[0].strip()
            if plotoutline: d['plot outline'] = plotoutline
        return {'data': d}

    def get_movie_plot(self, movieID):
        cont = self._mretrieve(imdbURL_movie % movieID + 'plotsummary')
        plot = _findBetween(cont, '<p class="plotpar">', '</p>')
        plot[:] = [_unHtml(x) for x in plot]
        if plot: return {'data': {'plot': plot}}
        return {'data': {}}

    def _search_person(self, name, results):
        ##params = urllib.urlencode({'nm': 'on', 'mx': str(results), 'q': name})
        ##params = 'q=%s&nm=on&mx=%s' % (urllib.quote_plus(name), str(results))
        ##cont = self._mretrieve(imdbURL_search % params)
        cont = subXMLRefs(self._get_search_content('nm', name, results))
        name = _findBetween(cont, '<title>', '</title>')
        res = []
        if not name: return res
        nl = name[0].lower()
        if not nl.startswith('imdb name'):
            # XXX: a direct hit!
            name = _unHtml(name[0])
            pidtag = _getTagWith(cont, '/board/threads/')
            pid = None
            if pidtag: pid = _findBetween(pidtag[0], '/name/nm', '/')
            if not (pid and name): return res
            res[:] = [(str(pid[0]), analyze_name(name, canonical=1))]
        else:
            lis = _findBetween(cont, '<li>', ['<small', '</li>', '<br'])
            for li in lis:
                pid = re_imdbID.findall(li)
                pname = _unHtml(li)
                if not (pid and pname): continue
                res.append((str(pid[0]), analyze_name(pname, canonical=1)))
        return res

    def get_person_main(self, personID):
        s = self._mretrieve(imdbURL_person % personID + 'maindetails')
        r = {}
        name = _findBetween(s, '<title>', '</title>')
        if not name:
            raise IMDbDataAccessError, 'unable to get personID "%s"' % personID
        name = _unHtml(name[0])
        r = analyze_name(name, canonical=1)
        bdate = _findBetween(s, '<div class="ch">Date of birth',
                            ('<br>', '<dt>'))
        if bdate:
            bdate = _unHtml('<a %s' % bdate[0])
            if bdate: r['birth date'] = bdate
        bnotes = _findBetween(s, 'href="/BornWhere?', '</dd>')
        if bnotes:
            bnotes = _unHtml('<a %s' % bnotes[0])
            if bnotes: r['birth notes'] = bnotes
        ddate = _findBetween(s, '<div class="ch">Date of death', '</dd>')
        if ddate:
            ddates = ddate[0].split('<br>')
            ddate = ddates[0]
            ddate = _unHtml('<a %s' % ddate)
            if ddate: r['death date'] = ddate
            dnotes = None
            if len(ddates) > 1:
                dnotes = _unHtml(ddates[1])
            if dnotes: r['death notes'] = dnotes
        akas = _findBetween(s, 'Sometimes Credited As:', '</dl>')
        if akas:
            akas[:] = [_unHtml(x) for x in akas[0].split('<br>')]
            if akas: r['akas'] = akas
        hs = _findBetween(s, 'name="headshot"', '</a>')
        if hs:
            hs[:] = _findBetween(hs[0], 'src="', '"')
            if hs: r['headshot'] = hs[0]
        workkind = _findBetween(s, '<b><a name=', '</a> - filmography')

        ws = []
        for w in workkind:
            if w and w[0] == '"': w = w[1:]
            se = ''
            sn = ''
            eti = w.rfind('>')
            if eti == -1: continue
            se = w[:eti]
            if se and se[-1] == '"': se = se[:-1]
            se = se.strip()
            sn = w[eti+1:].strip().lower()
            if se and sn: ws.append((se, sn))
        # XXX: I think "guest appearances" are gone.
        if s.find('<a href="#guest-appearances"') != -1:
            ws.append(('guest-appearances', 'notable tv guest appearances'))
        if s.find('<a href="#archive">') != -1:
            ws.append(('archive', 'archive footage'))
        for sect, sectName in ws:
            raws = ''
            inisect = s.find('<a name="%s' % sect)
            if inisect != -1:
                endsect = s[inisect:].find('</ol>')
                if endsect != -1: raws = s[inisect:inisect+endsect]
            if not raws: continue
            mlist = _findBetween(raws, '<li>', ('</li>', '<br>'))
            for m in mlist:
                d = {}
                mid = re_imdbID.findall(m)
                if not mid: continue
                d['movieID'] = mid[0]
                ti = m.find('/">')
                te = m.find('</a>')
                if ti != -1 and te > ti:
                    d['title'] = m[ti+3:te]
                    m = m[te+4:]
                else:
                    continue
                fi = m.find('<font ')
                if fi != -1:
                    fe = m.find('</font>')
                    if fe > fi:
                        fif = m[fi+6:].find('>')
                        if fif != -1:
                            d['status'] = m[fi+7+fif:fe]
                            m = m[:fi] + m[fe+7:]
                fai = m.find('<i>')
                if fai != -1:
                    fae = m[fai:].find('</i>')
                    if fae != -1:
                        m = m[:fai] + m[fai+fae+4:]
                tvi = m.find('<small>TV Series</small>')
                if tvi != -1:
                    m = m[:tvi] + m[tvi+24:]
                m = m.strip()
                for x in xrange(2):
                    if len(m) > 1 and m[0] == '(':
                        ey = m.find(')')
                        if ey != -1:
                            if m[1].isdigit() or \
                                    m[1:ey] in ('TV', 'V', 'mini', 'VG'):
                                d['title'] += ' %s' % m[:ey+1]
                                m = m[ey+1:].lstrip()
                istvguest = 0
                if m.find('<small>playing</small>') != -1:
                    istvguest = 1
                    m = m.replace('<small>playing</small>', '').strip()
                else:
                    m=m.replace('<small>',' ').replace('</small>',' ').strip()
                notes = u''
                role = u''
                if not istvguest:
                    ms = m.split('....')
                    if len(ms) == 2:
                        notes = ms[0].strip().replace('  ', ' ')
                        role = ms[1].strip()
                        fn = role.find('(')
                        if fn != -1:
                            en = role.rfind(')')
                            pnote = role[fn:en+1].strip()
                            role = '%s %s' % (role[:fn].strip(),
                                            role[en+1:].strip())
                            role = role.strip()
                            if pnote:
                                if notes: notes += ' '
                                notes += pnote
                    else:
                        notes = ''.join(ms).strip().replace('  ', ' ')
                        role = u''
                    #if len(ms) >= 1:
                    #    first = ms[0]
                    #    if first and first[0] == '(':
                    #        notes = first.strip()
                    #    ms = ms[1:]
                    #if ms: role = ' '.join(ms).strip()
                else:
                    # XXX: strip quotes from strings like "Himself"?
                    noteidx = m.find('(')
                    if noteidx == -1:
                        noteidx = m.find('in episode')
                    if noteidx != -1:
                        notes = m[noteidx:]
                        role = m[:noteidx-1]
                    else:
                        role = m
                m_title = _unHtml(d['title'])
                movie = Movie(title=m_title, accessSystem=self.accessSystem,
                                movieID=str(d['movieID']),
                                modFunct=self._defModFunct)
                if d.has_key('status'): movie['status'] = _unHtml(d['status'])
                if role: movie.currentRole = _unHtml(role)
                if notes: movie.notes = _unHtml(notes)
                r.setdefault(sectName, []).append(movie)
        return {'data': r, 'info sets': ('main', 'filmography')}

    def get_person_biography(self, personID):
        cont = self._mretrieve(imdbURL_person % personID + 'bio')
        d = {}
        spouses = _findBetween(cont, 'Spouse</dt>', ('</table>', '</dd>'))
        if spouses:
            sl = []
            for spouse in spouses[0].split('</tr>'):
                if spouse.count('</td>') > 1:
                    spouse = spouse.replace('</td>', '::</td>', 1)
                spouse = _unHtml(spouse)
                spouse = spouse.replace(':: ', '::').strip()
                if spouse: sl.append(spouse)
            if sl: d['spouse'] = sl
        misc_sects = _findBetween(cont, '<dt class="ch">', ('<hr', '</dd>'))
        misc_sects[:] = [x.split('</dt>') for x in misc_sects]
        misc_sects[:] = [x for x in misc_sects if len(x) == 2]
        for sect, data in misc_sects:
            sect = sect.lower().replace(':', '').strip()
            if sect == 'salary': sect = 'salary history'
            elif sect in ('imdb mini-biography by', 'spouse'): continue
            elif sect == 'nickname': sect = 'nick names'
            elif sect == 'where are they now': sect = 'where now'
            elif sect == 'personal quotes': sect = 'quotes'
            data = data.replace('</p><p class="biopar">', '::')
            data = data.replace('</td>\n<td valign="top">', '@@@@')
            data = data.replace('</td>\n</tr>', '::')
            data = _unHtml(data)
            data = [x.strip() for x in data.split('::')]
            data[:] = [x.replace('@@@@', '::') for x in data if x]
            if sect in ('birth name', 'height') and data: data = data[0]
            if sect == 'birth name': data = canonicalName(data)
            d[sect] = data
        return {'data': d}

