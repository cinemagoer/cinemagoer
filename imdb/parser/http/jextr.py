"""Extracts information from a JSON object."""


def movie_data(obj):
    """
    Extracts movie data from a JSON object.

    This data is usually (?) found in the __NEXT_DATA__ JSON object,
    in a "nodes" object.
    """
    data = {}
    if not isinstance(obj, dict):
        return data
    id_ = obj.get('id', '').replace('tt', '')
    if not id_:
        return {}
    data['id'] = id_
    if 'titleText' in obj:
        data['title'] = obj['titleText']['text']
    else:
        return {}
    if 'originalTitleText' in obj:
        data['original title'] = obj['originalTitleText']['text']
    data['kind'] = obj['titleType']['id']
    if 'releaseYear' in obj:
        ry = obj['releaseYear']
        if ry.get('year'):
            data['year'] = ry['year']
            if 'endYear' in ry and ry['endYear']:
                data['year'] = f"{data['year']}-{ry['endYear']}"
    if 'ratingsSummary' in obj:
        rs = obj['ratingsSummary']
        if 'aggregateRating' in rs and rs['aggregateRating']:
            data['rating'] = rs['aggregateRating']
            data['votes'] = rs['voteCount']
    if 'runtime' in obj and obj['runtime']:
        rt = obj['runtime']
        if 'seconds' in rt:
            data['runtimes'] = [rt['seconds'] / 60]
    if 'certificate' in obj and obj['certificate']:
        cert = obj['certificate']
        if 'rating' in cert:
            data['certificates'] = [cert['rating']]
    if 'titleGenres' in obj and obj['titleGenres']:
        tg = obj['titleGenres']
        for genre in tg.get('genres', []):
            if 'text' in genre:
                data.setdefault('genres', []).append(genre['text'])
    if 'plot' in obj and obj.get('plot', {}).get('plotText').get('plainText'):
        data['plot'] = obj['plot']['plotText']['plainText']
    return data
