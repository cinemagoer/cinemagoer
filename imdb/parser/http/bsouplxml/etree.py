"""
parser.http.bsouplxml.etree module (imdb.parser.http package).

This module adapts the beautifulsoup interface to lxml.etree module.

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
from _bsoup import Tag as Element

import bsoupxpath


def fromstring(xml_string):
    """Return a DOM representation of the string."""
    return BeautifulSoup.BeautifulStoneSoup(xml_string,
        convertEntities=BeautifulSoup.BeautifulStoneSoup.XML_ENTITIES
        ).findChild(True)

def tostring(element, encoding=None, pretty_print=False):
    """Return a unicode representation of an element."""
    if isinstance(element, unicode):
        return element
    if isinstance(element, BeautifulSoup.NavigableString):
        return unicode(element)
    if isinstance(element, BeautifulSoup.Tag):
        return element.__str__(None, pretty_print)

def setattribute(tag, name, value):
    tag[name] = value

def xpath(node, expr):
    """Apply an xpath expression to a node. Return a list of nodes."""
    #path = bsoupxpath.Path(expr)
    path = bsoupxpath.get_path(expr)
    return path.apply(node)


# XXX: monkey patching the beautifulsoup tag class
BeautifulSoup.Tag.attrib = property(fget=lambda self: self)
BeautifulSoup.Tag.text = property(fget=lambda self: self.string)
BeautifulSoup.Tag.set = setattribute
BeautifulSoup.Tag.getparent = lambda self: self.parent
BeautifulSoup.Tag.drop_tree = BeautifulSoup.Tag.extract
BeautifulSoup.Tag.xpath = xpath

# TODO: setting the text attribute for tags
