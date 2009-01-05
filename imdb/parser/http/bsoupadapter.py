"""
parser.http.bsoupadapter module (imdb.parser.http package).

This module adapts the beautifulsoup xpath support to the internal mechanism.

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


def fromstring(html_string):
    """Return a DOM representation of the string.
    """
    return BeautifulSoup.BeautifulSoup(html_string,
        convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)


def tostring(element):
    """Return a unicode representation of an element.
    """
    try:
        return unicode(element)
    except AttributeError:
        return str(element)


def appendchild(parent, tagname, attrs=None, text=None, dom=None):
    """Append a child element to an existing element."""
    if dom is None:
        raise ValueError("A soup instance must be supplied")
    child = BeautifulSoup.Tag(dom, tagname)
    if attrs is not None:
        for key in attrs:
            setattribute(child, key, attrs[key])
    if text is not None:
        textnode = BeautifulSoup.NavigableString(text)
        child.append(textnode)
    parent.append(child)
    return child


def getattribute(node, attrName):
    """Return an attribute value or None."""
    return node.get(attrName)


def setattribute(node, attrName, attrValue):
    """Set an attribute to a given value."""
    if attrValue is None:
        del node[attrName]
    else:
        node[attrName] = attrValue


def getparent(node):
    """Return the parent of the given node."""
    return node.parent


def droptree(node):
    """Remove a node and all its children."""
    # XXX: catch the raised exception, if the node is already gone?
    #      i.e.: removing <p> contained in an already removed <p>.
    node.extract()


def clone(node):
    """Return a clone of the given node."""
    # XXX: test with deepcopy?  Check if there are problems with
    #      python 2.4 and previous.
    return fromstring(tostring(node)).findChild(True)


def apply_xpath(node, path):
    """Apply an xpath expression to a node. Return a list of nodes.
    """
    #xpath = bsoupxpath.Path(path)
    xpath = bsoupxpath.get_path(path)
    return xpath.apply(node)
