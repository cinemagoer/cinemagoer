import xml.etree.ElementTree as ET

def test_movie_xml(ia):
    movie = ia.get_movie('0133093')    # Matrix
    movie_xml = movie.asXML()
    movie_xml = movie_xml.encode('utf8', 'ignore')
    assert ET.fromstring(movie_xml) is not None
