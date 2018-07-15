import xml.etree.ElementTree as ET

def test_movie_xml(ia):
    movie = ia.get_movie('0133093')    # Matrix
    assert ET.fromstring(movie.asXML())
