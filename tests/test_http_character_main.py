from pytest import fixture, mark

from imdb.parser.http.characterParser import DOMHTMLCharacterMaindetailsParser


@fixture(scope='module')
def character_main_details(url_opener, characters):
    """A function to retrieve the main details page of a test character."""
    def retrieve(character_key):
        url = characters[character_key]
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLCharacterMaindetailsParser()


@mark.skip(reason='character pages are title specific now')
def test_name_should_be_as_is(character_main_details):
    page = character_main_details('jesse james')
    data = parser.parse(page)['data']
    assert data['name'] == 'Jesse James'
