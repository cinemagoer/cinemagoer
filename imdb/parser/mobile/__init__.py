"""
parser.mobile package (imdb package).

This package provides the IMDbMobileAccessSystem class used to access
IMDb's data for mobile systems.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "mobile".

Copyright 2005 Davide Alberani <da@erlug.linux.it>

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

import re, urllib
from htmlentitydefs import entitydefs
from sgmllib import entityref, charref

from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import analyze_title, analyze_name, modNull, \
                        canonicalTitle, canonicalName
from imdb._exceptions import IMDbDataAccessError
from imdb.parser.http import IMDbHTTPAccessSystem, imdbURL_search, \
                                imdbURL_movie, imdbURL_person


# Common part for names search.
regexp_gn = r'(<a href="/name/nm[0-9]{7}/">.+?</a>.*?<br>)'
# Find the director(s).
re_dir = re.compile(r'directed by</b><br>\s*' + regexp_gn, re.I)
# Find the writer(s).
re_wri = re.compile(r'writing credits</b>\s*(?:<small>.*?</small>)?\s*<br>\s*' + regexp_gn, re.I)
# Extract personIDs and names.
re_names = re.compile(r'<a href="/name/nm([0-9]{7})/">(.+?)</a>\s*( .+?)?(?=<br>|</td>)', re.I)
# Extract personIDs, names and optional roles.
re_names_cast = re.compile(r'<a href="/name/nm([0-9]{7})/">(.+?)</a></td>(?:<td.*?>\s*\.\.\.\.\s*</td><td.*?>(.+?)</td></tr>)?', re.I)
# The personID.
re_personID = re.compile(r'<a href="/name/nm([0-9]{7})/board/threads/">', re.I)
# People headshots.
re_headshot = re.compile(r'<a.*?name="headshot".*?<img.+?src="(.+?)"')
# Person filmography sections.
re_whathedo = re.compile(r'<i>filmography as:</i>.+?</small>', re.I)
re_filmoyer_sect = re.compile(r'<a href="#(.+?)">(.+?)</a>')
# Person filmography.
re_filmoyer = re.compile(r'<li>\s*<a.*?href="/title/tt([0-9]{7}/">.+?</a>(?:\s|.)*?)\s*(?=</li>|<br>)', re.I)
# Name akas.
re_nmakas = re.compile(r'sometimes credited as:</div></dt>\s*<dd>(.+?)(?:<br>(.+?))*\s*</dd>', re.I)
# Birth name.
re_bname = re.compile(r'<dt class="ch">birth name</dt>\s*<dd>(.+?)\s*(?=<hr|</dd>)', re.I)
# Height.
re_height = re.compile(r'<dt class="ch">height</dt>\s*<dd>(.+?)\s*(?=<hr|</dd>)', re.I)
# Mini biography.
re_bio = re.compile(r'<dt class="ch">mini biography</dt>\s*<dd><p class="biopar">\s*(.+?)\s*</p>', re.I)
# Birth and death.
re_born = re.compile(r'<a href="/onthisday\?.+?">(.+?)</a>\s*<a href="/borninyear\?([0-9?]{4})">', re.I)
re_bnotes = re.compile(r'<a href="/bornwhere\?.+?">(.+?)</a>', re.I)
re_death = re.compile(r'<a href="/onthisday\?.+?">(.+?)</a>\s*?<a href="/diedinyear\?([0-9?]{4})">[0-9?]{4}</a><br>(?:\s*?(.+?)\s*)?\s*?</dd>', re.I)

# The movieID.
re_movieID = re.compile(r'<input.+?value="([0-9]{7})">', re.I)
# Movie genres.
re_genres = re.compile(r'href="/sections/genres/(.+?)/"', re.I)
# User rating.
re_ur = re.compile(r'user rating:</b>.*?<b>([0-9\.]+?)/10</b> \(([0-9,\.]+) votes\)', re.I | re.S)
re_top250 = re.compile(r'<a href="/top_250_films">top 250: #([0-9]{1,3})</a>', re.I)
# The cast's table.
re_cast = re.compile(r'cast overview.*?</table>', re.I)
# Akas for movies.
re_akas = re.compile(r'<i class="transl">(.+?)</i>', re.I)
# MPAA rating.
re_mpaa = re.compile(r'<a href="/mpaa">mpaa</a>:</b>\s*(.+?)\s*<br>', re.I)
# Runtimes.
re_runtimes = re.compile(r'<b class="ch">runtime:</b>\s*(.+?)\s*<br>', re.I)
# Countries.
re_countr = re.compile(r'<a href="/sections/countries/.+?/">(.+?)</a>', re.I)
# Languages.
re_lang = re.compile(r'<a href="/sections/languages/.+?/">(.+?)</a>', re.I)
# Color info.
re_color = re.compile(r'<a href="/list\?color-info=.+?">(.+?)</a>(?: <i>(.+?)</i>)?', re.I)
# Soundmix.
re_soundmix = re.compile(r'<a href="/list\?sound-mix=.+?">(.+?)</a>', re.I)
# Certificates.
re_certificates = re.compile(r'<a href="/list\?certificates=.+?">(.+?)</a>(?: <i>(.+?)</i>)?', re.I)
# To find the cover.
re_cover1 = re.compile(r'<img .*?alt="cover".*?>', re.I)
re_cover2 = re.compile(r'src="(.+?)"', re.I)
# Spouse.
re_spouse1 = re.compile(r'<dt class="ch">spouse</dt>\s*<dd><table border="0">(.+?)</table>', re.I | re.S)
re_spouse2 = re.compile(r'<tr>(.+?)</tr>', re.I | re.S)
re_misc_sect = re.compile(r'<dt class="ch">(.+?)</dt>\s*<dd>(.+?)\s*(?:</hr>|</dd>)', re.I|re.S)

# Movie plot.
re_plot = re.compile(r'<p class="plotpar">\s*(.+?)\s*</p>', re.I)

# Movie title or person name.
re_title = re.compile(r'<title>(.+?)</title>', re.I)
# To strip spaces.
re_spaces = re.compile(r'\s+')
# Strip html.
re_unhtml = re.compile(r'<.+?>')

# Movie search.
re_msearch = re.compile(r'<li>\s*<a.+?href="/title/tt([0-9]{7})/".*?>(.+?)</a>\s*(?: (.+?))?\s*(?=</li>|<br>)', re.I)
# Person search.
re_psearch = re.compile(r'<li>\s*<a.+?href="/name/nm([0-9]{7})/".*?>(.+?)</a>\s*(?: (.+?))?\s*(?=<small>|<br>|</li>)', re.I)


# Here to handle non-breaking spaces.
entitydefs['nbsp'] = ' '

def _replRef(match):
    """Replace the matched entity or reference."""
    ret = match.group()[1:-1]
    ret = entitydefs.get(ret, ret)
    if ret[0] == '#':
        try:
            ret = chr(int(ret[1:]))
            if ret == '\xa0': ret = ' '
        except (ValueError, TypeError, OverflowError):
            try:
                ret = unichr(int(ret[1:])).encode('utf-8')
            except (ValueError, TypeError, OverflowError):
                pass
            pass
    return ret

def _subRefs(s):
    """Return the given html string with entity and char references
    replaced."""
    s = entityref.sub(_replRef, s)
    s = charref.sub(_replRef, s)
    return s


def _getFilmography(s):
    """Return a dictionary with the filmography of a person."""
    r = {}
    bdate = re_born.search(s)
    if bdate:
        r['birth date'] = ' '.join(bdate.groups())
    bnotes = re_bnotes.search(s)
    if bnotes:
        r['birth notes'] = ' '.join(bnotes.groups())
    ddate = re_death.search(s)
    if ddate:
        gr = ddate.groups()
        r['death date'] = ' '.join(gr[0:2])
        dn = gr[2]
        if dn: r['death notes'] = dn
    akas = re_nmakas.search(s)
    if akas:
        r['akas'] = [x for x in akas.groups() if x]
    hs = re_headshot.search(s)
    if hs:
        r['headshot'] = hs.groups()[0]
    do_what = re_whathedo.search(s)
    if not do_what: return r
    sects = re_filmoyer_sect.findall(s[do_what.start():do_what.end()])
    if not sects: return r
    for sect, sectName in sects:
        sectName = sectName.lower()
        rawm = re.search('<a name="%s">.+?<ol>(.+?)</ol>' % sect, s, re.I|re.S)
        if not rawm: continue
        raws = s[rawm.start():rawm.end()]
        mlist = re_filmoyer.findall(raws)
        for m in mlist:
            d = {}
            d['movieID'] = m[:7]
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
                d['title'] = '"%s"' % d['title']
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
            #istvguest = 0
            #if m.find('<small>playing</small>') != -1:
            #    istvguest = 1
            m = m.replace('<small>', ' ').replace('</small>', ' ')
            m = re_spaces.sub(' ', m).strip()
            notes = ''
            role = ''
            ms = m.split('....')
            if len(ms) >= 1:
                first = ms[0]
                if first and first[0] == '(':
                    notes = first.strip()
                ms = ms[1:]
            if ms: role = ' '.join(ms).strip()
            movie = Movie(title=d['title'],
                            accessSystem='mobile', movieID=d['movieID'],
                            modFunct=modNull)
            if d.has_key('status'): movie['status'] = d['status']
            movie.currentRole = role
            movie.notes = notes
            if not r.has_key(sectName): r[sectName] = []
            r[sectName].append(movie)
    return r


class IMDbMobileAccessSystem(IMDbHTTPAccessSystem):
    """The class used to access IMDb's data through the web for
    mobile terminals."""

    accessSystem = 'mobile'

    def __init__(self, isThin=1, *arguments, **keywords):
        IMDbHTTPAccessSystem.__init__(self, isThin, *arguments, **keywords)
        self.accessSystem = 'mobile'

    def _mretrieve(self, url):
        return _subRefs(IMDbHTTPAccessSystem._retrieve(self, url))

    def _buildPerson(self, match, regexp=re_names):
        r = []
        if not match: return r
        names = regexp.findall(match.group())
        for name in names:
            notes = ''
            currentRole = name[2]
            fpi = currentRole.find('(')
            if fpi != -1:
                fpe = currentRole.rfind(')')
                notes = currentRole[fpi:fpe+1]
                currentRole = currentRole[:fpi].strip()
            r.append(Person(personID=name[0], name=canonicalName(name[1]),
                        currentRole=currentRole, notes=notes,
                        modFunct=modNull))
        return r

    def _search_movie(self, title, results):
        params = urllib.urlencode({'tt': 'on', 'mx': str(results), 'q': title})
        cont = self._mretrieve(imdbURL_search % params)
        title = re_title.findall(cont)
        res = []
        if not title: return res
        if title[0].lower().find('imdb title search') == -1:
            # XXX: a direct hit!
            title = analyze_title(title[0], canonical=1)
            mid = re_movieID.findall(cont)
            if mid: res = [(mid[0], title)]
        else:
            res = re_msearch.findall(cont)
            res = [(x[0], analyze_title(' '.join(x[1:]), canonical=1))
                    for x in res]
        return res

    def get_movie_main(self, movieID):
        cont = self._mretrieve(imdbURL_movie % movieID + 'maindetails')
        d = {}
        title = re_title.findall(cont)
        if not title:
            raise IMDbDataAccessError, 'unable to get movieID "%s"' % movieID
        d = analyze_title(title[0], canonical=1)
        directh = re_dir.search(cont)
        dnames = self._buildPerson(directh)
        if dnames: d['director'] = dnames
        wrih = re_wri.search(cont)
        wnames = self._buildPerson(wrih)
        if wnames: d['writer'] = wnames
        c1 = re_cover1.findall(cont)
        if c1:
            c2 = re_cover2.findall(c1[0])
            if c2: d['cover url'] = c2[0]
        genres = re_genres.findall(cont)
        if genres:
            d['genres'] = genres
        ur = re_ur.search(cont)
        if ur:
            rating, votes = ur.groups()
            if rating: d['rating'] = rating
            if votes: d['votes'] = votes.replace(',', '')
        top250 = re_top250.search(cont)
        if top250: d['top 250 rank'] = top250.group(1)
        castdata = re_cast.search(cont)
        cast = self._buildPerson(castdata, regexp=re_names_cast)
        if cast: d['cast'] = cast
        akas = [x.replace(' (','::(',1).replace('   [','::[').replace('  ',' ')
                for x in re_akas.findall(cont)]
        if akas: d['akas'] = akas
        mpaa = re_mpaa.findall(cont)
        if mpaa: d['mpaa'] = mpaa[0]
        runtimes = re_runtimes.search(cont)
        if runtimes:
            rt = [x.strip().replace(' min', '')
                    for x in runtimes.group(1).split('/')]
            d['runtimes'] = rt
        country = re_countr.findall(cont)
        if country: d['countries'] = country
        lang = re_lang.findall(cont)
        if re_lang: d['languages'] = lang
        col = re_color.findall(cont)
        for i in xrange(len(col)):
            if col[i][1]: col[i] = col[i][0] + '::' + col[i][1]
            else: col[i] = col[i][0]
        if col: d['color'] = col
        sm = re_soundmix.findall(cont)
        if sm: d['sound mix'] = sm
        cert = re_certificates.findall(cont)
        for i in xrange(len(cert)):
            if cert[i][1]: cert[i] = cert[i][0] + '::' + cert[i][1]
            else: cert[i] = cert[i][0]
        if cert: d['certificates'] = cert
        return {'data': d}

    def get_movie_plot(self, movieID):
        cont = self._mretrieve(imdbURL_movie % movieID + 'plotsummary')
        plot = re_plot.findall(cont)
        if plot: return {'data': {'plot': plot}}
        return {'data': {}}

    def _search_person(self, name, results):
        params = urllib.urlencode({'nm': 'on', 'mx': str(results), 'q': name})
        cont = self._mretrieve(imdbURL_search % params)
        name = re_title.findall(cont)
        res = []
        if not name: return res
        if name[0].lower().find('imdb name search') == -1:
            # XXX: a direct hit!
            name = analyze_name(name[0], canonical=1)
            pid = re_personID.findall(cont)
            if pid: res = [(pid[0], name)]
        else:
            res = re_psearch.findall(cont)
            res = [(x[0], analyze_name(' '.join(x[1:]), canonical=1))
                    for x in res]
        return res

    def get_person_main(self, personID):
        cont = self._mretrieve(imdbURL_person % personID + 'maindetails')
        d = {}
        name = re_title.findall(cont)
        if not name:
            raise IMDbDataAccessError, 'unable to get personID "%s"' % personID
        d = analyze_name(name[0], canonical=1)
        d.update(_getFilmography(cont))
        return {'data': d, 'info sets': ('main', 'filmography')}

    def get_person_biography(self, personID):
        cont = self._mretrieve(imdbURL_person % personID + 'bio')
        d = {}
        bname = re_bname.findall(cont)
        if bname: d['birth name'] = bname[0]
        height = re_height.findall(cont)
        if height: d['height'] = height[0]
        bio = re_bio.findall(cont)
        if bio: d['mini biography'] = bio
        spouses = re_spouse1.search(cont)
        if spouses:
            sl = []
            for spouse in re_spouse2.findall(spouses.groups()[0]):
                if spouse.count('</td>') > 1:
                    spouse = spouse.replace('</td>', '::</td>', 1)
                spouse = re_spaces.sub(' ', re_unhtml.sub('', spouse))
                spouse = spouse.replace(':: ', '::').strip()
                sl.append(spouse)
            if sl: d['spouse'] = sl
        misc_sects = re_misc_sect.findall(cont)
        if misc_sects:
            for sect, data in misc_sects:
                sect = sect.lower().replace(':', '').strip()
                if sect == 'salary': sect = 'salary history'
                if sect in ('birth name', 'height', 'mini biography',
                            'imdb mini-biography by', 'spouse'):
                    continue
                data = data.replace('</p><p class="biopar">', '::')
                data = data.replace('</td>\n<td valign="top">', '@@@@')
                data = data.replace('</td>\n</tr>', '::')
                data = re_spaces.sub(' ', re_unhtml.sub('', data))
                data = [x.strip() for x in data.split('::')]
                data[:] = [x.replace('@@@@', '::') for x in data if x]
                d[sect] = data
        return {'data': d}


