def test_movie_tech_sections(ia):
    movie = ia.get_movie('0133093', info=['technical'])
    tech = movie.get('tech', [])
    assert set(tech.keys()) == set(['sound mix', 'color', 'aspect ratio', 'camera',
                                    'laboratory', 'cinematographic process', 'printed film format',
                                    'negative format', 'runtime', 'film length'])

