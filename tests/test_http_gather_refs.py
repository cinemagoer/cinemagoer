from pytest import fixture

from imdb.parser.http.utils import GatherRefs


@fixture(scope='module')
def person_bio(url_opener, people):
    """A function to retrieve the main details page of a test person."""
    def retrieve(person_key):
        url = people[person_key] + '/bio'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = GatherRefs()


def test_movies_and_persons_refs_should_be_lists(person_bio):
    page = person_bio('julia roberts')
    data = parser.parse(page)
    assert len(data['names refs']) > 100
    assert len(data['titles refs']) > 70
