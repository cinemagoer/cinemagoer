
import re
import logging
import sqlalchemy
from difflib import SequenceMatcher
from imdb.utils import canonicalName, canonicalTitle, _unicodeArticles


RO_THRESHOLD = 0.6
STRING_MAXLENDIFFER = 0.7
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


KIND = {
    'tvEpisode': 'episode',
    'tvMiniSeries': 'tv mini series',
    'tvSeries': 'tv series',
    'tvShort': 'tv short',
    'tvSpecial': 'tv special',
    'videoGame': 'video game'
}

def transf_kind(x):
    return KIND.get(x, x)


DB_TRANSFORM = {
    'title_basics': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'titleType': {'transform': transf_kind, 'rename': 'kind'},
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
    """Return the soundex code for the given title; the (optional) starting article is pruned."""
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


def nameVariations(name):
    """Build name variations useful for searches."""
    canonical_name = canonicalName(name)
    logging.debug('name variations: 1:[%s] 2:[%s]',
                      name, canonical_name)
    return name, canonical_name


def ratcliff(s1, s2, sm):
    """Ratcliff-Obershelp similarity."""
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


def scan_names(name_list, name, results=0, ro_threshold=RO_THRESHOLD):
    """Scan a list of names, searching for best matches against
    the given variations."""
    canonical_name = canonicalName(name).replace(',', '')
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm1.set_seq1(name.lower())
    sm2.set_seq1(canonical_name.lower())
    resd = {}
    for i, n_data in name_list:
        nil = n_data['name']
        # Distance with the canonical name.
        ratios = [ratcliff(name, nil, sm1) + 0.1,
                  ratcliff(name, canonicalName(nil).replace(',', ''), sm2)]
        ratio = max(ratios)
        if ratio >= ro_threshold:
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


def strip_article(title):
    no_article_title = canonicalTitle(title)
    t2s = no_article_title.split(', ')
    if t2s[-1].lower() in _unicodeArticles:
        no_article_title = ', '.join(t2s[:-1])
    return no_article_title


def scan_titles(titles_list, title, results=0, ro_threshold=RO_THRESHOLD):
    """Scan a list of titles, searching for best matches against
    the given variations."""
    no_article_title = strip_article(title)
    sm1 = SequenceMatcher()
    sm1.set_seq1(title.lower())
    sm2 = SequenceMatcher()
    sm2.set_seq2(no_article_title.lower())
    resd = {}
    for i, t_data in titles_list:
        til = t_data['title']
        ratios = [ratcliff(title, til, sm1) + 0.1,
                  ratcliff(no_article_title, strip_article(til), sm2)]
        ratio = max(ratios)
        if t_data.get('kind') == 'episode':
            ratio -= .2
        if ratio >= ro_threshold:
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

