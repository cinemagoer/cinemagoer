from pytest import fixture

import re

from imdb.parser.http.movieParser import DOMHTMLPlotParser


@fixture(scope='module')
def movie_plot_summaries(url_opener, movies):
    """A function to retrieve the plot summary page of a test movie."""
    def retrieve(movie_key):
        url = movies[movie_key] + '/plotsummary'
        return url_opener.retrieve_unicode(url)
    return retrieve


parser = DOMHTMLPlotParser()


def test_summary_should_end_with_author(movie_plot_summaries):
    page = movie_plot_summaries('matrix')
    data = parser.parse(page)['data']
    assert re.match('^Thomas A\. Anderson is a man .*::redcommander27$', data['plot'][0])


def test_summary_should_have_synopsis(movie_plot_summaries):
    page = movie_plot_summaries('matrix')
    data = parser.parse(page)['data']
    assert len(data['synopsis']) >= 1 and data['synopsis'][0]


def test_summary_none_should_be_excluded(movie_plot_summaries):
    page = movie_plot_summaries('ates parcasi')
    data = parser.parse(page)['data']
    assert 'plot' not in data
