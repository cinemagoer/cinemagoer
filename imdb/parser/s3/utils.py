
import re
import logging
import sqlalchemy
from imdb.utils import canonicalName, canonicalTitle, _unicodeArticles


re_imdbids = re.compile(r'(nm|tt)')


def transf_imdbid(x):
    return int(x[2:])


def transf_multi_imdbid(x):
    if not x:
        return x
    return re_imdbids.sub('', x)


def transf_int(x):
    try:
        return int(x)
    except:
        return None


def transf_float(x):
    try:
        return float(x)
    except:
        return None


def transf_bool(x):
    try:
        return x == '1'
    except:
        return None


DB_TRANSFORM = {
    'title_basics': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'titleType': {'rename': 'kind'},
        'primaryTitle': {'rename': 'title'},
        'originalTitle': {'rename': 'original title'},
        'isAdult': {'type': sqlalchemy.Boolean, 'transform': transf_bool, 'rename': 'adult', 'index': True},
        'startYear': {'type': sqlalchemy.Integer, 'transform': transf_int, 'index': True},
        'endYear': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'runtimeMinutes': {'type': sqlalchemy.Integer, 'transform': transf_int,
                           'rename': 'runtimes'},
        't_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True}
    },
    'name_basics': {
        'nconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'personID', 'index': True},
        'primaryName': {'rename': 'name'},
        'birthYear': {'type': sqlalchemy.Integer, 'transform': transf_int,
                      'rename': 'birth date', 'index': True},
        'deathYear': {'type': sqlalchemy.Integer, 'transform': transf_int,
                      'rename': 'death date', 'index': True},
        'primaryProfession': {'rename': 'primary profession'},
        'knownForTitles': {'transform': transf_multi_imdbid, 'rename': 'known for'},
        'ns_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True},
        'sn_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True},
        's_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True},
    },
    'title_crew': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'directors': {'transform': transf_multi_imdbid, 'rename': 'director'},
        'writers': {'transform': transf_multi_imdbid, 'rename': 'writer'}
    },
    'title_episode': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'parentTconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid, 'index': True},
        'seasonNumber': {'type': sqlalchemy.Integer, 'transform': transf_int,
                         'rename': 'seasonNr'},
        'episodeNumber': {'type': sqlalchemy.Integer, 'transform': transf_int,
                          'rename': 'episodeNr'}
    },
    'title_principals': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'principalCast': {'transform': transf_multi_imdbid, 'rename': 'cast'}
    },
    'title_ratings': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'averageRating': {'type': sqlalchemy.Float, 'transform': transf_float,
                          'rename': 'rating', 'index': True},
        'numVotes': {'type': sqlalchemy.Integer, 'transform': transf_int,
                     'rename': 'votes', 'index': True}
    }
}


_translate = dict(B='1', C='2', D='3', F='1', G='2', J='2', K='2', L='4',
                    M='5', N='5', P='1', Q='2', R='6', S='2', T='3', V='1',
                    X='2', Z='2')
_translateget = _translate.get
_re_non_ascii = re.compile(r'^[^a-z]*', re.I)


def soundex(s, length=5):
    """Return the soundex code for the given string."""
    s = _re_non_ascii.sub('', s)
    if not s:
        return None
    s = s.upper()
    soundCode = s[0]
    count = 1
    for c in s[1:]:
        if count >= length:
            break
        cw = _translateget(c, '0')
        if cw != '0' and soundCode[-1] != cw:
            soundCode += cw
            count += 1
    return soundCode or None


def title_soundex(title):
    """Return the soundex code for the given title; the (optional) starting
    article is pruned."""
    if not title:
        return None
    title = canonicalTitle(title)
    ts = title.split(', ')
    if ts[-1].lower() in _unicodeArticles:
        title = ', '.join(ts[:-1])
    return soundex(title)


def name_soundexes(name):
    """Return three soundex codes for the given name; the name is assumed
    to be in the 'Name Surname' format.
    The first one is the soundex of the name in the normal format.
    The second is the soundex of the name in the canonical format, if different
    from the first one.
    The third is the soundex of the surname alone, if different from the
    other two values."""
    if not name:
        return None, None, None
    s1 = soundex(name)
    canonical_name = canonicalName(name)
    s2 = soundex(canonical_name)
    if s1 == s2:
        s2 = None
    s3 = soundex(canonical_name.split(', ')[0])
    if s3 and s3 in (s1, s2):
        s3 = None
    return s1, s2, s3


def titleVariations(title):
    """Build title variations useful for searches."""
    title2 = canonicalTitle(title)
    t2s = title2.split(', ')
    if t2s[-1].lower() in _unicodeArticles:
        title2 = ', '.join(t2s[:-1])
    logging.debug('title variations: 1:[%s] 2:[%s]',
                  title, title2)
    return title, title2


def nameVariations(name, fromPtdf=False):
    """Build name variations useful for searches."""
    # name1 is the name in the canonical format.
    name2 = cnonicalName(name)
    if name1 == name2:
        name2 = ''
    logging.debug('name variations: 1:[%s] 2:[%s]',
                      name, name2)
    return name, name2


