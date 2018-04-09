import re


def test_summary_should_end_with_author(ia):
    data = ia.get_movie('0133093', info=['plot'])   # Matrix
    assert re.match('^Thomas A\. Anderson is a man .*::redcommander27$', data['plot'][0])


def test_summary_should_have_synopsis(ia):
    data = ia.get_movie('0133093', info=['plot'])   # Matrix
    assert len(data['synopsis']) >= 1 and data['synopsis'][0]


def test_summary_none_should_be_excluded(ia):
    data = ia.get_movie('1863157', info=['plot'])   # Ates Parcasi
    assert 'plot' not in data
