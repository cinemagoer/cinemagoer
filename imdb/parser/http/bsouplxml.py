"""
parser.http.bsouplxml module (imdb.parser.http package).

This module adapts the beautifulsoup interface to lxml.

Copyright 2008 H. Turgut Uyar <uyar@tekir.org>
          2008 Davide Alberani <da@erlug.linux.it>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import _bsoup as BeautifulSoup
import bsoupxpath


class ETree(BeautifulSoup.BeautifulSoup):
    """Adapter for a soup."""

    def __init__(self, html_string):
        BeautifulSoup.BeautifulSoup.__init__(self, html_string,
            convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)
        self.root = self.findChild(True)
        self.root.soup = self


def fromstring(html_string):
    """Return a DOM representation of the string."""
    return ETree(html_string).root

def tostring(element, encoding=None):
    """Return a unicode representation of an element."""
    return unicode(element)


def get_attribute(tag, attr):
    if attr == 'attrib':
        return tag
    return BeautifulSoup.Tag.__getattr_backup__(tag, attr)

def setattribute(tag, name, value):
    tag[name] = value

def getparent(node):
    """Return the parent of the given node."""
    return node.parent

def drop_tree(node):
    """Remove a node and all its children."""
    # XXX: catch the raised exception, if the node is already gone?
    #      i.e.: removing <p> contained in an already removed <p>.
    node.extract()

def xpath(node, expr):
    """Apply an xpath expression to a node. Return a list of nodes."""
    #path = bsoupxpath.Path(expr)
    path = bsoupxpath.get_path(expr)
    return path.apply(node)


# XXX: monkey patching the beautifulsoup tag class
BeautifulSoup.Tag.__getattr_backup__ = BeautifulSoup.Tag.__getattr__
BeautifulSoup.Tag.__getattr__ = get_attribute

BeautifulSoup.Tag.set = setattribute
BeautifulSoup.Tag.getparent = getparent
BeautifulSoup.Tag.drop_tree = drop_tree
BeautifulSoup.Tag.xpath = xpath
