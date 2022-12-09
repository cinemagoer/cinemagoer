from pytest import fixture

import gettext
import os

import imdb.locale  # noqa: F401

gettext.textdomain("imdbpy")

_ = gettext.gettext


@fixture
def italian():
    """Set the language to Italian temporarily."""
    lang = os.environ["LANG"]
    os.environ["LANG"] = "it_IT.UTF-8"
    yield
    os.environ["LANG"] = lang


def test_locale_should_work(italian):
    assert _("art-director") == "Direttore artistico"