def ratcliff(s1, s2, sm):
    """Ratcliff-Obershelp similarity."""
    STRING_MAXLENDIFFER = 0.7
    s1len = len(s1)
    s2len = len(s2)
    if s1len < s2len:
        threshold = float(s1len) / s2len
    else:
        threshold = float(s2len) / s1len
    if threshold < STRING_MAXLENDIFFER:
        return 0.0
    sm.set_seq2(s2.lower())
    return sm.ratio()


def scan_names(name_list, name1, name2, results=0, ro_thresold=None):
    """Scan a list of names, searching for best matches against
    the given variations."""
    if ro_thresold is not None:
        RO_THRESHOLD = ro_thresold
    else:
        RO_THRESHOLD = 0.6
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm1.set_seq1(name1.lower())
    if name2:
        sm2.set_seq1(name2.lower())
    resd = {}
    for i, n_data in name_list:
        nil = n_data['name']
        # Distance with the canonical name.
        ratios = [ratcliff(name1, nil, sm1) + 0.05]
        namesurname = ''
        if not _scan_character:
            nils = nil.split(', ', 1)
            surname = nils[0]
            if len(nils) == 2:
                namesurname = '%s %s' % (nils[1], surname)
        else:
            nils = nil.split(' ', 1)
            surname = nils[-1]
            namesurname = nil
        if surname != nil:
            # Distance with the "Surname" in the database.
            ratios.append(ratcliff(name1, surname, sm1))
            if not _scan_character:
                ratios.append(ratcliff(name1, namesurname, sm1))
            if name2:
                ratios.append(ratcliff(name2, surname, sm2))
                # Distance with the "Name Surname" in the database.
                if namesurname:
                    ratios.append(ratcliff(name2, namesurname, sm2))
        if name3:
            # Distance with the long imdb canonical name.
            ratios.append(ratcliff(name3,
                                   build_name(n_data, canonical=1), sm3) + 0.1)
        ratio = max(ratios)
        if ratio >= RO_THRESHOLD:
            if i in resd:
                if ratio > resd[i][0]:
                    resd[i] = (ratio, (i, n_data))
            else:
                resd[i] = (ratio, (i, n_data))
    res = list(resd.values())
    res.sort()
    res.reverse()
    if results > 0:
        res[:] = res[:results]
    return res


def scan_titles(titles_list, title1, title2, results=0,
                searchingEpisode=0, onlyEpisodes=0, ro_thresold=None):
    """Scan a list of titles, searching for best matches against
    the given variations."""
    if ro_thresold is not None:
        RO_THRESHOLD = ro_thresold
    else:
        RO_THRESHOLD = 0.6
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm3 = SequenceMatcher()
    sm1.set_seq1(title1.lower())
    sm2.set_seq2(title2.lower())
    if title3:
        sm3.set_seq1(title3.lower())
        if title3[-1] == '}':
            searchingEpisode = 1
    hasArt = 0
    if title2 != title1:
        hasArt = 1
    resd = {}
    for i, t_data in titles_list:
        if onlyEpisodes:
            if t_data.get('kind') != 'episode':
                continue
            til = t_data['title']
            if til[-1] == ')':
                dateIdx = til.rfind('(')
                if dateIdx != -1:
                    til = til[:dateIdx].rstrip()
            if not til:
                continue
            ratio = ratcliff(title1, til, sm1)
            if ratio >= RO_THRESHOLD:
                resd[i] = (ratio, (i, t_data))
            continue
        if searchingEpisode:
            if t_data.get('kind') != 'episode':
                continue
        elif t_data.get('kind') == 'episode':
            continue
        til = t_data['title']
        # Distance with the canonical title (with or without article).
        #   titleS      -> titleR
        #   titleS, the -> titleR, the
        if not searchingEpisode:
            til = canonicalTitle(til)
            ratios = [ratcliff(title1, til, sm1) + 0.05]
            # til2 is til without the article, if present.
            til2 = til
            tils = til2.split(', ')
            matchHasArt = 0
            if tils[-1].lower() in _unicodeArticles:
                til2 = ', '.join(tils[:-1])
                matchHasArt = 1
            if hasArt and not matchHasArt:
                #   titleS[, the]  -> titleR
                ratios.append(ratcliff(title2, til, sm2))
            elif matchHasArt and not hasArt:
                #   titleS  -> titleR[, the]
                ratios.append(ratcliff(title1, til2, sm1))
        else:
            ratios = [0.0]
        if title3:
            # Distance with the long imdb canonical title.
            ratios.append(ratcliff(title3,
                                   build_title(t_data, canonical=1, ptdf=1), sm3) + 0.1)
        ratio = max(ratios)
        if ratio >= RO_THRESHOLD:
            if i in resd:
                if ratio > resd[i][0]:
                    resd[i] = (ratio, (i, t_data))
            else:
                resd[i] = (ratio, (i, t_data))
    res = list(resd.values())
    res.sort()
    res.reverse()
    if results > 0:
        res[:] = res[:results]
    return res


