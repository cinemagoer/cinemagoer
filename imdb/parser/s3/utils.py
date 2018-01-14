
import re
import sqlalchemy


re_imdbids = re.compile(r'(nm|tt)')


def transf_imdbid(x):
    return int(x[2:])


def transf_multi_imdbid(x):
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
        return bool(x)
    except:
        return None


DB_TRANSFORM = {
    'title_basics': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID'},
        'isAdult': {'type': sqlalchemy.Boolean, 'transform': transf_bool},
        'startYear': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'endYear': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'runtimeMinutes': {'type': sqlalchemy.Integer, 'transform': transf_int,
                           'rename': 'runtime'}
    },
    'name_basics': {
        'nconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'personID'},
        'birthYear': {'type': sqlalchemy.Integer, 'transform': transf_int,
                      'rename': 'birth date'},
        'deathYear': {'type': sqlalchemy.Integer, 'transform': transf_int,
                      'rename': 'death date'}
    },
    'title_crew': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID'},
        'directors': {'transform': transf_multi_imdbid, 'rename': 'director'},
        'writers': {'transform': transf_multi_imdbid, 'rename': 'writer'}
    },
    'title_episode': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID'},
        'parentTconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid},
        'seasonNumber': {'type': sqlalchemy.Integer, 'transform': transf_int,
                         'rename': 'seasonNr'},
        'episodeNumber': {'type': sqlalchemy.Integer, 'transform': transf_int,
                          'rename': 'episodeNr'}
    },
    'title_principals': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID'},
        'principalCast': {'transform': transf_multi_imdbid}
    },
    'title_ratings': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID'},
        'averageRating': {'type': sqlalchemy.Float, 'transform': transf_float,
                          'rename': 'rating'},
        'numVotes': {'type': sqlalchemy.Integer, 'transform': transf_int,
                     'rename': 'votes'}
    },

}
